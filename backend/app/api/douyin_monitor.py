from flask import current_app, g, jsonify, request

from backend.app.api import api_bp
from backend.app.api.auth import require_auth
from backend.app.models.douyin_monitor import DouyinMonitorRun
from backend.app.services import douyin_monitor as monitor
from backend.app.services import douyin_stats as stats


@api_bp.route('/douyin/monitor/overview', methods=['GET'])
@require_auth
def get_douyin_monitor_overview():
    window = stats.parse_window(request.args.get('window'))
    try:
        top_n = int(request.args.get('top', 3))
    except (TypeError, ValueError):
        top_n = 3
    top_n = min(max(top_n, 1), 10)
    return jsonify(stats.build_overview(window, top_n))


def _parse_video_ids():
    raw = request.args.get('video_ids') or request.args.get('video_id')
    if not raw:
        return None
    ids = []
    for part in raw.split(','):
        try:
            value = int(part.strip())
        except ValueError:
            continue
        if value not in ids:
            ids.append(value)
    return ids[:10] or None


@api_bp.route('/douyin/monitor/charts', methods=['GET'])
@require_auth
def get_douyin_monitor_charts():
    window = stats.parse_window(request.args.get('window'))
    try:
        top_n = int(request.args.get('top', 8))
    except (TypeError, ValueError):
        top_n = 8
    top_n = min(max(top_n, 1), 20)
    return jsonify(stats.build_charts(window, top_n, _parse_video_ids()))


@api_bp.route('/douyin/monitor/config', methods=['GET'])
@require_auth
def get_douyin_monitor_config():
    return jsonify(monitor.config_to_dict(monitor.get_config()))


@api_bp.route('/douyin/monitor/config', methods=['PUT'])
@require_auth
def update_douyin_monitor_config():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': '请求体必须是 JSON 对象'}), 400

    cfg, errors = monitor.save_config(data, getattr(g, 'username', None))
    if errors:
        return jsonify({'error': '配置校验失败', 'fields': errors}), 400

    return jsonify(monitor.config_to_dict(cfg))


@api_bp.route('/douyin/monitor/status', methods=['GET'])
@require_auth
def get_douyin_monitor_status():
    return jsonify(monitor.get_status())


@api_bp.route('/douyin/monitor/run', methods=['POST'])
@require_auth
def trigger_douyin_monitor_run():
    data = request.get_json(silent=True) or {}
    raw_ids = data.get('video_ids')
    video_ids = None
    if raw_ids is not None:
        if not isinstance(raw_ids, list) or not raw_ids:
            return jsonify({'error': 'video_ids 必须是非空数组'}), 400
        try:
            video_ids = [int(value) for value in raw_ids]
        except (TypeError, ValueError):
            return jsonify({'error': 'video_ids 必须由整数组成'}), 400

    run, running = monitor.start_run(
        current_app._get_current_object(),
        trigger_type='manual',
        video_ids=video_ids,
    )
    if run is None:
        return jsonify({
            'error': '已有采集任务在运行',
            'run': monitor.run_to_dict(running),
        }), 409

    return jsonify({'run_id': run.id, 'run': monitor.run_to_dict(run)}), 202


@api_bp.route('/douyin/monitor/runs/<int:run_id>', methods=['GET'])
@require_auth
def get_douyin_monitor_run(run_id):
    run = DouyinMonitorRun.query.get_or_404(run_id)
    return jsonify(monitor.run_to_dict(run))


@api_bp.route('/douyin/monitor/run/failed', methods=['POST'])
@require_auth
def retry_douyin_monitor_failed():
    video_ids = monitor.failed_video_ids()
    if not video_ids:
        return jsonify({'error': '没有采集失败的视频'}), 400

    run, running = monitor.start_run(
        current_app._get_current_object(),
        trigger_type='manual',
        video_ids=video_ids,
    )
    if run is None:
        return jsonify({
            'error': '已有采集任务在运行',
            'run': monitor.run_to_dict(running),
        }), 409

    return jsonify({
        'run_id': run.id,
        'run': monitor.run_to_dict(run),
        'total': len(video_ids),
    }), 202


@api_bp.route('/douyin/monitor/runs', methods=['GET'])
@require_auth
def list_douyin_monitor_runs():
    try:
        limit = int(request.args.get('limit', 20))
    except (TypeError, ValueError):
        limit = 20
    limit = min(max(limit, 1), 100)

    runs = (
        DouyinMonitorRun.query
        .order_by(DouyinMonitorRun.id.desc())
        .limit(limit)
        .all()
    )
    return jsonify({'items': [monitor.run_to_dict(run) for run in runs]})
