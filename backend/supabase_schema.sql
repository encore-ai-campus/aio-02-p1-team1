-- =========================================================
-- 초기화용 SQL (조장 기준 테이블)
-- 기존 테이블 삭제 후 전체 재생성
-- 주의: 기존 데이터는 전부 삭제됨
-- PRD 17.4~17.10 확장 컬럼·로그 테이블은
-- supabase_schema_prd_extend.sql 을 이어서 실행한다.
-- =========================================================

create extension if not exists "pgcrypto";


-- =========================================================
-- 0. 기존 테이블 삭제
-- FK 관계 때문에 자식 테이블부터 삭제
-- =========================================================

drop table if exists feedback cascade;
drop table if exists dashboard_search_stats cascade;
drop table if exists dashboard_data_quality cascade;

drop table if exists restaurant_tag_map cascade;
drop table if exists restaurant_tags cascade;
drop table if exists tag_categories cascade;

drop table if exists menus cascade;
drop table if exists restaurants cascade;
drop table if exists restaurant_categories cascade;

drop table if exists messages cascade;
drop table if exists conversations cascade;
drop table if exists profiles cascade;


-- =========================================================
-- 1. 사용자 프로필
-- Supabase auth.users 와 1:1 연결
-- =========================================================

create table profiles (
    id uuid primary key
        references auth.users(id)
        on delete cascade,

    profile_login_id varchar(45)
        unique,

    profile_nickname varchar(45) not null
        unique,

    kakao_profile_id varchar(100)
        unique,

    profile_created_at timestamptz not null
        default current_timestamp,

    profile_updated_at timestamptz,

    profile_withdrawn_at timestamptz,

    profile_status char(1) not null
        default '1'
        check (profile_status in ('0', '1')),

    profile_type char(1) not null
        default '1'
        check (profile_type in ('0', '1'))
);


-- =========================================================
-- 2. 대화방
-- =========================================================

create table conversations (
    id uuid primary key
        default gen_random_uuid(),

    user_id uuid not null
        references profiles(id)
        on delete cascade,

    title varchar(100),

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now()
);


-- =========================================================
-- 3. 메시지
-- =========================================================

create table messages (
    id uuid primary key
        default gen_random_uuid(),

    conversation_id uuid not null
        references conversations(id)
        on delete cascade,

    role varchar(20) not null
        check (role in ('user', 'assistant', 'system')),

    content text not null,

    created_at timestamptz not null
        default now()
);


-- =========================================================
-- 4. 음식점 카테고리
-- =========================================================

create table restaurant_categories (
    id uuid primary key
        default gen_random_uuid(),

    name varchar(30) not null
        unique
);


-- =========================================================
-- 5. 음식점
-- =========================================================

create table restaurants (
    id uuid primary key
        default gen_random_uuid(),

    category_id uuid
        references restaurant_categories(id)
        on delete set null,

    name varchar(100) not null,

    address varchar(255),

    phone varchar(30),

    description varchar(500),

    storage_path varchar(500) not null,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now()
);


-- =========================================================
-- 6. 메뉴
-- =========================================================

create table menus (
    id uuid primary key
        default gen_random_uuid(),

    restaurant_id uuid not null
        references restaurants(id)
        on delete cascade,

    name varchar(100) not null,

    price integer not null
        check (price >= 0),

    created_at timestamptz not null
        default now()
);


-- =========================================================
-- 7. 태그 카테고리
-- 예: 가격대 / 분위기 / 이용목적 / 맛
-- =========================================================

create table tag_categories (
    id uuid primary key
        default gen_random_uuid(),

    code varchar(30) not null
        unique,

    name varchar(30) not null
        unique
);


-- =========================================================
-- 8. 음식점 태그
-- =========================================================

create table restaurant_tags (
    id uuid primary key
        default gen_random_uuid(),

    category_id uuid not null
        references tag_categories(id)
        on delete cascade,

    name varchar(50) not null,

    unique (category_id, name)
);


-- =========================================================
-- 9. 음식점 - 태그 매핑
-- N:M 관계
-- =========================================================

create table restaurant_tag_map (
    restaurant_id uuid not null
        references restaurants(id)
        on delete cascade,

    tag_id uuid not null
        references restaurant_tags(id)
        on delete cascade,

    primary key (restaurant_id, tag_id)
);


-- =========================================================
-- 10. 추천 피드백
-- 1: 싫어요
-- 2: 중간
-- 3: 좋아요
-- =========================================================

create table feedback (
    feedback_id uuid primary key
        default gen_random_uuid(),

    profile_id uuid not null
        references profiles(id)
        on delete cascade,

    conversation_id uuid not null
        references conversations(id)
        on delete cascade,

    restaurant_id uuid not null
        references restaurants(id)
        on delete cascade,

    feedback_value char(1) not null
        check (feedback_value in ('1', '2', '3')),

    created_at timestamptz not null
        default current_timestamp,

    updated_at timestamptz
);


-- =========================================================
-- 11. 관리자 대시보드 검색 통계
-- stat_type
-- 0: 음식 카테고리
-- 1: 가격대
-- 2: 상황 태그
-- =========================================================

create table dashboard_search_stats (
    stat_id uuid primary key
        default gen_random_uuid(),

    stat_date date not null,

    stat_type char(1) not null
        check (stat_type in ('0', '1', '2')),

    stat_key varchar(45) not null,

    count integer not null
        default 0
        check (count >= 0),

    created_at timestamptz not null
        default current_timestamp
);


-- =========================================================
-- 12. 관리자 대시보드 데이터 품질
-- =========================================================

create table dashboard_data_quality (
    stat_id uuid primary key
        default gen_random_uuid(),

    checked_at timestamptz not null
        default current_timestamp,

    total_restaurant integer not null
        default 0
        check (total_restaurant >= 0),

    complete_count integer not null
        default 0
        check (complete_count >= 0)
);


-- =========================================================
-- 13. 인덱스
-- =========================================================

create index idx_conversations_user_id
    on conversations(user_id);

create index idx_messages_conversation_id
    on messages(conversation_id);

create index idx_restaurants_category_id
    on restaurants(category_id);

create index idx_menus_restaurant_id
    on menus(restaurant_id);

create index idx_restaurant_tags_category_id
    on restaurant_tags(category_id);

create index idx_restaurant_tag_map_restaurant_id
    on restaurant_tag_map(restaurant_id);

create index idx_restaurant_tag_map_tag_id
    on restaurant_tag_map(tag_id);

create index idx_feedback_profile_id
    on feedback(profile_id);

create index idx_feedback_conversation_id
    on feedback(conversation_id);

create index idx_feedback_restaurant_id
    on feedback(restaurant_id);

create index idx_feedback_created_at
    on feedback(created_at);

create index idx_dashboard_search_stats_date
    on dashboard_search_stats(stat_date);

create index idx_dashboard_search_stats_type
    on dashboard_search_stats(stat_type);

create index idx_dashboard_search_stats_date_type
    on dashboard_search_stats(stat_date, stat_type);
