import os
from urllib.parse import quote_plus
import settings
from typing import Optional

class Config:
    """기본 설정 클래스"""
    
    @staticmethod
    def is_ci_environment():
        """CI 환경 여부 확인"""
        return any([
            os.getenv('CI'),
            os.getenv('GITHUB_ACTIONS'),
            os.getenv('GITLAB_CI'),
            os.getenv('TRAVIS'),
            os.getenv('CIRCLECI')
        ])

    @staticmethod
    def should_use_tunnel():
        """SSH 터널링 사용 여부 확인"""
        if Config.is_ci_environment():
            return False
        
        # 명시적으로 비활성화된 경우
        if hasattr(settings, 'SSH_TUNNEL_ENABLED') and not settings.SSH_TUNNEL_ENABLED:
            return False
        
        # 운영 환경에서는 터널링 비활성화 (서버에서 직접 실행)
        if hasattr(settings, 'PRODUCTION_MODE') and settings.PRODUCTION_MODE:
            return False
        
        # 기본적으로 터널링 사용
        return True

    # 데이터베이스 연결 문자열 생성
    @staticmethod
    def get_database_url():
        if settings.DB_TYPE == "POSTGRESQL":
            # 더 안전한 URL 인코딩 처리
            from urllib.parse import quote_plus
            user = quote_plus(settings.DB_USER)
            password = quote_plus(settings.DB_PASS)
            host = quote_plus(settings.DB_HOST)
            name = quote_plus(settings.DB_NAME)
            return f"postgresql://{user}:{password}@{host}:{settings.DB_PORT}/{name}"
        elif settings.DB_TYPE == "MARIADB":
            user = quote_plus(settings.DB_USER)
            password = quote_plus(settings.DB_PASS)
            host = quote_plus(settings.DB_HOST)
            name = quote_plus(settings.DB_NAME)
            return f"mysql+pymysql://{user}:{password}@{host}:{settings.DB_PORT}/{name}"
        else:
            raise ValueError(f"지원하지 않는 데이터베이스 유형: {settings.DB_TYPE}")
    
    # SSH 터널링이 활성화된 경우 동적으로 데이터베이스 URL 생성
    @staticmethod
    def get_database_url_with_tunnel(local_port: Optional[int] = None):
        """SSH 터널링을 사용하는 데이터베이스 URL 생성"""
        if local_port is not None:
            # SSH 터널링을 통해 로컬 포트로 연결
            if settings.DB_TYPE == "POSTGRESQL":
                password = quote_plus(settings.DB_PASS)
                return f"postgresql://{settings.DB_USER}:{password}@localhost:{local_port}/{settings.DB_NAME}"
            elif settings.DB_TYPE == "MARIADB":
                password = quote_plus(settings.DB_PASS)
                return f"mysql+pymysql://{settings.DB_USER}:{password}@localhost:{local_port}/{settings.DB_NAME}"
        
        # 기본 데이터베이스 URL 반환
        return Config.get_database_url()
    
    # 기본 데이터베이스 URL (SSH 터널링 비활성화 시)
    SQLALCHEMY_DATABASE_URI = get_database_url.__func__()
    SQLALCHEMY_BINDS = {
        'admin_cloakbox': get_database_url.__func__()
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': settings.DB_RECONN_TIMEOUT
        }
    }
    
    # SSH 터널링이 활성화된 경우 추가 설정
    if hasattr(settings, 'SSH_TUNNEL_ENABLED') and settings.SSH_TUNNEL_ENABLED:
        SQLALCHEMY_ENGINE_OPTIONS['connect_args']['connect_timeout'] = 10
        SQLALCHEMY_ENGINE_OPTIONS['pool_recycle'] = 180  # 터널링 환경에서는 더 짧은 재사용 시간

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

# SSH 터널링을 위한 동적 설정 함수
def update_database_config_with_tunnel(local_port: Optional[int]):
    """SSH 터널링을 사용하여 데이터베이스 설정 업데이트"""
    if local_port is None:
        raise ValueError("local_port가 None입니다.")
        
    tunnel_url = Config.get_database_url_with_tunnel(local_port)
    
    # 모든 설정 클래스의 데이터베이스 URL 업데이트
    for config_class in [DevelopmentConfig, ProductionConfig]:
        config_class.SQLALCHEMY_DATABASE_URI = tunnel_url
        config_class.SQLALCHEMY_BINDS = {
            'admin_cloakbox': tunnel_url
        }
        # 터널링 환경에 맞는 엔진 옵션 설정
        config_class.SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 180,  # 터널링 환경에서는 더 짧은 재사용 시간
            'connect_args': {
                'connect_timeout': 10
            }
        }
    
    print(f"데이터베이스 설정이 SSH 터널링으로 업데이트됨: {tunnel_url}")