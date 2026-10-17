from flask import Blueprint

api_bp = Blueprint('api', __name__)

from backend.app.api import auth, douyin, users
