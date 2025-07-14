import random
import string
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import desc
from models.certification_model.certification import UserCertification
from utils.email_manager import EmailManager
from extensions import db
import settings

def generate_certification_code(length: int = 6) -> str:
    """ 인증번호 생성 """
    return ''.join(random.choices(string.digits, k=length))

def create_certification_code(email: str, user_uuid: Optional[str] = None) -> UserCertification:
    """ 인증번호 생성 및 저장 """
    existing_codes = UserCertification.query.filter_by(
        recipient=email.lower(),
        use_yn=False
    ).all()

    for code in existing_codes:
        db.session.delete(code)
    
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
CloakBox 팀
"""
    try:
        email_manager.send_email(email, subject, body)
        return True
    except Exception as e:
        print(f"이메일 전송 실패: {str(e)}")
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
    
    # 인증 성공 시 삭제
    db.session.delete(certification_code)
    db.session.commit()
    
    return certification_code

def cleanup_expired_codes():
    """ 만료된 인증번호 정리 """
    current_time_unix = int(datetime.now(timezone.utc).timestamp())
    expired_codes = UserCertification.query.filter(
        UserCertification.expires_at_unix < current_time_unix
    ).all()

    for code in expired_codes:
        db.session.delete(code)
    
    db.session.commit()