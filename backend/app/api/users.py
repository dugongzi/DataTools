from flask import jsonify, request
from backend.app.api import api_bp
from backend.app.api.auth import require_auth
from backend.app.models.user import User
from backend.app.schemas.user import UserSchema
from backend.app import db

user_schema = UserSchema()
users_schema = UserSchema(many=True)


@api_bp.route('/users', methods=['GET'])
@require_auth
def get_users():
    users = User.query.all()
    return jsonify(users_schema.dump(users))


@api_bp.route('/users/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user_schema.dump(user))


@api_bp.route('/users', methods=['POST'])
@require_auth
def create_user():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    email = data.get('email') or (f'{username}@datatools.local' if username else None)

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'error': 'Username already exists'}), 409

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'Email already exists'}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user_schema.dump(user)), 201


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}

    username = data.get('username', user.username)
    email = data.get('email', user.email)

    if username and User.query.filter(User.username == username, User.id != user_id).first() is not None:
        return jsonify({'error': 'Username already exists'}), 409

    if email and User.query.filter(User.email == email, User.id != user_id).first() is not None:
        return jsonify({'error': 'Email already exists'}), 409

    user.username = username
    user.email = email
    password = data.get('password')
    if password:
        user.set_password(password)
    db.session.commit()
    return jsonify(user_schema.dump(user))


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_auth
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204


@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})
