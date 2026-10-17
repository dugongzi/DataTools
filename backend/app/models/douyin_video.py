from datetime import datetime

from backend.app import db


class DouyinVideo(db.Model):
    __tablename__ = 'douyin_videos'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), unique=True, nullable=False)
    author = db.Column(db.String(120))
    title = db.Column(db.String(255))
    raw_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DouyinVideo {self.url}>'
