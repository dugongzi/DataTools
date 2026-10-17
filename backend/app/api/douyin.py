import re

from flask import jsonify, request

from backend.app import db
from backend.app.api import api_bp
from backend.app.api.auth import require_auth
from backend.app.models.douyin_video import DouyinVideo
from backend.app.schemas.douyin_video import douyin_videos_schema

URL_RE = re.compile(r'https?://[^\s，。、；！？（）()\[\]【】<>"\'|]+', re.IGNORECASE)
HOST_RE = re.compile(r'(^|\.)douyin\.com(?::\d+)?(?:/|$)', re.IGNORECASE)
AUTHOR_RE = re.compile(r'【\s*(.+?)\s*的[^】]{0,12}作品\s*】')


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


@api_bp.route('/douyin/videos', methods=['GET'])
@require_auth
def get_douyin_videos():
    page = _positive_int(request.args.get('page'), 1)
    per_page = min(_positive_int(request.args.get('per_page'), DEFAULT_PER_PAGE), MAX_PER_PAGE)

    pagination = DouyinVideo.query.order_by(
        DouyinVideo.created_at.desc(), DouyinVideo.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': douyin_videos_schema.dump(pagination.items),
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    })


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
    return jsonify({
        'created': douyin_videos_schema.dump(created),
        'skipped': skipped,
    }), 201


@api_bp.route('/douyin/videos/<int:video_id>', methods=['DELETE'])
@require_auth
def delete_douyin_video(video_id):
    video = DouyinVideo.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    return '', 204
