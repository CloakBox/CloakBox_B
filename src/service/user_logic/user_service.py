import bcrypt
from models.user_model.user import User
from extensions import jwt_manager, app_logger
from models.user_model.user_profile_update_dto import UserProfileUpdateDTO
from extensions import db

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
        app_logger.error(f"비밀번호 검증 중 오류: {e}")
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

def create_user_token(user: User) -> dict[str, str]:
    """
    사용자 토큰을 생성합니다.
    """
    try:
        payload = {
            'nickname': user.nickname,
            'email': user.email
        }
        access_token = jwt_manager.create_access_token(payload)
        refresh_token = jwt_manager.create_refresh_token(payload)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    except Exception as e:
        raise Exception(f"사용자 토큰 생성 중 오류가 발생했습니다: {e}")

def get_user_profile_by_user_info(user_info: dict) -> dict:
    """
    토큰을 사용하여 사용자 프로필을 조회합니다.
    """
    try:
        user_email = user_info.get('user_email') or user_info.get('email')
        
        if not user_email:
            raise Exception("토큰에서 이메일 정보를 찾을 수 없습니다.")
        
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            raise Exception("사용자를 찾을 수 없습니다.")
        
        return user.to_dict()
    
    except Exception as e:
        raise Exception(f"사용자 프로필 조회 중 오류가 발생했습니다: {e}")

def update_user_profile_by_user_info(user_info: dict, user_profile_update_data: UserProfileUpdateDTO) -> dict:
    """
    사용자 프로필을 수정합니다.
    """
    try:
        user_email = user_info.get('user_email') or user_info.get('email')
        
        if not user_email:
            raise Exception("토큰에서 이메일 정보를 찾을 수 없습니다.")
        
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            raise Exception("사용자를 찾을 수 없습니다.")
        
        user.nickname = user_profile_update_data.nickname
        user.bio = user_profile_update_data.bio
        
        db.session.commit()
        
        return user.to_dict()
    
    except Exception as e:
        raise Exception(f"사용자 프로필 수정 중 오류가 발생했습니다: {e}")