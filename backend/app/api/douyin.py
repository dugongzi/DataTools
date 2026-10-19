import csv
import io
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import Response, current_app, jsonify, request

from backend.app import db
from backend.app.api import api_bp
from backend.app.api.auth import require_auth
from backend.app.models.douyin_monitor import DouyinVideoLatest, DouyinVideoSnapshot
from backend.app.models.douyin_video import DouyinVideo
from backend.app.schemas.douyin_video import douyin_videos_schema
from backend.app.services import douyin_monitor as monitor
from backend.app.services import douyin_stats as stats

URL_RE = re.compile(r'https?://[^\s，。、；！？（）()\[\]【】<>"\'|]+', re.IGNORECASE)
HOST_RE = re.compile(r'(^|\.)douyin\.com(?::\d+)?(?:/|$)', re.IGNORECASE)
AUTHOR_RE = re.compile(r'【\s*(.+?)\s*的[^】]{0,12}作品\s*】')
TIMEZONE = ZoneInfo('Asia/Shanghai')


def extract_douyin_links(text):
    """Parse pasted Douyin share text into unique {url, author, title, raw_text} records."""
    records = []
    seen = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        author = None
        title = None
        author_match = AUTHOR_RE.search(line)
        if author_match:
            author = author_match.group(1).strip() or None
            rest = line[author_match.end():]
            title_match = re.match(r'\s*(.+?)\s*https?://', rest, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip() or None

        for url in URL_RE.findall(line):
            url = url.strip()
            if not url or not HOST_RE.search(url) or url in seen:
                continue
            seen.add(url)
            records.append({'url': url, 'author': author, 'title': title, 'raw_text': line})
    return records


DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def _positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _collect_video_items(keyword, status, window):
    """按筛选条件汇总视频列表（含最新指标与窗口增长）。"""
    query = DouyinVideo.query
    if keyword:
        like = f'%{keyword}%'
        query = query.filter(
            db.or_(DouyinVideo.title.like(like), DouyinVideo.author.like(like))
        )
    videos = query.all()
    ids = [video.id for video in videos]

    latest_rows = {
        row.video_id: row
        for row in DouyinVideoLatest.query.filter(DouyinVideoLatest.video_id.in_(ids)).all()
    } if ids else {}
    growth = stats.growth_map(ids, window) if ids else {}

    items = []
    for video, item in zip(videos, douyin_videos_schema.dump(videos)):
        latest = latest_rows.get(video.id)
        if not stats.matches_status(latest, status):
            continue
        item['latest'] = monitor.latest_to_dict(latest)
        item['growth'] = growth.get(video.id) or stats.empty_growth(window)
        items.append(item)
    return items


def _csv_response(filename, header, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    return Response(
        '\ufeff' + buffer.getvalue(),
        content_type='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


def _format_time(value):
    if not value:
        return ''
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return str(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')


@api_bp.route('/douyin/videos', methods=['GET'])
@require_auth
def get_douyin_videos():
    page = _positive_int(request.args.get('page'), 1)
    per_page = min(_positive_int(request.args.get('per_page'), DEFAULT_PER_PAGE), MAX_PER_PAGE)

    keyword = (request.args.get('q') or '').strip()
    status = request.args.get('status') or 'all'
    sort = request.args.get('sort') or 'created_at'
    if sort not in stats.SORT_FIELDS:
        sort = 'created_at'
    order = 'asc' if (request.args.get('order') or '').lower() == 'asc' else 'desc'
    window = stats.parse_window(request.args.get('window'))

    items = _collect_video_items(keyword, status, window)
    items.sort(key=lambda item: stats.sort_value(item, sort), reverse=(order == 'desc'))

    total = len(items)
    start = (page - 1) * per_page
    page_items = items[start:start + per_page]

    return jsonify({
        'items': page_items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'window': window,
        'sort': sort,
        'order': order,
    })


@api_bp.route('/douyin/videos/export', methods=['GET'])
@require_auth
def export_douyin_videos():
    keyword = (request.args.get('q') or '').strip()
    status = request.args.get('status') or 'all'
    sort = request.args.get('sort') or 'created_at'
    if sort not in stats.SORT_FIELDS:
        sort = 'created_at'
    order = 'asc' if (request.args.get('order') or '').lower() == 'asc' else 'desc'
    window = stats.parse_window(request.args.get('window'))

    items = _collect_video_items(keyword, status, window)
    items.sort(key=lambda item: stats.sort_value(item, sort), reverse=(order == 'desc'))

    header = [
        '视频ID', '链接', '作者', '标题',
        '点赞', '评论', '分享', '收藏', '播放', '互动总量',
        '增长-点赞', '增长-评论', '增长-分享', '增长-收藏', '增长-互动', '增长率',
        '采集状态', '最近采集时间', '最近错误', '导入时间',
    ]
    rows = []
    for item in items:
        latest = item.get('latest') or {}
        growth = item.get('growth') or {}
        available = bool(growth.get('available'))
        if not latest:
            status_text = '未采集'
        elif latest.get('last_error'):
            status_text = '采集失败'
        else:
            status_text = '已采集'
        rows.append([
            item.get('id'),
            item.get('url'),
            item.get('author') or '',
            item.get('title') or '',
            latest.get('digg_count') or 0,
            latest.get('comment_count') or 0,
            latest.get('share_count') or 0,
            latest.get('collect_count') or 0,
            latest.get('play_count') or 0,
            sum(int(latest.get(f'{metric}_count') or 0) for metric in stats.METRICS),
            growth.get('digg_count') if available else '',
            growth.get('comment_count') if available else '',
            growth.get('share_count') if available else '',
            growth.get('collect_count') if available else '',
            growth.get('interaction') if available else '',
            f"{growth['rate'] * 100:.2f}%" if available and growth.get('rate') is not None else '',
            status_text,
            _format_time(latest.get('captured_at')),
            latest.get('last_error') or '',
            _format_time(item.get('created_at')),
        ])

    stamp = datetime.now(TIMEZONE).strftime('%Y%m%d_%H%M%S')
    return _csv_response(f'douyin_videos_{window}_{stamp}.csv', header, rows)



@api_bp.route('/douyin/videos', methods=['POST'])
@require_auth
def create_douyin_videos():
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': '请先粘贴抖音分享内容'}), 400

    records = extract_douyin_links(text)
    if not records:
        return jsonify({'error': '未识别到有效的抖音链接'}), 400

    created = []
    skipped = []
    for record in records:
        if DouyinVideo.query.filter_by(url=record['url']).first() is not None:
            skipped.append(record['url'])
            continue
        video = DouyinVideo(**record)
        db.session.add(video)
        created.append(video)

    db.session.commit()

    run_id = None
    cfg = monitor.get_config()
    if created and cfg.fetch_on_import:
        run, _ = monitor.start_run(
            current_app._get_current_object(),
            trigger_type='import',
            video_ids=[video.id for video in created],
        )
        if run is not None:
            run_id = run.id

    return jsonify({
        'created': douyin_videos_schema.dump(created),
        'skipped': skipped,
        'run_id': run_id,
    }), 201


def _snapshot_items(video_id, window, limit):
    query = DouyinVideoSnapshot.query.filter_by(video_id=video_id)
    start = stats.window_start(window) if window else None
    if start is not None:
        query = query.filter(DouyinVideoSnapshot.captured_at >= start)

    rows = (
        query
        .order_by(DouyinVideoSnapshot.captured_at.desc(), DouyinVideoSnapshot.id.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()

    items = []
    previous = None
    for row in rows:
        item = monitor.snapshot_to_dict(row)
        item['growth'] = None
        if previous is not None and row.error is None:
            item['growth'] = {
                metric: int(getattr(row, metric) or 0) - int(getattr(previous, metric) or 0)
                for metric in stats.METRICS
            }
            item['growth']['interaction'] = sum(item['growth'].values())
        items.append(item)
        if row.error is None:
            previous = row
    return items


@api_bp.route('/douyin/videos/<int:video_id>/snapshots', methods=['GET'])
@require_auth
def get_douyin_video_snapshots(video_id):
    DouyinVideo.query.get_or_404(video_id)

    try:
        limit = int(request.args.get('limit', 100))
    except (TypeError, ValueError):
        limit = 100
    limit = min(max(limit, 1), 500)

    window = request.args.get('window')
    window = stats.parse_window(window) if window else None

    items = _snapshot_items(video_id, window, limit)
    growth = stats.growth_map([video_id], window or stats.DEFAULT_WINDOW).get(video_id)

    return jsonify({
        'items': items,
        'window': window,
        'growth': growth or stats.empty_growth(window or stats.DEFAULT_WINDOW),
    })


@api_bp.route('/douyin/videos/<int:video_id>/snapshots/export', methods=['GET'])
@require_auth
def export_douyin_video_snapshots(video_id):
    DouyinVideo.query.get_or_404(video_id)

    try:
        limit = int(request.args.get('limit', 5000))
    except (TypeError, ValueError):
        limit = 5000
    limit = min(max(limit, 1), 10000)

    window = request.args.get('window')
    window = stats.parse_window(window) if window else None

    items = _snapshot_items(video_id, window, limit)
    header = [
        '采集时间', '点赞', '评论', '分享', '收藏', '播放',
        '增长-点赞', '增长-评论', '增长-分享', '增长-收藏', '增长-互动', '错误',
    ]
    rows = []
    for item in items:
        growth = item.get('growth') or {}
        rows.append([
            _format_time(item.get('captured_at')),
            item.get('digg_count'),
            item.get('comment_count'),
            item.get('share_count'),
            item.get('collect_count'),
            item.get('play_count'),
            growth.get('digg_count', ''),
            growth.get('comment_count', ''),
            growth.get('share_count', ''),
            growth.get('collect_count', ''),
            growth.get('interaction', ''),
            item.get('error') or '',
        ])

    stamp = datetime.now(TIMEZONE).strftime('%Y%m%d_%H%M%S')
    return _csv_response(f'douyin_video_{video_id}_snapshots_{stamp}.csv', header, rows)



@api_bp.route('/douyin/videos/<int:video_id>', methods=['DELETE'])
@require_auth
def delete_douyin_video(video_id):
    video = DouyinVideo.query.get_or_404(video_id)
    DouyinVideoSnapshot.query.filter_by(video_id=video_id).delete(synchronize_session=False)
    DouyinVideoLatest.query.filter_by(video_id=video_id).delete(synchronize_session=False)
    db.session.delete(video)
    db.session.commit()
    return '', 204
