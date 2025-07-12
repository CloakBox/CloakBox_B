import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional, Dict, Any
from flask import Flask, request, g
import json
import settings

class LoggingManager:

    """로깅 매니저"""
    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self.log_dir = getattr(settings, 'LOG_DIR', 'logs')
        self.log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
        self.max_log_size = getattr(settings, 'MAX_LOG_SIZE', 10 * 1024 * 1024)
        self.backup_count = getattr(settings, 'LOG_BACKUP_COUNT', 5)
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """로그 디렉토리 생성"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _get_log_format(self, log_type: str = 'default') -> str:
        """로그 형식 반환"""
        formats = {
            'default': '[%(asctime)s] %(levelname)s: %(module)s %(message)s',
            'detailed': '[%(asctime)s] %(levelname)s: %(pathname)s:%(lineno)d %(funcName)s() - %(message)s',
            'api': '[%(asctime)s] %(levelname)s: %(module)s - %(message)s',
            'error': '[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s'
        }
        return formats.get(log_type, formats['default'])
    
    def create_logger(self, name: str, log_file: Optional[str] = None, 
                    log_format: str = 'default', console_output: bool = True) -> logging.Logger:
        """로거 생성"""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.log_level.upper()))

        # 기존 핸들러 제거 (중복제거)
        logger.handlers.clear()

        # 파일 핸들러 설정
        if log_file:
            file_path = os.path.join(self.log_dir, log_file)
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=self.max_log_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(
                self._get_log_format(log_format),
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # 콘솔 핸들러 설정
        if console_output:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                self._get_log_format(log_format),
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        self.loggers[name] = logger
        return logger
    

    def get_logger(self, name: str) -> Optional[logging.Logger]:
        """기존 로거 반환"""
        return self.loggers.get(name)
    
    def setup_app_logger(self, app: Flask) -> None:
        """Flask 앱 로거 설정"""
        app_logger = self.create_logger(
            'cloakbox_app',
            'app.log',
            'detailed',
            console_output=True
        )

        app.logger.handlers.clear()
        for handler in app_logger.handlers:
            app.logger.addHandler(handler)
        
        app.logger.setLevel(getattr(logging, self.log_level.upper()))

    def setup_api_logger(self) -> logging.Logger:
        """API 요청 로깅 설정"""
        return self.create_logger(
            'cloakbox_api',
            'api.log',
            'api',
            console_output=True
        )

    def setup_error_logger(self) -> logging.Logger:
        """에러 로깅 설정"""
        return self.create_logger(
            'cloakbox_error',
            'error.log',
            'error',
            console_output=True
        )
    
    def setup_db_logger(self) -> logging.Logger:
        """데이터베이스 로깅 설정"""
        return self.create_logger(
            'cloakbox_database',
            'database.log',
            'detailed',
            console_output=True
        )
    
    def log_request(self, logger: logging.Logger, status_code: int,
                    response_time: float, additional_info: Optional[Dict[str, Any]] = None) -> None:
        """API 요청 로깅"""
        try:
            log_data: Dict[str, Any] = {
                'method': request.method,
                'url': request.url,
                'status_code': status_code,
                'response_time': round(response_time, 2),
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'timestamp': datetime.now().isoformat()
            }

            if additional_info:
                log_data.update(additional_info)

            if status_code >= 400:
                logger.error(f"API 요청 오류: {json.dumps(log_data, ensure_ascii=False)}")
            else:
                logger.info(f"API 요청: {json.dumps(log_data, ensure_ascii=False)}")
        except Exception as e:
            logger.error(f"로깅 오류: {str(e)}")
    
    def log_error(self, logger: logging.Logger, error: Exception, 
                 context: Optional[Dict[str, Any]] = None) -> None:
        """에러 로깅"""
        try:
            error_data: Dict[str, Any] = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': datetime.now().isoformat()
            }
            
            if context:
                error_data.update(context)
            
            if hasattr(request, 'method'):
                request_data: Dict[str, Any] = {
                    'method': request.method,
                    'url': request.url,
                    'ip': request.remote_addr
                }
                error_data.update(request_data)
            
            logger.error(f"에러 발생: {json.dumps(error_data, ensure_ascii=False)}", exc_info=True)
            
        except Exception as e:
            logger.critical(f"에러 로깅 중 치명적 오류 발생: {str(e)}")

logger_manager = LoggingManager()

def setup_logging(app: Flask) -> None:
    """Flask 앱에 로깅 설정"""
    logger_manager.setup_app_logger(app)

    # 요청 처리 시간 측정을 위한 미들웨어 설정
    @app.before_request
    def before_request():
        g.start_time = datetime.now()

    @app.after_request
    def after_request(response):
        # API 로깅
        if hasattr(g, 'start_time'):
            response_time = (datetime.now() - g.start_time).total_seconds() * 1000
            api_logger = logger_manager.get_logger('cloakbox_api')
            if not api_logger:
                api_logger = logger_manager.setup_api_logger()

            # 에러 응답의 경우 응답 본문도 로깅
            additional_info = {}
            if response.status_code >= 400:
                try:
                    # 응답 본문에서 에러 메시지 추출
                    response_data = response.get_json()
                    if response_data:
                        additional_info['error_message'] = response_data.get('message', '알 수 없는 오류')
                        additional_info['error_status'] = response_data.get('status', 'error')
                except Exception:
                    # JSON 파싱 실패 시 텍스트로 처리
                    additional_info['error_message'] = response.get_data(as_text=True)[:200]

            logger_manager.log_request(api_logger, response.status_code, response_time, additional_info)
        
        return response

    # 전역 에러 핸들러
    @app.errorhandler(Exception)
    def handle_exception(error):
        error_logger = logger_manager.get_logger('cloakbox_error')
        if not error_logger:
            error_logger = logger_manager.setup_error_logger()
        
        logger_manager.log_error(error_logger, error, {
            'endpoint': request.endpoint,
            'args': dict(request.args),
            'form': dict(request.form) if request.form else None
        })

        return {'error': '내부 서버 오류가 발생했습니다.'}, 500
    
def get_app_logger() -> logging.Logger:
    """앱 로거 반환"""
    logger = logger_manager.get_logger('cloakbox_app')
    if not logger:
        logger = logger_manager.create_logger('cloakbox_app', 'app.log', 'detailed')
    return logger

def get_api_logger() -> logging.Logger:
    """API 로거 반환"""
    logger = logger_manager.get_logger('cloakbox_api')
    if not logger:
        logger = logger_manager.create_logger('cloakbox_api', 'api.log', 'api')
    return logger

def get_error_logger() -> logging.Logger:
    """에러 로거 반환"""
    logger = logger_manager.get_logger('cloakbox_error')
    if not logger:
        logger = logger_manager.create_logger('cloakbox_error', 'error.log', 'error')
    return logger

def get_database_logger() -> logging.Logger:
    """데이터베이스 로거 반환"""
    logger = logger_manager.get_logger('cloakbox_database')
    if not logger:
        logger = logger_manager.create_logger('cloakbox_database', 'database.log', 'detailed')
    return logger

def log_info(message: str, logger_name: str = 'cloakbox_app') -> None:
    """정보 로깅"""
    logger = logger_manager.get_logger(logger_name)
    if logger:
        logger.info(message)

def log_error(message: str, logger_name: str = 'cloakbox_app') -> None:
    """에러 로깅"""
    logger = logger_manager.get_logger(logger_name)
    if logger:
        logger.error(message)

def log_warning(message: str, logger_name: str = 'cloakbox_app') -> None:
    """경고 로깅"""
    logger = logger_manager.get_logger(logger_name)
    if logger:
        logger.warning(message)

def log_debug(message: str, logger_name: str = 'cloakbox_app') -> None:
    """디버그 로깅"""
    logger = logger_manager.get_logger(logger_name)
    if logger:
        logger.debug(message)