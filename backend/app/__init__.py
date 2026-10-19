from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from backend.config import config

db = SQLAlchemy()
ma = Marshmallow()


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    ma.init_app(app)
    CORS(app)
    
    # 注册蓝图
    from backend.app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # 确保所有模型都已导入，create_all 才能建表
    from backend.app import models  # noqa: F401

    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app
