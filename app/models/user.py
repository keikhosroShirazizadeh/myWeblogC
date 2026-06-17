from datetime import datetime
from bson import ObjectId
from flask_login import UserMixin
from app.extensions import mongo, bcrypt


class User(UserMixin):
    def __init__(self, data):
        self._id = data['_id']
        self.id = str(data['_id'])
        self.username = data.get('username', '')
        self.email = data.get('email', '')
        self.password_hash = data.get('password_hash', '')
        self.role = data.get('role', 'user')
        self.profile = data.get('profile', {})
        self._is_active = data.get('is_active', True)
        self.created_at = data.get('created_at', datetime.utcnow())

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return self._is_active

    @property
    def is_admin(self):
        return self.role == 'admin'

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def update_profile(self, profile_data):
        mongo.db.users.update_one(
            {'_id': self._id},
            {'$set': {'profile': profile_data, 'updated_at': datetime.utcnow()}}
        )
        self.profile = profile_data

    def change_password(self, new_password):
        new_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        mongo.db.users.update_one(
            {'_id': self._id},
            {'$set': {'password_hash': new_hash}}
        )

    @staticmethod
    def find_by_email(email):
        data = mongo.db.users.find_one({'email': email.lower()})
        return User(data) if data else None

    @staticmethod
    def find_by_username(username):
        data = mongo.db.users.find_one({'username': username})
        return User(data) if data else None

    @staticmethod
    def find_by_id(user_id):
        try:
            data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            return User(data) if data else None
        except Exception:
            return None

    @staticmethod
    def exists(email=None, username=None):
        query = {}
        if email:
            query['email'] = email.lower()
        if username:
            query['username'] = username
        return bool(query) and mongo.db.users.count_documents(query) > 0

    @staticmethod
    def create(username, email, password, role='user'):
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        doc = {
            'username': username,
            'email': email.lower(),
            'password_hash': password_hash,
            'role': role,
            'profile': {
                'first_name': '',
                'last_name': '',
                'avatar': '',
                'bio_en': '',
                'bio_fa': '',
                'phone': '',
            },
            'is_active': True,
            'created_at': datetime.utcnow(),
        }
        result = mongo.db.users.insert_one(doc)
        return str(result.inserted_id)

    @staticmethod
    def get_all():
        return [User(d) for d in mongo.db.users.find().sort('created_at', -1)]


def init_admin():
    if mongo.db.users.count_documents({'role': 'admin'}) == 0:
        password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
        mongo.db.users.insert_one({
            'username': 'admin',
            'email': 'admin@example.com',
            'password_hash': password_hash,
            'role': 'admin',
            'profile': {
                'first_name': 'Admin',
                'last_name': '',
                'avatar': '',
                'bio_en': 'Site Administrator',
                'bio_fa': 'مدیر سایت',
                'phone': '',
            },
            'is_active': True,
            'created_at': datetime.utcnow(),
        })
        print("Default admin created: admin / admin123")
