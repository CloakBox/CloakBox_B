from functools import wraps
from flask import g
from typing import Callable, Any

def get_transaction_logger():
    """트랜잭션 전용 로거 생성"""
    try:
        from extensions import app_logger
        return app_logger
    except ImportError:
        import logging
        logger = logging.getLogger('transaction')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s: %(module)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

def transaction_managed(func: Callable) -> Callable:
    """트랜잭션을 관리하는 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger = get_transaction_logger()
        try:
            # 트랜잭션 시작
            result = func(*args, **kwargs)
            
            # 성공 시 커밋 (db는 외부에서 주입받음)
            logger.info(f"트랜잭션 커밋 성공: {func.__name__}")
            
            return result
            
        except Exception as e:
            # 실패 시 롤백 (db는 외부에서 주입받음)
            logger.error(f"트랜잭션 롤백: {func.__name__} - {str(e)}")
            raise e
    
    return wrapper

def safe_commit(db_session):
    """안전한 커밋 수행"""
    logger = get_transaction_logger()
    try:
        db_session.commit()
        logger.info("커밋 성공")
        return True
    except Exception as e:
        db_session.rollback()
        logger.error(f"커밋 실패: {str(e)}")
        return False

def safe_rollback(db_session):
    """안전한 롤백 수행"""
    logger = get_transaction_logger()
    try:
        db_session.rollback()
        logger.info("롤백 수행")
        return True
    except Exception as e:
        logger.error(f"롤백 실패: {str(e)}")
        return False

class TransactionManager:
    """트랜잭션 매니저 클래스"""
    
    def __init__(self, db_session, logger=None):
        self.db_session = db_session
        self._logger = logger
        self._logger_initialized = logger is not None
    
    @property
    def logger(self):
        """로거 lazy loading"""
        if not self._logger_initialized:
            try:
                from extensions import app_logger
                self._logger = app_logger
            except ImportError:
                self._logger = get_transaction_logger()
            self._logger_initialized = True
        return self._logger
    
    def commit(self):
        """커밋 수행"""
        return safe_commit(self.db_session)
    
    def rollback(self):
        """롤백 수행"""
        return safe_rollback(self.db_session)
    
    def managed_transaction(self, func: Callable) -> Callable:
        """트랜잭션 관리 데코레이터"""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                self.commit()
                self.logger.info(f"트랜잭션 커밋 성공: {func.__name__}")
                return result
            except Exception as e:
                self.rollback()
                self.logger.error(f"트랜잭션 롤백: {func.__name__} - {str(e)}")
                raise e
        return wrapper