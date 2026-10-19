"""抖音监控编排服务：配置读写、定时判断、批量采集与快照落库。"""
import logging
import threading
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from backend.app import db
from backend.app.models.douyin_monitor import (
    DouyinMonitorConfig,
    DouyinMonitorRun,
    DouyinMonitorRunTarget,
    DouyinVideoLatest,
    DouyinVideoSnapshot,
)
from backend.app.models.douyin_video import DouyinVideo
from backend.app.services.douyin_fetcher import DouyinFetcher

logger = logging.getLogger('douyin.monitor')

TIMEZONE = ZoneInfo('Asia/Shanghai')
LOCK_NAME = 'douyin_monitor'
# 新建 run 到线程拿到命名锁之间的宽限期，超过后未持锁的 running 记录视为僵尸
STALE_GRACE_SECONDS = 60
# 快照保留天数，超出部分在每轮采集结束时清理
SNAPSHOT_RETENTION_DAYS = 90

DEFAULT_CONFIG = {
    'enabled': False,
    'schedule_type': 'interval',
    'interval_minutes': 30,
    'cron_expression': '0 */2 * * *',
    'concurrency': 3,
    'retry_times': 2,
    'retry_delay_seconds': 5,
    'fetch_on_import': True,
    'stale_minutes': 15,
}


# ==================== 配置 ====================

def get_config() -> DouyinMonitorConfig:
    cfg = db.session.get(DouyinMonitorConfig, 1)
    if cfg is None:
        cfg = DouyinMonitorConfig(id=1, **DEFAULT_CONFIG)
        db.session.add(cfg)
        db.session.commit()
    if cfg.next_run_at is None:
        cfg.next_run_at = _next_run_naive(cfg)
        db.session.commit()
    return cfg


def config_to_dict(cfg: DouyinMonitorConfig) -> dict:
    return {
        'enabled': bool(cfg.enabled),
        'schedule_type': cfg.schedule_type,
        'interval_minutes': cfg.interval_minutes,
        'cron_expression': cfg.cron_expression,
        'concurrency': cfg.concurrency,
        'retry_times': cfg.retry_times,
        'retry_delay_seconds': cfg.retry_delay_seconds,
        'fetch_on_import': bool(cfg.fetch_on_import),
        'stale_minutes': cfg.stale_minutes,
        'next_run_at': iso_utc(cfg.next_run_at),
        'updated_at': iso_utc(cfg.updated_at),
        'updated_by': cfg.updated_by,
    }


def _parse_int(data, key, low, high, errors):
    raw = data.get(key, DEFAULT_CONFIG[key])
    try:
        value = int(raw)
    except (TypeError, ValueError):
        errors[key] = '必须是整数'
        return DEFAULT_CONFIG[key]
    if not low <= value <= high:
        errors[key] = f'必须在 {low} ~ {high} 之间'
        return DEFAULT_CONFIG[key]
    return value


def save_config(data: dict, username: str):
    """校验并保存配置。返回 (cfg, errors)。"""
    errors = {}

    schedule_type = data.get('schedule_type', 'interval')
    if schedule_type not in ('interval', 'cron'):
        errors['schedule_type'] = '只支持 interval 或 cron'
        schedule_type = 'interval'

    cron_expression = str(data.get('cron_expression') or '').strip() or DEFAULT_CONFIG['cron_expression']
    if schedule_type == 'cron':
        try:
            CronTrigger.from_crontab(cron_expression, timezone=TIMEZONE)
        except Exception:
            errors['cron_expression'] = 'Cron 表达式不合法'

    interval_minutes = _parse_int(data, 'interval_minutes', 5, 1440, errors)
    concurrency = _parse_int(data, 'concurrency', 1, 5, errors)
    retry_times = _parse_int(data, 'retry_times', 0, 5, errors)
    retry_delay_seconds = _parse_int(data, 'retry_delay_seconds', 1, 60, errors)
    stale_minutes = _parse_int(data, 'stale_minutes', 1, 1440, errors)

    if errors:
        return None, errors

    cfg = get_config()
    cfg.enabled = bool(data.get('enabled', False))
    cfg.schedule_type = schedule_type
    cfg.interval_minutes = interval_minutes
    cfg.cron_expression = cron_expression
    cfg.concurrency = concurrency
    cfg.retry_times = retry_times
    cfg.retry_delay_seconds = retry_delay_seconds
    cfg.fetch_on_import = bool(data.get('fetch_on_import', True))
    cfg.stale_minutes = stale_minutes
    cfg.updated_by = username
    cfg.next_run_at = _next_run_naive(cfg, base=datetime.now(timezone.utc))
    db.session.commit()
    return cfg, {}


# ==================== 调度判断 ====================

def _last_finished_run():
    return (
        DouyinMonitorRun.query
        .filter(DouyinMonitorRun.status.in_(['success', 'partial', 'failed']))
        .order_by(DouyinMonitorRun.started_at.desc())
        .first()
    )


def _next_run_naive(cfg: DouyinMonitorConfig, base=None) -> datetime:
    """计算下一次执行时间，返回 naive UTC。"""
    if base is None:
        last = _last_finished_run()
        if last and last.started_at:
            base = last.started_at.replace(tzinfo=timezone.utc)
        else:
            base = datetime.now(timezone.utc)

    if cfg.schedule_type == 'cron':
        trigger = CronTrigger.from_crontab(cfg.cron_expression, timezone=TIMEZONE)
        next_fire = trigger.get_next_fire_time(None, base)
    else:
        next_fire = base + timedelta(minutes=cfg.interval_minutes)

    return next_fire.astimezone(timezone.utc).replace(tzinfo=None)


def is_due(cfg: DouyinMonitorConfig) -> bool:
    if not cfg.enabled:
        return False
    if cfg.next_run_at is None:
        return True
    return datetime.utcnow() >= cfg.next_run_at


# ==================== 运行 ====================

def create_run(trigger_type: str, total: int = 0) -> DouyinMonitorRun:
    run = DouyinMonitorRun(trigger_type=trigger_type, status='running', total=total)
    db.session.add(run)
    db.session.commit()
    return run


def _lock_held() -> bool:
    """判断 MySQL 命名锁是否仍被某个采集线程持有。"""
    try:
        return db.session.execute(
            text('SELECT IS_USED_LOCK(:name)'), {'name': LOCK_NAME}
        ).scalar() is not None
    except Exception:  # noqa: BLE001
        return False


def reclaim_stale_runs() -> int:
    """回收进程重启后遗留的 running 记录：未持锁且超过宽限期即视为已中断。"""
    cutoff = datetime.utcnow() - timedelta(seconds=STALE_GRACE_SECONDS)
    candidates = DouyinMonitorRun.query.filter(
        DouyinMonitorRun.status == 'running',
        DouyinMonitorRun.started_at < cutoff,
    ).all()
    if not candidates or _lock_held():
        return 0

    now = datetime.utcnow()
    for run in candidates:
        run.status = 'failed'
        run.finished_at = now
        run.message = '采集超时（进程可能已重启）'
    db.session.commit()
    return len(candidates)


def start_run(app, trigger_type: str = 'manual', video_ids=None):
    """启动后台采集线程。返回 (run, running_run)；已有任务时 run 为 None。"""
    reclaim_stale_runs()
    running = DouyinMonitorRun.query.filter_by(status='running').first()
    if running is not None:
        return None, running

    total = len(video_ids) if video_ids else DouyinVideo.query.count()
    run = create_run(trigger_type, total)
    thread = threading.Thread(
        target=run_cycle,
        args=(app, run.id, video_ids),
        daemon=True,
        name=f'douyin-monitor-{run.id}',
    )
    thread.start()
    return run, None


def run_cycle(app, run_id: int, video_ids=None):
    """执行一轮采集（同步）。使用 MySQL 命名锁避免多进程重复执行。"""
    with app.app_context():
        conn = db.engine.connect()
        locked = False
        try:
            locked = conn.execute(
                text('SELECT GET_LOCK(:name, 0)'), {'name': LOCK_NAME}
            ).scalar() == 1
            if not locked:
                logger.warning('run=%s 未获取到采集锁，跳过本轮', run_id)
                _finish_run(run_id, 'failed', 0, 0, '已有采集任务在运行')
                return
            _execute(run_id, video_ids)
        except Exception as exc:  # noqa: BLE001
            logger.exception('run=%s 采集异常', run_id)
            db.session.rollback()
            _finish_run(run_id, 'failed', 0, 0, str(exc)[:255])
        finally:
            if locked:
                try:
                    conn.execute(text('SELECT RELEASE_LOCK(:name)'), {'name': LOCK_NAME})
                except Exception:  # noqa: BLE001
                    pass
            conn.close()
            db.session.remove()


def _execute(run_id: int, video_ids=None):
    run = db.session.get(DouyinMonitorRun, run_id)
    if run is None:
        return

    cfg = get_config()

    if video_ids:
        videos = DouyinVideo.query.filter(DouyinVideo.id.in_(video_ids)).order_by(DouyinVideo.id).all()
    else:
        videos = DouyinVideo.query.order_by(DouyinVideo.id).all()

    run.total = len(videos)
    DouyinMonitorRunTarget.query.filter_by(run_id=run_id).delete(synchronize_session=False)
    db.session.add_all([
        DouyinMonitorRunTarget(run_id=run_id, video_id=video.id) for video in videos
    ])
    db.session.commit()

    if not videos:
        _finish_run(run_id, 'success', 0, 0, '没有需要采集的视频')
        return

    ids = [video.id for video in videos]
    latest_map = {
        row.video_id: row
        for row in DouyinVideoLatest.query.filter(DouyinVideoLatest.video_id.in_(ids)).all()
    }

    # 已解析过 aweme_id 的视频直接复用，避免每轮重复解析短链
    inputs = []
    for video in videos:
        latest = latest_map.get(video.id)
        inputs.append(latest.aweme_id if latest and latest.aweme_id else video.url)

    # 关闭上面的读事务：采集可能长时间阻塞，不能让 MDL 一直挂在这里挡住 DDL
    db.session.commit()

    success = 0
    failed = 0

    def save_result(index: int, result: dict):
        """每抓完一条就写库，让前端进度实时变化。"""
        nonlocal success, failed
        video = videos[index]
        latest = latest_map.get(video.id)
        if latest is None:
            latest = DouyinVideoLatest(video_id=video.id)
            db.session.add(latest)
            latest_map[video.id] = latest

        now = datetime.utcnow()
        if result.get('error'):
            failed += 1
            message = str(result['error'])[:255]
            latest.last_error = message
            db.session.add(DouyinVideoSnapshot(
                video_id=video.id,
                aweme_id=latest.aweme_id,
                captured_at=now,
                error=message,
            ))
        else:
            success += 1
            stats = result.get('statistics') or {}
            latest.aweme_id = result.get('aweme_id') or latest.aweme_id
            latest.digg_count = stats.get('digg_count', 0)
            latest.comment_count = stats.get('comment_count', 0)
            latest.share_count = stats.get('share_count', 0)
            latest.collect_count = stats.get('collect_count', 0)
            latest.play_count = stats.get('play_count', 0)
            latest.captured_at = now
            latest.last_error = None

            db.session.add(DouyinVideoSnapshot(
                video_id=video.id,
                aweme_id=latest.aweme_id,
                digg_count=latest.digg_count,
                comment_count=latest.comment_count,
                share_count=latest.share_count,
                collect_count=latest.collect_count,
                play_count=latest.play_count,
                captured_at=now,
            ))

            if not video.author and result.get('author'):
                video.author = result['author'][:120]
            if not video.title and result.get('desc'):
                video.title = result['desc'][:255]

        run.success_count = success
        run.failed_count = failed
        db.session.commit()

    fetcher = DouyinFetcher(
        concurrency=cfg.concurrency,
        retry_times=cfg.retry_times,
        retry_delay_seconds=cfg.retry_delay_seconds,
    )
    logger.info('run=%s 开始采集，共 %s 条，并发=%s', run_id, len(videos), cfg.concurrency)
    fetcher.fetch_video_details(inputs, concurrency=cfg.concurrency, on_result=save_result)

    status = 'success'
    if failed and not success:
        status = 'failed'
    elif failed:
        status = 'partial'

    logger.info('run=%s 采集结束，成功 %s 条，失败 %s 条', run_id, success, failed)
    _finish_run(run_id, status, success, failed, f'成功 {success} 条，失败 {failed} 条')


def _finish_run(run_id: int, status: str, success: int, failed: int, message: str):
    run = db.session.get(DouyinMonitorRun, run_id)
    if run is not None:
        run.status = status
        run.success_count = success
        run.failed_count = failed
        run.finished_at = datetime.utcnow()
        run.message = message

    cfg = get_config()
    cfg.next_run_at = _next_run_naive(cfg, base=datetime.now(timezone.utc))
    db.session.commit()

    try:
        purge_old_snapshots()
    except Exception:  # noqa: BLE001
        db.session.rollback()


def purge_old_snapshots(days: int = SNAPSHOT_RETENTION_DAYS) -> int:
    """删除超过保留期的快照，控制表体积。返回删除条数。"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    deleted = DouyinVideoSnapshot.query.filter(
        DouyinVideoSnapshot.captured_at < cutoff
    ).delete(synchronize_session=False)
    if deleted:
        db.session.commit()
    return deleted


def failed_video_ids() -> list:
    """返回最近一次采集失败的视频 ID 列表。"""
    return [
        row.video_id
        for row in DouyinVideoLatest.query.filter(
            DouyinVideoLatest.last_error.isnot(None)
        ).order_by(DouyinVideoLatest.video_id).all()
    ]



# ==================== 序列化 ====================

def iso_utc(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat()


def latest_to_dict(latest: DouyinVideoLatest):
    if latest is None:
        return None
    return {
        'aweme_id': latest.aweme_id,
        'digg_count': latest.digg_count or 0,
        'comment_count': latest.comment_count or 0,
        'share_count': latest.share_count or 0,
        'collect_count': latest.collect_count or 0,
        'play_count': latest.play_count or 0,
        'captured_at': iso_utc(latest.captured_at),
        'last_error': latest.last_error,
    }


def snapshot_to_dict(snapshot: DouyinVideoSnapshot):
    return {
        'id': snapshot.id,
        'aweme_id': snapshot.aweme_id,
        'digg_count': snapshot.digg_count,
        'comment_count': snapshot.comment_count,
        'share_count': snapshot.share_count,
        'collect_count': snapshot.collect_count,
        'play_count': snapshot.play_count,
        'captured_at': iso_utc(snapshot.captured_at),
        'error': snapshot.error,
    }


def run_to_dict(run: DouyinMonitorRun):
    if run is None:
        return None
    return {
        'id': run.id,
        'trigger_type': run.trigger_type,
        'status': run.status,
        'total': run.total,
        'success_count': run.success_count,
        'failed_count': run.failed_count,
        'started_at': iso_utc(run.started_at),
        'finished_at': iso_utc(run.finished_at),
        'message': run.message,
        'video_ids': [
            row.video_id
            for row in DouyinMonitorRunTarget.query
            .filter_by(run_id=run.id)
            .order_by(DouyinMonitorRunTarget.video_id)
            .all()
        ],
    }


def get_status() -> dict:
    cfg = get_config()
    reclaim_stale_runs()
    running = (
        DouyinMonitorRun.query.filter_by(status='running')
        .order_by(DouyinMonitorRun.started_at.desc())
        .first()
    )
    last = _last_finished_run()

    return {
        'enabled': bool(cfg.enabled),
        'running': running is not None,
        'current_run': run_to_dict(running),
        'last_run': run_to_dict(last),
        'next_run_at': iso_utc(cfg.next_run_at),
        'total_videos': DouyinVideo.query.count(),
    }
