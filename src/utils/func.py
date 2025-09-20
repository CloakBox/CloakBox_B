
# 공통 유틸리티 함수
def create_error_response(message, error_code, status_code):
    """에러 응답 생성"""
    return {
        "status": "error",
        "message": message,
        "error": error_code
    }, status_code

def validate_request_json():
    from flask import request
    """요청 JSON 데이터 검증"""
    if not request.json:
        return False, create_error_response("요청 데이터가 없습니다.", "REQUEST_DATA_MISSING", 400)
    return True, None

def validate_required_fields(data, required_fields):
    """필수 필드 검증"""
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return False, create_error_response(
            f"필수 필드가 없습니다: {', '.join(missing_fields)}",
            "REQUIRED_FIELDS_MISSING",
            400
        )
    return True, None

def handle_database_operation(func, *args, **kwargs):
    from sqlalchemy.exc import SQLAlchemyError
    from extensions import db, app_logger
    """DB 작업 예외 처리"""
    try:
        return func(*args, **kwargs)
    except SQLAlchemyError as e:
        db.session.rollback()
        app_logger.error(f"데이터베이스 오류: {str(e)}")
        raise e

def create_user_login_log(user_id, user_ip_id, user_agent_id):
    from models.user_model.user_login_log import UserLoginLog
    from extensions import db
    from datetime import datetime
    import time
    """사용자 로그인 로그 생성 또는 업데이트"""
    existing_log = UserLoginLog.query.filter_by(user_id=user_id).first()
    
    if existing_log:
        existing_log.event_at = datetime.now()
        existing_log.event_at_unix = int(time.time())
        existing_log.ip_id = user_ip_id
        existing_log.user_agent_id = user_agent_id
    else:
        user_login_log = UserLoginLog(
            user_id=user_id,
            ip_id=user_ip_id,
            user_agent_id=user_agent_id
        )
        db.session.add(user_login_log)

def get_user_ip(request, db):
    
    from models.user_model.user_ip import UserIp
    
    # 사용자 IP와 User-Agent 정보 추출
    user_ip_str = request.remote_addr

    # IP 정보 저장 또는 조회
    user_ip_record = UserIp.query.filter_by(ip_str=user_ip_str).first()
    if not user_ip_record:
        user_ip_record = UserIp(ip_str=user_ip_str)
        db.session.add(user_ip_record)
        db.session.flush()
    
    return user_ip_record.id

def get_user_agent(request, db):
    
    from models.user_model.user_agent import UserAgent
    
    user_agent_str = request.headers.get('User-Agent', '')
    
    # User-Agent 정보 저장 또는 조회
    user_agent_record = UserAgent.query.filter_by(user_agent_str=user_agent_str).first()
    if not user_agent_record:
        user_agent_record = UserAgent(user_agent_str=user_agent_str)
        db.session.add(user_agent_record)
        db.session.flush()
    
    return user_agent_record.id