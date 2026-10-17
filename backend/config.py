import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(basedir), '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    ADMIN_ROLE = os.environ.get('ADMIN_ROLE', 'superadmin')
    ACCESS_TOKEN_MAX_AGE = int(os.environ.get('ACCESS_TOKEN_MAX_AGE', '3600'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:"
        f"{os.environ.get('MYSQL_PASSWORD')}@"
        f"127.0.0.1:{os.environ.get('MYSQL_PORT')}/"
        f"{os.environ.get('MYSQL_DATABASE')}"
        f"?charset=utf8mb4"
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:"
        f"{os.environ.get('MYSQL_PASSWORD')}@"
        "mysql:3306/"
        f"{os.environ.get('MYSQL_DATABASE')}"
    )


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
