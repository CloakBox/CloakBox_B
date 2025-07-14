# 서드파티 라이브러리 임포트
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 로컬 모듈 임포트
from utils.tunnel_manager import tunnel_manager
from utils.loging_manager import *

# Flask 확장들
db = SQLAlchemy()
migrate = Migrate()

def init_extensions(app):
    """어플리케이션에 확장들을 초기화"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 로깅 설정 추가
    setup_logging(app)