import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, jsonify, request

from backend.app.api import api_bp
from backend.app.models.user import User


def _create_access_token(username, role):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            'sub': username,
            'role': role,
            'iat': now,
            'exp': now + timedelta(seconds=current_app.config['ACCESS_TOKEN_MAX_AGE']),
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256',
    )


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get('Authorization', '').split()
        if len(authorization) != 2 or authorization[0].lower() != 'bearer':
            return jsonify({'error': 'Authentication required'}), 401

        try:
            claims = jwt.decode(
                authorization[1],
                current_app.config['SECRET_KEY'],
                algorithms=['HS256'],
            )
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid or expired token'}), 401

        if not isinstance(claims, dict) or not claims.get('sub'):
            return jsonify({'error': 'Invalid token claims'}), 401

        return view(*args, **kwargs)

    return wrapped


@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data.get('username')
    password = data.get('password')
    admin_username = current_app.config['ADMIN_USERNAME']
    admin_password = current_app.config['ADMIN_PASSWORD']
    admin_role = current_app.config['ADMIN_ROLE']

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({'error': 'Invalid username or password'}), 401

    authenticated_username = None
    if (admin_username and admin_password
            and secrets.compare_digest(username, admin_username)
            and secrets.compare_digest(password, admin_password)):
        authenticated_username = admin_username
    else:
        user = User.query.filter_by(username=username).first()
        if user is not None and user.check_password(password):
            authenticated_username = user.username

    if authenticated_username is None:
        return jsonify({'error': 'Invalid username or password'}), 401

    token = _create_access_token(authenticated_username, admin_role)
    return jsonify({
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': current_app.config['ACCESS_TOKEN_MAX_AGE'],
        'user': {
            'username': authenticated_username,
            'role': admin_role,
        },
    })
