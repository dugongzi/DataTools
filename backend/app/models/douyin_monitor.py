from datetime import datetime

from backend.app import db


class DouyinMonitorConfig(db.Model):
    """抖音采集配置（单行，id 固定为 1）"""

    __tablename__ = 'douyin_monitor_config'

    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    schedule_type = db.Column(db.String(16), nullable=False, default='interval')
    interval_minutes = db.Column(db.Integer, nullable=False, default=30)
    cron_expression = db.Column(db.String(64), nullable=False, default='0 */2 * * *')
    concurrency = db.Column(db.Integer, nullable=False, default=3)
    retry_times = db.Column(db.Integer, nullable=False, default=2)
    retry_delay_seconds = db.Column(db.Integer, nullable=False, default=5)
    fetch_on_import = db.Column(db.Boolean, nullable=False, default=True)
    stale_minutes = db.Column(db.Integer, nullable=False, default=15)
    next_run_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(80))


class DouyinVideoLatest(db.Model):
    """每个视频的最新互动指标"""

    __tablename__ = 'douyin_video_latest'

    video_id = db.Column(
        db.Integer,
        db.ForeignKey('douyin_videos.id', ondelete='CASCADE'),
        primary_key=True,
    )
    aweme_id = db.Column(db.String(32))
    digg_count = db.Column(db.BigInteger, default=0)
    comment_count = db.Column(db.BigInteger, default=0)
    share_count = db.Column(db.BigInteger, default=0)
    collect_count = db.Column(db.BigInteger, default=0)
    play_count = db.Column(db.BigInteger, default=0)
    captured_at = db.Column(db.DateTime)
    last_error = db.Column(db.String(255))


class DouyinVideoSnapshot(db.Model):
    """互动指标历史快照"""

    __tablename__ = 'douyin_video_snapshots'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    video_id = db.Column(
        db.Integer,
        db.ForeignKey('douyin_videos.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    aweme_id = db.Column(db.String(32))
    digg_count = db.Column(db.BigInteger)
    comment_count = db.Column(db.BigInteger)
    share_count = db.Column(db.BigInteger)
    collect_count = db.Column(db.BigInteger)
    play_count = db.Column(db.BigInteger)
    captured_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    error = db.Column(db.String(255))


class DouyinMonitorRun(db.Model):
    """采集运行记录"""

    __tablename__ = 'douyin_monitor_runs'

    id = db.Column(db.Integer, primary_key=True)
    trigger_type = db.Column(db.String(16), nullable=False, default='manual')
    status = db.Column(db.String(16), nullable=False, default='running')
    total = db.Column(db.Integer, nullable=False, default=0)
    success_count = db.Column(db.Integer, nullable=False, default=0)
    failed_count = db.Column(db.Integer, nullable=False, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)
    message = db.Column(db.String(255))
