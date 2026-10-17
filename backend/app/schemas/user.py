from backend.app import ma
from backend.app.models.user import User


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        exclude = ('password_hash',)


user_schema = UserSchema()
users_schema = UserSchema(many=True)
