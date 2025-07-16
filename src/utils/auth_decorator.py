from functools import wraps
from flask import request

def require_auth(f):
    """인증 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # lazy import로 무한참조 방지
        try:
            from extensions import jwt_manager, app_logger
        except ImportError:
            # extensions가 아직 초기화되지 않은 경우
            from .jwt_manager import jwt_manager
            import logging
            app_logger = logging.getLogger('auth_decorator')
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            app_logger.warning("인증 실패: 토큰 없음")
            return {
                'status': 'error',
                'message': '토큰이 없습니다.'
            }, 401
        
        # Bearer 토큰 형식 확인
        if not auth_header.startswith('Bearer '):
            app_logger.warning("인증 실패: 잘못된 토큰 형식")
            return {
                'status': 'error',
                'message': '유효하지 않은 토큰 형식입니다.'
            }, 401
        
        # 토큰 추출
        token = auth_header.split(' ')[1]

        # 토큰 검증
        payload = jwt_manager.verify_token(token)
        if not payload:
            app_logger.warning("인증 실패: 유효하지 않은 토큰")
            return {
                'status': 'error',
                'message': '유효하지 않은 토큰입니다.'
            }, 401
        
        # 토큰 타입 확인
        if payload.get('type') != 'access':
            app_logger.warning("인증 실패: 액세스 토큰이 아님")
            return {
                'status': 'error',
                'message': '액세스 토큰이 필요합니다.'
            }, 401
        
        app_logger.info(f"인증 성공: {payload.get('user_id', 'unknown')}")
        return f(*args, **kwargs)
    
    return decorated_function

def require_permission(required_permission: list = None):
    """권한 검증 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                from extensions import jwt_manager, app_logger, db
                from models.user_model.user import User
            except ImportError:
                from .jwt_manager import jwt_manager
                import logging
                app_logger = logging.getLogger('auth_decorator')
                return {
                    'status': 'error',
                    'message': '시스템 초기화 오류',
                }, 500
            
            # 토큰에서 사용자 ID 추출
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {
                    'status': 'error',
                    'message': '토큰이 필요합니다.',
                }, 401
            
            token = auth_header.split(' ')[1]
            payload = jwt_manager.verify_token(token)
            if not payload:
                return {
                    'status': 'error',
                    'message': '유효하지 않은 토큰입니다.',
                }, 401
            
            # 권한 검증
            user_id = payload.get('user_id')
            if not user_id:
                return {
                    'status': 'error',
                    'message': '사용자 정보를 찾을 수 없습니다.',
                }, 404
            
            # 사용자 조회
            try:
                user = User.query.filter_by(id=user_id).first()
                if not user:
                    app_logger.warning(f"권한 검증 실패: 사용자를 찾을 수 없음 - {user_id}")
                    return {
                        'status': 'error',
                        'message': '사용자를 찾을 수 없습니다.'
                    }, 404
                
                if not user.is_active:
                    app_logger.warning(f"권한 검증 실패: 비활성화된 사용자 - {user_id}")
                    return {
                        'status': 'error',
                        'message': '비활성화된 사용자입니다.'
                    }, 403
                
                # 권한 검증
                if required_permission and not user.has_permission(required_permission):
                    app_logger.warning(f"권한 검증 실패: 필요한 권한 없음 - {user_id} - {required_permission}")
                    return {
                        'status': 'error',
                        'message': '이 작업을 수행 할 권한이 없습니다.'
                    }, 403
                
                app_logger.info(f"권한 검증 성공: {user_id} - {required_permission}")
                return f(*args, **kwargs)
            
            except Exception as e:
                app_logger.error(f"권한 검증 중 오류: {str(e)}")
                return {
                    'status': 'error',
                    'message': '권한 검증 중 오류가 발생했습니다.'
                }, 500
            
        return decorated_function
    return decorator

def require_admin(f):
    return require_permission(['admin'])(f)
    # return require_permission(UserRole.ADMIN)(f)