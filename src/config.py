import os
from urllib.parse import quote_plus
import settings

class Config:
    """기본 설정 클래스"""
    
    # 데이터베이스 연결 문자열 생성
    @staticmethod
    def get_database_url():
        if settings.DB_TYPE == "POSTGRESQL":
            password = quote_plus(settings.DB_PASS)
            return f"postgresql://{settings.DB_USER}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        elif settings.DB_TYPE == "MARIADB":
            password = quote_plus(settings.DB_PASS)
            return f"mysql+pymysql://{settings.DB_USER}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        else:
            raise ValueError(f"지원하지 않는 데이터베이스 유형: {settings.DB_TYPE}")
    
    SQLALCHEMY_DATABASE_URI = get_database_url.__func__()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': settings.DB_RECONN_TIMEOUT
        }
    }
    
class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    TESTING = settings.DEBUG_MODE > 0
    
class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig if not settings.PRODUCTION_MODE else ProductionConfig
}