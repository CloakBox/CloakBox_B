# 서드파티 라이브러리 임포트
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

# 로컬 모듈 임포트
from utils.tunnel_manager import tunnel_manager
from utils.loging_manager import *
from utils.transacation_manager import TransactionManager
from utils.email_manager import EmailManager
from utils.jwt_manager import jwt_manager
from utils.auth_decorator import require_auth, require_permission, require_admin

# Flask 확장들
db = SQLAlchemy()
migrate = Migrate()

app_logger = None
api_logger = None
error_logger = None
database_logger = None
transaction_manager = None
email_manager = None

def init_extensions(app):
    """어플리케이션에 확장들을 초기화"""
    global app_logger, api_logger, error_logger, database_logger
    global transaction_manager, email_manager
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 로깅 설정 추가
    setup_logging(app)
    
    # 로거들 초기화
    try:
        app_logger = get_app_logger()
        api_logger = get_api_logger()
        error_logger = get_error_logger()
        database_logger = get_database_logger()
        
        # 로거가 None인 경우 기본 로거 생성
        if app_logger is None:
            app_logger = logging.getLogger('cloakbox_app')
            app_logger.setLevel(logging.INFO)
            if not app_logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
                handler.setFormatter(formatter)
                app_logger.addHandler(handler)
        
        if api_logger is None:
            api_logger = logging.getLogger('cloakbox_api')
            api_logger.setLevel(logging.INFO)
            if not api_logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
                handler.setFormatter(formatter)
                api_logger.addHandler(handler)
        
        if error_logger is None:
            error_logger = logging.getLogger('cloakbox_error')
            error_logger.setLevel(logging.ERROR)
            if not error_logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
                handler.setFormatter(formatter)
                error_logger.addHandler(handler)
        
        if database_logger is None:
            database_logger = logging.getLogger('cloakbox_database')
            database_logger.setLevel(logging.INFO)
            if not database_logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
                handler.setFormatter(formatter)
                database_logger.addHandler(handler)
            
    except Exception as e:
        # 로거 초기화 실패 시 기본 로거 사용
        app_logger = logging.getLogger('cloakbox_app')
        api_logger = logging.getLogger('cloakbox_api')
        error_logger = logging.getLogger('cloakbox_error')
        database_logger = logging.getLogger('cloakbox_database')
        
        for logger in [app_logger, api_logger, error_logger, database_logger]:
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
    
    # 매니저들 초기화
    transaction_manager = TransactionManager(db.session, app_logger)
    email_manager = EmailManager()