from pydantic import BaseModel, Field
from typing import Optional

class UserProfileUpdateDTO(BaseModel):

    nickname: Optional[str] = Field(None, min_length=1, max_length=255, description="사용자 닉네임")
    gender: Optional[str] = Field(None, description="성별")
    bio: Optional[str] = Field(None, description="자기소개")
    
    class Config:
        strict = True