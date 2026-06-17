import os
from flask import Flask, session
from .config import Config
from .extensions import mongo, login_manager, bcrypt


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'templates'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)

    mongo.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return User.find_by_id(user_id)

    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.public import public_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(public_bp)

    @app.context_processor
    def inject_globals():
        from .models.category import get_menu_categories
        lang = session.get('lang', 'en')
        return {
            'menu_categories': get_menu_categories(),
            'current_lang': lang,
            'is_rtl': lang == 'fa',
        }

    with app.app_context():
        from .models.user import init_admin
        init_admin()

    return app
