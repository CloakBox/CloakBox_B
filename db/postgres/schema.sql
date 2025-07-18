-- 사용자 정보 테이블
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role_id BIGINT NULL,
    nickname VARCHAR(50) NULL,
    bio TEXT NULL,
    birth DATE NULL,
    gender VARCHAR(10) NULL,
    login_type VARCHAR(20) NULL,
    login_yn BOOLEAN NULL DEFAULT true,
    created_at_unix BIGINT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    user_ip_id BIGINT NULL,
    user_agent_id BIGINT NULL,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    user_image_id BIGINT NULL,
    user_setting_id BIGINT NULL
);

-- 사용자 로그인 로그 테이블
CREATE TABLE user_login_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    event_type VARCHAR(20) DEFAULT 'LOGIN',
    event_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_at_unix BIGINT NOT NULL DEFAULT EXTRACT(epoch FROM CURRENT_TIMESTAMP),
    ip_id BIGINT NOT NULL,
    user_agent_id BIGINT NOT NULL
);

-- 사용자 IP 테이블
CREATE TABLE user_ip (
    id BIGSERIAL PRIMARY KEY,
    ip_str VARCHAR(255) NOT NULL
);

-- 사용자 에이전트 테이블
CREATE TABLE user_agent (
    id BIGSERIAL PRIMARY KEY,
    user_agent_str VARCHAR(255) NOT NULL
);

-- 사용자 인증 테이블
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

-- 사용자 이미지 테이블
CREATE TABLE user_image (
	id BIGSERIAL PRIMARY KEY,
	uuid UUID NOT NULL,
	size BIGINT	NULL,
	path VARCHAR(255) NULL,
	name VARCHAR(255) NULL,
	extension VARCHAR(50) NULL
);

-- 사용자 설정 테이블
CREATE TABLE user_setting (
	id BIGSERIAL PRIMARY KEY,
	dark_mode VARCHAR(1) NULL DEFAULT 'N',
	editor_mode	VARCHAR(50) NULL,
	lang_cd	VARCHAR(255) NULL DEFAULT 'ko'
);

-- 사용자 이벤트 로그 테이블
CREATE TABLE user_event_log (
	id	BIGSERIAL PRIMARY KEY,
	user_uuid UUID NOT NULL,
	event_type VARCHAR(255)	NOT NULL,
	event_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	event_at_unix BIGINT NULL
);