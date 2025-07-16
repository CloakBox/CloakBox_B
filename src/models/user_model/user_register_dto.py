from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional
import re

class UserRegisterDTO(BaseModel):

    name: str = Field(..., min_length=1, max_length=255, description="사용자 이름")
    nickname: Optional[str] = Field(..., min_length=1, max_length=255, description="사용자 닉네임")
    email: str = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=1, description="비밀번호")
    confirm_password: str = Field(..., min_length=1, description="비밀번호 확인")
    
    class Config:
        strict = True
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError('올바른 이메일 형식이 아닙니다.')
        return value.lower()
    
    # @field_validator('password')
    # @classmethod
    # def validate_password(cls, value: str) -> str:
    #     # 비밀번호 복잡도 검증
    #     if len(value) < 8:
    #         raise ValueError('비밀번호는 최소 8자 이상이어야 합니다.')
        
    #     if not re.search(r'[A-Z]', value):
    #         raise ValueError('비밀번호는 최소 하나의 대문자를 포함해야 합니다.')
        
    #     if not re.search(r'[a-z]', value):
    #         raise ValueError('비밀번호는 최소 하나의 소문자를 포함해야 합니다.')
        
    #     if not re.search(r'\d', value):
    #         raise ValueError('비밀번호는 최소 하나의 숫자를 포함해야 합니다.')
        
    #     if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
    #         raise ValueError('비밀번호는 최소 하나의 특수문자를 포함해야 합니다.')
        
    #     return value
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, value: str, info: Any) -> str:
        data = info.data
        if 'password' in data and value != data['password']:
            raise ValueError('비밀번호가 일치하지 않습니다.')
        return value