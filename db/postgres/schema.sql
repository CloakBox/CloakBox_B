CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_certification (
	id BIGSERIAL PRIMARY KEY,
	user_uuid UUID NULL,
	code varchar(10) NOT NULL,
	recipient varchar(255) NOT NULL,
	use_yn bool DEFAULT false NULL,
	created_at timestamptz DEFAULT now() NULL,
	created_at_unix int8 DEFAULT EXTRACT(epoch FROM now()) NULL,
	expires_at timestamptz NOT NULL,
    expires_at_unix int8 DEFAULT EXTRACT(epoch FROM now()) NULL
);

-- updated_at 컬럼을 자동으로 업데이트하기 위한 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- users 테이블에 트리거 생성
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
