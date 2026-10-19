"""抖音视频统计：时间窗口、增长值与概览聚合。"""
from bisect import bisect_right
from datetime import datetime, timedelta

from sqlalchemy import func, or_

from backend.app import db
from backend.app.models.douyin_monitor import DouyinVideoLatest, DouyinVideoSnapshot
from backend.app.models.douyin_video import DouyinVideo
from backend.app.services.douyin_monitor import iso_utc, latest_to_dict

WINDOWS = {
    '1h': timedelta(hours=1),
    '6h': timedelta(hours=6),
    '24h': timedelta(hours=24),
    '7d': timedelta(days=7),
    'all': None,
}
DEFAULT_WINDOW = '24h'
METRICS = ('digg_count', 'comment_count', 'share_count', 'collect_count')
TREND_BUCKETS = {
    '1h': timedelta(minutes=5),
    '6h': timedelta(minutes=30),
    '24h': timedelta(hours=1),
    '7d': timedelta(hours=6),
    'all': timedelta(days=1),
}
MAX_TREND_POINTS = 48
SORT_FIELDS = {
    'created_at',
    'captured_at',
    'digg',
    'comment',
    'share',
    'collect',
    'interaction',
    'growth',
    'growth_digg',
    'growth_comment',
    'growth_share',
    'growth_collect',
    'growth_rate',
}


def parse_window(value):
    return value if value in WINDOWS else DEFAULT_WINDOW


def window_start(window):
    delta = WINDOWS[window]
    if delta is None:
        return None
    return datetime.utcnow() - delta


def empty_growth(window):
    return {
        'window': window,
        'available': False,
        'from': None,
        'to': None,
        'digg_count': None,
        'comment_count': None,
        'share_count': None,
        'collect_count': None,
        'interaction': None,
        'rate': None,
        'points': 0,
    }


def growth_map(video_ids, window):
    """计算每个视频在窗口内的增长值：窗口内最后一条快照 - 第一条快照。"""
    if not video_ids:
        return {}

    start = window_start(window)
    rn_first = func.row_number().over(
        partition_by=DouyinVideoSnapshot.video_id,
        order_by=(DouyinVideoSnapshot.captured_at.asc(), DouyinVideoSnapshot.id.asc()),
    ).label('rn_first')
    rn_last = func.row_number().over(
        partition_by=DouyinVideoSnapshot.video_id,
        order_by=(DouyinVideoSnapshot.captured_at.desc(), DouyinVideoSnapshot.id.desc()),
    ).label('rn_last')
    total_count = func.count(DouyinVideoSnapshot.id).over(
        partition_by=DouyinVideoSnapshot.video_id
    ).label('total_count')

    query = db.session.query(
        DouyinVideoSnapshot.video_id.label('video_id'),
        DouyinVideoSnapshot.digg_count.label('digg_count'),
        DouyinVideoSnapshot.comment_count.label('comment_count'),
        DouyinVideoSnapshot.share_count.label('share_count'),
        DouyinVideoSnapshot.collect_count.label('collect_count'),
        DouyinVideoSnapshot.captured_at.label('captured_at'),
        rn_first,
        rn_last,
        total_count,
    ).filter(
        DouyinVideoSnapshot.video_id.in_(video_ids),
        DouyinVideoSnapshot.error.is_(None),
    )
    if start is not None:
        query = query.filter(DouyinVideoSnapshot.captured_at >= start)

    ranked = query.subquery()
    rows = db.session.query(ranked).filter(
        or_(ranked.c.rn_first == 1, ranked.c.rn_last == 1)
    ).all()

    grouped = {}
    for row in rows:
        entry = grouped.setdefault(row.video_id, {'total': row.total_count})
        entry['first' if row.rn_first == 1 else 'last'] = row

    result = {}
    for video_id, entry in grouped.items():
        first = entry.get('first')
        last = entry.get('last')
        if first is None or last is None or (entry.get('total') or 0) < 2:
            result[video_id] = empty_growth(window)
            continue

        deltas = {
            metric: int(getattr(last, metric) or 0) - int(getattr(first, metric) or 0)
            for metric in METRICS
        }
        interaction = sum(deltas.values())
        base = sum(int(getattr(first, metric) or 0) for metric in METRICS)
        result[video_id] = {
            'window': window,
            'available': True,
            'from': iso_utc(first.captured_at),
            'to': iso_utc(last.captured_at),
            **deltas,
            'interaction': interaction,
            'rate': (interaction / base) if base > 0 else None,
            'points': entry.get('total') or 0,
        }

    return result


def latest_interaction(latest):
    if latest is None:
        return 0
    return sum(int(getattr(latest, metric) or 0) for metric in METRICS)


def build_overview(window=DEFAULT_WINDOW, top_n=3):
    window = parse_window(window)
    videos = DouyinVideo.query.order_by(DouyinVideo.id).all()
    ids = [video.id for video in videos]
    latest_map = {
        row.video_id: row
        for row in DouyinVideoLatest.query.filter(DouyinVideoLatest.video_id.in_(ids)).all()
    } if ids else {}
    growth = growth_map(ids, window)

    totals = {metric: 0 for metric in METRICS}
    captured = 0
    failed = 0
    last_captured = None

    for video in videos:
        latest = latest_map.get(video.id)
        if latest is None or latest.captured_at is None:
            continue
        if latest.last_error:
            failed += 1
            continue
        captured += 1
        for metric in METRICS:
            totals[metric] += int(getattr(latest, metric) or 0)
        if last_captured is None or latest.captured_at > last_captured:
            last_captured = latest.captured_at

    total_interaction = sum(totals.values())
    growth_totals = {
        metric: sum(item[metric] for item in growth.values() if item['available'])
        for metric in METRICS
    }
    growth_interaction = sum(growth_totals.values())
    base_interaction = total_interaction - growth_interaction
    growth_rate = (growth_interaction / base_interaction) if base_interaction > 0 else None

    ranked = sorted(
        (video for video in videos if growth.get(video.id, {}).get('available')),
        key=lambda video: growth[video.id]['interaction'],
        reverse=True,
    )[:top_n]

    top_videos = [
        {
            'id': video.id,
            'url': video.url,
            'author': video.author,
            'title': video.title,
            'raw_text': video.raw_text,
            'created_at': iso_utc(video.created_at),
            'updated_at': iso_utc(video.updated_at),
            'latest': latest_to_dict(latest_map.get(video.id)),
            'growth': growth[video.id],
        }
        for video in ranked
    ]

    return {
        'window': window,
        'window_start': iso_utc(window_start(window)),
        'total_videos': len(videos),
        'captured_videos': captured,
        'failed_videos': failed,
        'pending_videos': max(0, len(videos) - captured - failed),
        'totals': {**totals, 'interaction': total_interaction},
        'growth': {**growth_totals, 'interaction': growth_interaction, 'rate': growth_rate},
        'last_captured_at': iso_utc(last_captured),
        'top_videos': top_videos,
    }


def _baseline_snapshots(video_ids, start):
    """取窗口开始前每个视频的最后一条有效快照，作为首个分桶的增长基准。"""
    if start is None or not video_ids:
        return {}

    rn = func.row_number().over(
        partition_by=DouyinVideoSnapshot.video_id,
        order_by=(DouyinVideoSnapshot.captured_at.desc(), DouyinVideoSnapshot.id.desc()),
    ).label('rn')
    ranked = db.session.query(
        DouyinVideoSnapshot.video_id.label('video_id'),
        DouyinVideoSnapshot.digg_count.label('digg_count'),
        DouyinVideoSnapshot.comment_count.label('comment_count'),
        DouyinVideoSnapshot.share_count.label('share_count'),
        DouyinVideoSnapshot.collect_count.label('collect_count'),
        DouyinVideoSnapshot.captured_at.label('captured_at'),
        rn,
    ).filter(
        DouyinVideoSnapshot.video_id.in_(video_ids),
        DouyinVideoSnapshot.error.is_(None),
        DouyinVideoSnapshot.captured_at < start,
    ).subquery()

    rows = db.session.query(ranked).filter(ranked.c.rn == 1).all()
    return {row.video_id: row for row in rows}


def _trend_edges(window, snapshots):
    """构造趋势分桶边界，'all' 以最早快照为起点，并限制最大点数。"""
    now = datetime.utcnow()
    start = window_start(window)
    if start is None:
        start = min(
            (snapshot.captured_at for snapshot in snapshots if snapshot.captured_at),
            default=now,
        )

    size = TREND_BUCKETS.get(window, timedelta(hours=1))
    span = now - start
    if span < timedelta(0):
        span = timedelta(0)
    while span / size > MAX_TREND_POINTS:
        size *= 2

    count = max(1, int(span / size) + 1)
    edges = [start + size * index for index in range(count + 1)]
    return edges, size


def _trend_points(edges, buckets):
    return [
        {
            'time': iso_utc(edges[index + 1]),
            **bucket,
            'interaction': sum(bucket.values()),
        }
        for index, bucket in enumerate(buckets)
    ]


def build_trend_series(window, video_ids):
    """按视频分桶汇总新增互动，返回 (聚合趋势, 每条视频趋势)。"""
    empty = {'bucket_seconds': 0, 'points': []}
    if not video_ids:
        return empty, []

    start = window_start(window)
    query = db.session.query(
        DouyinVideoSnapshot.video_id.label('video_id'),
        DouyinVideoSnapshot.digg_count.label('digg_count'),
        DouyinVideoSnapshot.comment_count.label('comment_count'),
        DouyinVideoSnapshot.share_count.label('share_count'),
        DouyinVideoSnapshot.collect_count.label('collect_count'),
        DouyinVideoSnapshot.captured_at.label('captured_at'),
    ).filter(
        DouyinVideoSnapshot.video_id.in_(video_ids),
        DouyinVideoSnapshot.error.is_(None),
    )
    if start is not None:
        query = query.filter(DouyinVideoSnapshot.captured_at >= start)

    rows = query.order_by(
        DouyinVideoSnapshot.video_id.asc(),
        DouyinVideoSnapshot.captured_at.asc(),
        DouyinVideoSnapshot.id.asc(),
    ).all()
    if not rows:
        return empty, []

    edges, size = _trend_edges(window, rows)
    bucket_count = len(edges) - 1
    aggregate = [{metric: 0 for metric in METRICS} for _ in range(bucket_count)]

    grouped = {}
    for row in rows:
        grouped.setdefault(row.video_id, []).append(row)

    baseline = _baseline_snapshots(list(grouped), start)
    per_video = {}
    for video_id, items in grouped.items():
        buckets = [{metric: 0 for metric in METRICS} for _ in range(bucket_count)]
        previous = baseline.get(video_id)
        for row in items:
            if previous is not None and row.captured_at is not None:
                index = bisect_right(edges, row.captured_at) - 1
                index = min(max(index, 0), bucket_count - 1)
                for metric in METRICS:
                    delta = int(getattr(row, metric) or 0) - int(getattr(previous, metric) or 0)
                    buckets[index][metric] += delta
                    aggregate[index][metric] += delta
            previous = row
        per_video[video_id] = buckets

    bucket_seconds = int(size.total_seconds())
    trend = {'bucket_seconds': bucket_seconds, 'points': _trend_points(edges, aggregate)}
    series = [
        {
            'video_id': video_id,
            'bucket_seconds': bucket_seconds,
            'points': _trend_points(edges, buckets),
        }
        for video_id, buckets in per_video.items()
    ]
    return trend, series


def build_author_ranking(top_n=8):
    """按作者汇总最新快照的累计互动，返回互动最高的前 N 位作者。"""
    videos = DouyinVideo.query.order_by(DouyinVideo.id).all()
    ids = [video.id for video in videos]
    if not ids:
        return []

    latest_map = {
        row.video_id: row
        for row in DouyinVideoLatest.query.filter(DouyinVideoLatest.video_id.in_(ids)).all()
    }

    totals = {}
    for video in videos:
        latest = latest_map.get(video.id)
        if latest is None or latest.captured_at is None or latest.last_error:
            continue
        author = video.author or '未知作者'
        totals[author] = totals.get(author, 0) + latest_interaction(latest)

    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:top_n]
    return [{'author': author, 'interaction': value} for author, value in ranked]


def build_charts(window=DEFAULT_WINDOW, top_n=8, video_ids=None):
    """主页图表数据：增长趋势、互动构成、增长 Top 视频、作者排行。

    video_ids 为空表示全部视频；非空时趋势只统计所选视频，并返回逐视频序列。
    """
    window = parse_window(window)
    overview = build_overview(window, top_n)
    videos = DouyinVideo.query.order_by(DouyinVideo.id).all()
    wanted = set(video_ids) if video_ids else None
    selected = [video for video in videos if wanted is None or video.id in wanted]
    trend, series = build_trend_series(window, [video.id for video in selected])

    meta = {video.id: video for video in selected}
    # 未选视频时不返回逐视频序列，避免视频较多时响应体过大。
    trends = [] if wanted is None else [
        {
            'video_id': item['video_id'],
            'title': meta[item['video_id']].title,
            'author': meta[item['video_id']].author,
            'bucket_seconds': item['bucket_seconds'],
            'points': item['points'],
        }
        for item in series
        if item['video_id'] in meta
    ]

    return {
        'window': window,
        'trend': trend,
        'trends': trends,
        'videos': [
            {
                'id': video.id,
                'url': video.url,
                'title': video.title,
                'author': video.author,
            }
            for video in videos
        ],
        'composition': overview['totals'],
        'top_videos': overview['top_videos'],
        'authors': build_author_ranking(top_n),
    }


def matches_status(latest, status):
    if status == 'captured':
        return latest is not None and latest.last_error is None and latest.captured_at is not None
    if status == 'failed':
        return latest is not None and latest.last_error is not None
    if status == 'pending':
        return latest is None or latest.captured_at is None
    return True


def sort_value(item, sort):
    latest = item.get('latest') or {}
    growth = item.get('growth') or {}

    if sort in ('digg', 'comment', 'share', 'collect'):
        return latest.get(f'{sort}_count') or -1
    if sort == 'interaction':
        return sum(int(latest.get(f'{metric}_count') or 0) for metric in METRICS)
    if sort == 'growth':
        return growth.get('interaction') if growth.get('available') else -1
    if sort.startswith('growth_') and sort != 'growth_rate':
        metric = f'{sort[len("growth_"):]}_count'
        return growth.get(metric) if growth.get('available') else -1
    if sort == 'growth_rate':
        rate = growth.get('rate')
        return rate if rate is not None else -1
    if sort == 'captured_at':
        return latest.get('captured_at') or ''
    return item.get('created_at') or ''
