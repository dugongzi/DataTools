from backend.app import ma
from backend.app.models.douyin_video import DouyinVideo


class DouyinVideoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DouyinVideo
        load_instance = True
        include_fk = True


douyin_video_schema = DouyinVideoSchema()
douyin_videos_schema = DouyinVideoSchema(many=True)
