from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    import os
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'erlau-secret-key-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erlau.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Lütfen giriş yapın.'

    from app.routes import auth, main, satin_alma, admin
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(satin_alma)
    app.register_blueprint(admin)

    with app.app_context():
        db.create_all()
        from app.models import User, Department
        from app.utils import create_default_data
        create_default_data()

    return app
