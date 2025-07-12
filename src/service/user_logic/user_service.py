import bcrypt
from typing import Optional

def hash_password(password: str) -> str:
    """
    비밀번호를 bcrypt로 암호화합니다.
    """
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        raise Exception(f"비밀번호 암호화 중 오류가 발생했습니다: {e}")

def check_password_hash(password: str, hashed_password: str) -> bool:
    """
    입력된 비밀번호와 해시된 비밀번호를 비교합니다.
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"비밀번호 검증 중 오류: {e}")
        return False

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    비밀번호 강도를 검증합니다.
    """
    import re
    
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다."
    
    if not re.search(r'[A-Z]', password):
        return False, "비밀번호는 최소 하나의 대문자를 포함해야 합니다."
    
    if not re.search(r'[a-z]', password):
        return False, "비밀번호는 최소 하나의 소문자를 포함해야 합니다."
    
    if not re.search(r'\d', password):
        return False, "비밀번호는 최소 하나의 숫자를 포함해야 합니다."
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "비밀번호는 최소 하나의 특수문자를 포함해야 합니다."
    
    return True, "비밀번호가 유효합니다."