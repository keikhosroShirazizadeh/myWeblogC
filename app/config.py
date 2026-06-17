import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-do-not-use-in-production')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/myweblogc')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    WTF_CSRF_ENABLED = True
    LANGUAGES = ['en', 'fa']
    DEFAULT_LANGUAGE = 'en'
