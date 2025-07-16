CREATE TABLE user_login_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    event_type VARCHAR(20) DEFAULT 'LOGIN',
    event_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_at_unix BIGINT NOT NULL DEFAULT EXTRACT(epoch FROM CURRENT_TIMESTAMP),
    ip_id BIGINT NOT NULL,
    user_agent_id BIGINT NOT NULL
);

COMMENT ON COLUMN user_login_log.user_id IS '사용자 ID';
COMMENT ON COLUMN user_login_log.event_type IS '이벤트 타입';
COMMENT ON COLUMN user_login_log.event_at IS '이벤트 일시';
COMMENT ON COLUMN user_login_log.event_at_unix IS '이벤트 일시 UNIX timestamp (ms)';
COMMENT ON COLUMN user_login_log.ip_id IS 'IP ID';
COMMENT ON COLUMN user_login_log.user_agent_id IS '사용자 에이전트 ID';

COMMENT ON TABLE user_login_log IS '사용자 로그인 로그 테이블';
COMMENT ON COLUMN user_login_log.id IS '사용자 로그인 로그 ID';

CREATE TABLE user_ip (
    id BIGSERIAL PRIMARY KEY,
    ip_str VARCHAR(255) NOT NULL
);

COMMENT ON TABLE user_ip IS '사용자 IP 테이블';
COMMENT ON COLUMN user_ip.id IS '사용자 IP ID';
COMMENT ON COLUMN user_ip.ip_str IS '사용자 IP 주소';

CREATE TABLE user_agent (
    id BIGSERIAL PRIMARY KEY,
    user_agent_str VARCHAR(255) NOT NULL
);

COMMENT ON TABLE user_agent IS '사용자 에이전트 테이블';
COMMENT ON COLUMN user_agent.id IS '사용자 에이전트 ID';
COMMENT ON COLUMN user_agent.user_agent_str IS '사용자 에이전트 문자열';

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role_id BIGINT NULL,
    nickname VARCHAR(50) NULL,
    bio TEXT NULL,
    phone VARCHAR(20) NULL,
    birth DATE NULL,
    gender VARCHAR(10) NULL,
    login_type VARCHAR(20) NULL,
    login_yn BOOLEAN NULL DEFAULT true,
    created_at_unix BIGINT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    user_ip_id BIGINT NULL,
    user_agent_id BIGINT NULL,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    user_image_id BIGINT NULL
);

-- 컬럼 코멘트 추가
COMMENT ON TABLE users IS '사용자 정보 테이블';
COMMENT ON COLUMN users.id IS '사용자ID';
COMMENT ON COLUMN users.name IS '사용자명';
COMMENT ON COLUMN users.email IS '이메일';
COMMENT ON COLUMN users.password IS '비밀번호';
COMMENT ON COLUMN users.role_id IS '권한';
COMMENT ON COLUMN users.nickname IS '닉네임';
COMMENT ON COLUMN users.bio IS '자기소개';
COMMENT ON COLUMN users.phone IS '전화번호';
COMMENT ON COLUMN users.birth IS '생년월일';
COMMENT ON COLUMN users.gender IS '성별';
COMMENT ON COLUMN users.login_type IS '로그인 구분';
COMMENT ON COLUMN users.login_yn IS '로그인가능여부';
COMMENT ON COLUMN users.created_at_unix IS '생성일자 UNIX timestamp (ms)';
COMMENT ON COLUMN users.created_at IS '생성일자';
COMMENT ON COLUMN users.user_ip_id IS '로그인 IP';
COMMENT ON COLUMN users.user_agent_id IS '로그인 에이전트';
COMMENT ON COLUMN users.updated_at IS '업데이트 일자';
COMMENT ON COLUMN users.user_image_id IS '사용자 이미지 ID';


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
