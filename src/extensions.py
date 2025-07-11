from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_extensions(app):
    """어플리케이션에 확장들을 초기화"""
    db.init_app(app)
    migrate.init_app(app, db)