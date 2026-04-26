from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    import os
    
    # Güvenlik: Production'da SECRET_KEY kontrolü
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'erlau-dev-key-2026')
    
    # SQLite Performansı: "Database is locked" hatalarını önlemek için timeout eklendi
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erlau.db?timeout=30'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Lütfen giriş yapın.'

    from app.routes import auth, main, satin_alma, admin, muhasebe
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(satin_alma)
    app.register_blueprint(admin)
    app.register_blueprint(muhasebe)

    if not app.debug:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'erlau.log'),
            maxBytes=1_000_000, backupCount=5, encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s [%(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(logging.WARNING)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.WARNING)

    from flask import render_template

    @app.errorhandler(404)
    def sayfa_bulunamadi(e):
        return render_template('hata.html', kod=404, mesaj='Sayfa bulunamadı.', aciklama='Aradığınız sayfa mevcut değil veya taşınmış olabilir.'), 404

    @app.errorhandler(403)
    def erisim_engellendi(e):
        return render_template('hata.html', kod=403, mesaj='Erişim engellendi.', aciklama='Bu sayfayı görüntüleme yetkiniz bulunmuyor.'), 403

    @app.errorhandler(500)
    def sunucu_hatasi(e):
        return render_template('hata.html', kod=500, mesaj='Sunucu hatası.', aciklama='Beklenmedik bir hata oluştu. Tekrar deneyin veya yönetici ile iletişime geçin.'), 500

    with app.app_context():
        db.create_all()
        from app.models import User, Department
        from app.utils import create_default_data
        create_default_data()

    return app
