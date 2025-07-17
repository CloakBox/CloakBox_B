import random
import string
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import desc
from models.certification_model.certification import UserCertification
from utils.email_manager import EmailManager
from extensions import db, app_logger
import settings

def generate_certification_code(length: int = 6) -> str:
    """ 인증번호 생성 """
    return ''.join(random.choices(string.digits, k=length))

def create_certification_code(email: str, user_uuid: Optional[str] = None) -> UserCertification:
    """ 인증번호 생성 및 저장 """
    try:
        # 재생성 제한 확인
        if not can_create_new_code(email):
            raise Exception("1분 이내에 재생성할 수 없습니다.")
        
        # 기존 미사용 코드들을 사용 처리
        existing_codes = UserCertification.query.filter_by(
            recipient=email.lower(),
            use_yn=False
        ).all()

        for code in existing_codes:
            code.mark_as_used()
        
        # 새로운 인증번호 생성
        code_length = getattr(settings, 'CERTIFICATION_CODE_LENGTH', 6)
        certification_code = generate_certification_code(code_length)

        # 인증번호 저장
        new_certification = UserCertification(
            recipient=email.lower(),
            code=certification_code,
            user_uuid=user_uuid
        )
        db.session.add(new_certification)
        db.session.commit()

        return new_certification
    except Exception as e:
        app_logger.error(f"인증번호 생성 중 데이터베이스 오류: {str(e)}")
        db.session.rollback()
        raise e

def send_certification_email(email: str, code: str) -> bool:
    """ 인증번호 이메일 전송 """
    email_manager = EmailManager()

    subject = '[CloakBox] 이메일 인증번호'
    body = f"""
안녕하세요!

CloakBox 이메일 인증번호를 안내드립니다.

인증번호: {code}

이 인증번호는 5분 후에 만료됩니다.
타인에게 인증번호를 알려주지 마세요.

감사합니다.
CloakBox 팀.
"""
    try:
        email_manager.send_email(email, subject, body)
        return True
    except Exception as e:
        app_logger.error(f"이메일 전송 실패: {str(e)}")
        return False

def verify_certification_code(email: str, code: str) -> Optional[UserCertification]:
    """ 인증번호 검증 """
    certification_code = UserCertification.query.filter_by(
        recipient=email.lower(),
        code=code,
        use_yn=False
    ).order_by(desc(UserCertification.created_at)).first()

    if not certification_code or not certification_code.is_valid():
        return None
    
    certification_code.mark_as_used()
    db.session.commit()
    
    return certification_code

def cleanup_expired_codes():
    """ 만료된 인증번호 정리 """
    current_time_unix = int(datetime.now().timestamp())
    expired_codes = UserCertification.query.filter(
        UserCertification.expires_at_unix < current_time_unix
    ).all()

    for code in expired_codes:
        db.session.delete(code)
    
    db.session.commit()

def can_create_new_code(email: str) -> bool:
    """ 새로운 인증번호 생성 가능 여부 확인 """
    one_minute_ago = datetime.now() - timedelta(minutes=1)
    
    recent_code = UserCertification.query.filter(
        UserCertification.recipient == email.lower(),
        UserCertification.use_yn == False,
        UserCertification.created_at >= one_minute_ago
    ).first()
    
    return recent_code is None


