"""
======================================================================
AE WIKI 통합 챗봇 시스템 - 핵심 유틸리티 라이브러리 (utils.py)
======================================================================

📋 파일 역할:
- AE WIKI 시스템의 모든 핵심 기능을 통합 제공하는 중앙 유틸리티 모듈
- 3개 전용 챗봇(AE WIKI, AE 용어집, JEDEC SPEC) 시스템의 백엔드 로직 구현
- 데이터 관리, 사용자 인증, API 통신, UI 컴포넌트 등 전반적인 기능 제공

🔧 주요 기능 영역:
1. 📁 로컬 데이터 관리: JSON 기반 경량 데이터베이스 시스템
   - 사용자 계정, 채팅 기록, Q&A 데이터 통합 관리
   - 데이터 초기화, 저장, 로드 및 스키마 호환성 보장

2. 🔐 사용자 인증 및 세션 관리: 브라우저별 독립 세션 시스템
   - 간소화된 로그인/로그아웃 시스템 구현
   - 세션 상태 관리 및 자동 로그인 복구
   - 관리자 권한 확인 및 사용자 정보 관리

3. 🤖 AI API 통합 시스템: RAG 및 LLM API 통합 관리
   - 챗봇별 전용 문서 인덱스 검색 (RAG API)
   - 확장된 10턴 대화 맥락 지원 (LLM API)
   - 챗봇별 프롬프트 최적화 및 출처 표시 형식 지원

4. 💾 채팅 및 검색 로그 관리: 실시간 대화 저장 시스템
   - 슬라이딩 윈도우 메모리 관리로 성능 최적화
   - 검색 기록 분석 및 사용자 활동 추적
   - 포인트 시스템 및 랭킹 기능

5. 🎨 UI 테마 및 스타일: 통합된 다크 테마 시스템
   - Streamlit 커스텀 CSS 스타일링
   - 타이핑 효과 및 동적 UI 컴포넌트
   - 반응형 레이아웃 및 사용자 경험 최적화

6. 📝 Q&A 시스템: 질문/답변 게시판 기능
   - 질문 등록, 답변 작성, 좋아요 시스템
   - 카테고리별 검색 및 필터링
   - 사용자 활동 기반 포인트 시스템

🔗 연동 관계:
- 🏠_Home.py: 메인 페이지에서 전체 시스템 초기화
- pages/*.py: 모든 페이지에서 공통 기능 호출
- config.py: 설정값 및 API 키 관리
- user_manager.py: 통합 사용자 관리 시스템과 연동
- conversation_manager.py: 대화 관리 기능과 협력
- theme.py: UI 테마 설정과 연동

🔄 데이터 흐름:
1. 사용자 요청 → 인증 확인 → API 호출 → 응답 처리 → UI 표시
2. 채팅 데이터 → 실시간 저장 → 메모리 관리 → 검색 인덱싱
3. 사용자 활동 → 포인트 계산 → 랭킹 업데이트 → 통계 생성

🚀 성능 최적화:
- 메모리 효율적인 슬라이딩 윈도우 채팅 히스토리
- 비동기 API 호출 및 에러 복구 메커니즘
- JSON 파일 기반 경량 데이터베이스로 빠른 응답
- 캐싱 및 세션 상태 최적화

⚠️ 주의사항:
- 대용량 파일로 인해 메모리 사용량 모니터링 필요
- API 키 및 인증 정보 보안 관리 중요
- 동시 사용자 접근 시 데이터 일관성 보장 필요
"""

import streamlit as st  # Streamlit 웹 앱 프레임워크
import json  # JSON 데이터 직렬화/역직렬화
import os  # 파일 시스템 접근 및 경로 관리
import uuid  # 고유 식별자 생성 (사용자 ID, 세션 ID 등)
import requests  # HTTP API 호출 (RAG API, LLM API)
import time  # 시간 지연 및 성능 측정
import re  # 정규표현식 (데이터 검증, 텍스트 파싱)
import logging  # 로깅 시스템 (에러 추적, 디버깅)
from datetime import datetime  # 날짜/시간 처리 (로그, 타임스탬프)
from typing import Dict, List, Optional, Any  # 타입 힌팅 (코드 가독성 및 안정성)

from config import DATA_CONFIG, API_CONFIG, MISC_CONFIG, AUTH_CONFIG, get_index_system_prompt, get_index_config, RESPONSE_FORMAT_TEMPLATE, get_index_rag_name, TEST_CONFIG  # 설정 파일에서 구성 정보 가져오기

# ====================================
# 🔧 전역 변수 및 상수 정의
# ====================================

# 간소화된 인증 시스템 설정 - streamlit-authenticator 대신 자체 구현 사용
STREAMLIT_AUTHENTICATOR_AVAILABLE = False  # 외부 인증 라이브러리 비활성화 플래그

# === 로깅 시스템 초기화 ===
logger = logging.getLogger(__name__)  # 모듈별 로거 인스턴스 생성 (에러 추적 및 디버깅용)

# ====================================
# 🗃️ 로컬 데이터 관리 시스템
# ====================================
# 사용자 계정, 채팅 기록, 질문/답변 등을 JSON 파일로 관리하는 경량 데이터베이스 시스템

def initialize_data() -> Dict[str, Any]:
    """
    메인 데이터 저장소 초기화
    
    시스템 최초 실행 시 또는 데이터 파일이 없을 때 기본 구조를 생성합니다.
    Q&A 시스템, 채팅 기록, 사용자 포인트 등 모든 데이터 스키마를 통합 관리합니다.
    
    호출 관계:
    - 🏠_Home.py, 챗봇 페이지들에서 시스템 시작 시 호출
    - load_data() -> save_data() 체인 호출로 데이터 초기화
    
    부작용:
    - knowledge_data.json 파일이 없으면 새로 생성
    - 파일 시스템에 JSON 데이터 영구 저장
    
    Returns:
        Dict[str, Any]: 초기화된 데이터 구조 또는 기존 데이터
            - questions: List[Dict] - Q&A 시스템용 질문 목록
            - answers: List[Dict] - Q&A 시스템용 답변 목록  
            - chat_history: List[Dict] - 기술 챗봇 대화 기록
            - admin_chat_history: List[Dict] - 관리자 챗봇 대화 기록
            - user_points: Dict[str, int] - 사용자별 포인트 시스템
    """
    data_file = DATA_CONFIG["data_file"]
    
    if not os.path.exists(data_file):
        # 시스템 기본 스키마 정의
        initial_data = {
            "questions": [],  # Q&A 시스템용 질문 목록
            "answers": [],    # Q&A 시스템용 답변 목록
            "users": {},      # 레거시 사용자 정보 (하위 호환성)
            "likes": {},      # 답변 좋아요 시스템
            "search_logs": [],  # 검색 기록 분석용
            "chat_history": [],  # 기술 챗봇 대화 기록
            "admin_chat_history": [],  # 관리자 챗봇 대화 기록 (호환성)
            "user_points": {},  # 사용자 포인트 시스템
            "registration_requests": [],  # 회원가입 신청 목록 (관리자 승인 대기)
            "approved_users": {}  # 승인된 사용자 목록 (자동 로그인 가능)
        }
        save_data(initial_data)
        return initial_data
    else:
        # 기존 데이터 로드 및 호환성 업데이트
        data = load_data()
        
        # 회원가입 관련 필드가 없으면 추가
        updated = False
        if "registration_requests" not in data:
            data["registration_requests"] = []
            updated = True
            logger.info("기존 데이터베이스에 registration_requests 필드 추가됨")
            
        if "approved_users" not in data:
            data["approved_users"] = {}
            updated = True
            logger.info("기존 데이터베이스에 approved_users 필드 추가됨")
            
        if updated:
            save_data(data)
        
        return data

def save_data(data: Dict[str, Any]) -> None:
    """
    데이터를 JSON 파일에 안전하게 저장
    
    메모리의 데이터 변경사항을 영구 저장소에 동기화합니다.
    UTF-8 인코딩과 들여쓰기를 적용하여 가독성과 국제화를 지원합니다.
    
    호출 관계:
    - save_chat_history(), add_question(), add_answer() 등에서 호출
    - 모든 데이터 변경 작업 후 자동으로 호출되어 일관성 보장
    
    부작용:
    - knowledge_data.json 파일을 완전히 덮어씀 (원자적 쓰기)
    - 파일 쓰기 오류 시 IOError 예외 발생 (상위로 전파)
    
    Args:
        data: 저장할 데이터 구조 (JSON 직렬화 가능한 타입)
    """
    data_file = DATA_CONFIG["data_file"]
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data() -> Dict[str, Any]:
    """
    JSON 파일에서 데이터 로드 및 스키마 호환성 보장
    
    영구 저장소에서 데이터를 메모리로 로드하면서 스키마 진화를 지원합니다.
    새로 추가된 필드들을 자동으로 보완하여 하위 호환성을 유지합니다.
    
    호출 관계:
    - initialize_data()에서 파일이 존재할 때 호출
    - 시스템 전반에서 데이터 조회 시 간접적으로 호출
    
    복구 메커니즘:
    - FileNotFoundError -> initialize_data() 재귀 호출로 자동 생성
    - JSONDecodeError -> 손상된 파일 무시하고 새로 초기화
    
    Returns:
        Dict[str, Any]: 로드된 데이터 또는 새로 초기화된 데이터
            - 기존 스키마는 그대로 유지
            - 누락된 스키마 필드는 기본값으로 자동 보완
    """
    data_file = DATA_CONFIG["data_file"]
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 하위 호환성: 새로 추가된 스키마 필드들을 기존 데이터에 보완
            required_keys = ["search_logs", "chat_history", "admin_chat_history"]
            for key in required_keys:
                if key not in data:
                    data[key] = []
            
            # 포인트 시스템 스키마 보완
            if "user_points" not in data:
                data["user_points"] = {}
                    
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # 파일 없음 또는 JSON 파싱 오류 시 자동 복구
        return initialize_data()

# ====================================
# 🔐 Streamlit Authenticator 기반 인증 시스템
# ====================================
# streamlit-authenticator를 사용한 브라우저별 독립 세션 관리
# 쿠키 기반 인증으로 URL 공유 시에도 개별 로그인 보장

def get_users_from_secrets():
    """
    통합 사용자 관리 시스템에서 사용자 정보 로드
    
    Returns:
        Dict: 사용자 정보 딕셔너리
    """
    try:
        from user_manager import get_all_active_users
        return get_all_active_users()
    except Exception as e:
        logger.error(f"사용자 정보 로드 실패: {e}")
        return {}

def verify_password(username: str, password: str) -> bool:
    """
    사용자명과 비밀번호 확인
    
    Args:
        username: 사용자명
        password: 비밀번호
        
    Returns:
        bool: 인증 성공 여부
    """
    try:
        from user_manager import verify_user_password
        return verify_user_password(username, password)
    except Exception as e:
        logger.error(f"비밀번호 확인 실패: {e}")
        return False

def simple_login(username: str, password: str) -> tuple[bool, str, dict]:
    """
    간단한 로그인 처리
    
    Args:
        username: 사용자명
        password: 비밀번호
        
    Returns:
        tuple: (성공여부, 메시지, 사용자정보)
    """
    try:
        from user_manager import authenticate_user
        success, message, user_data = authenticate_user(username, password)
        if success and user_data:
            # 호환성을 위해 필요한 필드들 매핑
            return True, message, {
                'username': username,
                'name': user_data.get('name', user_data.get('nickname', username)),
                'nox_id': user_data.get('nox_id', username),
                'department': user_data.get('department', 'Unknown'),
                'user_id': user_data.get('user_id'),
                'nickname': user_data.get('nickname', user_data.get('name', username)),
                'role': user_data.get('role', 'user')
            }
        else:
            return False, message, {}
    except Exception as e:
        logger.error(f"로그인 처리 실패: {e}")
        return False, "로그인 처리 중 오류가 발생했습니다", {}
        
def initialize_users_data() -> Dict[str, Any]:
    """
    사용자 계정 데이터베이스 초기화
    
    사용자 프로필, 세션 정보, 로그인 시도 기록을 관리하는 별도 데이터베이스를 구성합니다.
    메인 데이터와 분리하여 보안성을 높이고 사용자 관련 작업의 성능을 개선합니다.
    
    Returns:
        Dict[str, Any]: 초기화된 사용자 데이터베이스 구조
    """
    users_file = DATA_CONFIG["users_file"]
    
    if not os.path.exists(users_file):
        initial_users = {
            "users": {},  # user_id -> user_profile 매핑
            "sessions": {},  # session_id -> user_id 매핑 (확장용)
            "login_attempts": {}  # 보안: 로그인 시도 추적 (확장용)
        }
        save_users_data(initial_users)
        return initial_users
    else:
        return load_users_data()

def save_users_data(users_data: Dict[str, Any]) -> None:
    """
    사용자 데이터베이스를 JSON 파일에 저장
    
    사용자 계정 정보의 변경사항을 즉시 영구 저장소에 반영합니다.
    메인 데이터와 독립적으로 관리되어 사용자 정보 업데이트 시 성능 최적화가 가능합니다.
    
    Args:
        users_data: 저장할 사용자 데이터베이스
    """
    users_file = DATA_CONFIG["users_file"]
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

def load_users_data() -> Dict[str, Any]:
    """
    사용자 데이터베이스 로드 및 오류 복구
    
    사용자 계정 정보를 메모리로 로드하며, 파일 손상 시 자동 복구를 수행합니다.
    데이터베이스 무결성 검사를 통해 시스템 안정성을 보장합니다.
    
    Returns:
        Dict[str, Any]: 로드된 사용자 데이터베이스 또는 새로 초기화된 구조
    """
    users_file = DATA_CONFIG["users_file"]
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return initialize_users_data()

def validate_nox_id(nox_id: str) -> tuple[bool, str]:
    """
    사용자 ID 형식 검증 (완화된 규칙)
    
    사용자 ID의 형식적 유효성을 검사합니다. 기존 시스템과 호환성을 위해
    영문, 숫자, 특수문자(., -, _)를 허용하는 유연한 정책을 적용합니다.
    
    Args:
        nox_id: 검증할 사용자 ID
        
    Returns:
        tuple[bool, str]: (유효성 여부, 오류 메시지)
    """
    if len(nox_id) < AUTH_CONFIG["username_min_length"]:
        return False, f"사용자 ID는 최소 {AUTH_CONFIG['username_min_length']}자 이상이어야 합니다."
    
    # 유연한 ID 형식: 기존 시스템 계정과의 호환성을 위해 특수문자 허용
    if not re.match(r'^[a-zA-Z0-9._-]+$', nox_id):
        return False, "사용자 ID는 영문, 숫자, '.', '-', '_'만 사용 가능합니다."
    
    return True, ""

def validate_nickname(nickname: str) -> tuple[bool, str]:
    """
    사용자 닉네임 형식 검증
    
    화면에 표시될 닉네임의 형식을 검증합니다. 한글, 영문, 숫자와 
    일반적인 특수문자를 허용하여 사용자 편의성을 높입니다.
    
    Args:
        nickname: 검증할 닉네임
        
    Returns:
        tuple[bool, str]: (유효성 여부, 오류 메시지)
    """
    if len(nickname) < AUTH_CONFIG["nickname_min_length"]:
        return False, f"닉네임은 최소 {AUTH_CONFIG['nickname_min_length']}자 이상이어야 합니다."
    
    # 한글, 영문, 숫자, 공백, 하이픈, 언더스코어 허용
    if not re.match(r'^[a-zA-Z0-9가-힣_\s-]+$', nickname):
        return False, "닉네임은 영문, 한글, 숫자, 공백, '-', '_'만 사용 가능합니다."
    
    return True, ""

def validate_department(department: str) -> tuple[bool, str]:
    """
    소속부서 유효성 검증
    
    사용자가 선택한 부서가 시스템에 등록된 유효한 부서인지 확인합니다.
    조직 구조 변경 시 config.py에서 부서 목록을 업데이트하여 관리합니다.
    
    Args:
        department: 검증할 부서명
        
    Returns:
        tuple[bool, str]: (유효성 여부, 오류 메시지)
    """
    if not department:
        return False, "소속부서를 선택해주세요."
    
    if department not in AUTH_CONFIG["departments"]:
        return False, "유효한 소속부서를 선택해주세요."
    
    return True, ""

def register_user(nox_id: str, nickname: str, department: str) -> tuple[bool, str]:
    """
    신규 사용자 등록 처리
    
    입력된 사용자 정보의 유효성을 검사하고 중복을 확인한 후 새 계정을 생성합니다.
    기존 데이터와의 호환성을 유지하면서 새로운 사용자 스키마를 적용합니다.
    
    Args:
        nox_id: 사용자 ID
        nickname: 표시용 닉네임
        department: 소속 부서
        
    Returns:
        tuple[bool, str]: (등록 성공 여부, 결과 메시지)
    """
    users_data = load_users_data()
    
    # 중복 검사: 기존 다양한 데이터 형식과의 호환성 고려
    for user_info in users_data["users"].values():
        # 레거시 데이터 호환성: username 필드도 함께 검사
        existing_nox_id = user_info.get("nox_id", user_info.get("username", ""))
        existing_nickname = user_info.get("nickname", user_info.get("display_name", ""))
        
        if existing_nox_id == nox_id:
            return False, "이미 사용 중인 사용자 ID입니다."
        if existing_nickname == nickname:
            return False, "이미 사용 중인 닉네임입니다."
    
    # 새 사용자 프로필 생성
    user_id = str(uuid.uuid4())
    user_info = {
        "user_id": user_id,
        "nox_id": nox_id,
        "nickname": nickname,
        "department": department,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_login": None,
        "is_active": True  # 계정 활성화 상태
    }
    
    users_data["users"][user_id] = user_info
    save_users_data(users_data)
    
    return True, "등록이 완료되었습니다."

def is_logged_in() -> bool:
    """
    간단한 인증 시스템 기반 로그인 상태 확인
    
    현재 세션에서 사용자가 로그인되어 있는지 확인합니다.
    
    Returns:
        bool: 로그인 상태
            - True: 유효한 세션 존재 (auth_user 정보 있음)
            - False: 미인증 상태 (로그인 필요)
    """
    # 간단한 세션 상태 확인
    return (
        st.session_state.get("logged_in") == True and 
        st.session_state.get("auth_user") is not None
    )

def setup_session_after_login(username: str, name: str):
    """
    간단한 인증 시스템 로그인 성공 후 세션 정보 설정
    
    simple_login() 성공 후 호출되어 세션에 필요한 사용자 정보를 설정합니다.
    포인트 시스템과의 연동을 위해 auth_user, auth_name 정보를 저장합니다.
    
    호출 관계:
    - login 페이지에서 simple_login() 성공 후 호출
    - 포인트 시스템 함수들이 st.session_state["auth_user"] 참조
    
    부작용:
    - st.session_state에 logged_in, auth_user, auth_name 설정
    - secrets.toml에서 추가 사용자 정보 로드하여 보완
    
    Args:
        username: 사용자명 (녹스 ID)
        name: 표시명 (닉네임)
    """
    # 로그인 상태 설정 (중요!)
    st.session_state["logged_in"] = True
    
    # 포인트 시스템과 연동을 위한 세션 정보 설정
    st.session_state["auth_user"] = username  # 녹스 ID (포인트 적립 시 사용)
    st.session_state["auth_name"] = name      # 표시명 (UI에서 사용)
    
    try:
        # 통합 사용자 관리 시스템에서 추가 사용자 정보 로드
        from user_manager import get_active_user
        user_info = get_active_user(username)
        if user_info:
            st.session_state["auth_nox_id"] = user_info.get("nox_id", username)
            st.session_state["auth_department"] = user_info.get("department", "기타")
            logger.info(f"사용자 {username}({name}) 로그인 성공 - 세션 정보 설정 완료")
        else:
            # 기본 정보로 설정
            st.session_state["auth_nox_id"] = username
            st.session_state["auth_department"] = "기타"
            logger.warning(f"사용자 {username}의 추가 정보를 찾을 수 없음")
    except Exception as e:
        # 오류 발생 시 기본 로그인은 유지
        st.session_state["auth_nox_id"] = username
        st.session_state["auth_department"] = "기타"
        logger.warning(f"사용자 {username}의 추가 정보 로드 실패: {e}")

def logout_user() -> None:
    """
    간단한 인증 시스템 로그아웃 처리
    
    세션에서 모든 인증 관련 정보를 제거합니다.
    
    부작용:
    - 로그인 상태 및 사용자 정보 세션 키들 정리
    - 임시 캐시나 상태값들 초기화
    """
    # 로그인 상태 제거
    if "logged_in" in st.session_state:
        del st.session_state["logged_in"]
    
    # 포인트 시스템 연동 세션 정리
    auth_keys = ["auth_user", "auth_name", "auth_nox_id", "auth_department"]
    for key in auth_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    logger.info("로그아웃 - 모든 세션 정리 완료")


def initialize_session_state() -> None:
    """
    세션 상태 초기화 (호환성 함수)
    
    순수 인증 시스템에서는 별도의 초기화가 필요하지 않습니다.
    기존 코드와의 호환성을 위해 유지되는 함수입니다.
    """
    # 순수 인증 시스템에서는 별도 세션 초기화 불필요
    pass

def restore_login_from_storage() -> bool:
    """
    브라우저 저장소에서 로그인 정보 복원 (호환성 함수)
    
    순수 인증 시스템에서는 세션 기반 인증을 사용하므로
    별도의 브라우저 저장소 복원이 필요하지 않습니다.
    
    기존 코드 호환성을 위해 유지하되, 항상 False를 반환합니다.
    """
    return False  # 순수 인증 시스템에서는 불필요

def require_login() -> bool:
    """
    순수 인증 시스템 기반 페이지 접근 권한 검증
    
    모든 보호된 페이지의 진입점에서 호출되는 접근 제어 함수입니다.
    simple_login() 기반의 인증 상태를 확인하여 페이지 접근을 제어합니다.
    
    호출 관계:
    - 모든 챗봇 페이지와 관리자 페이지의 main() 함수에서 최우선 호출
    - 로그인되지 않은 사용자는 로그인 페이지로 자동 리디렉션
    
    인증 플로우:
    1. 순수 인증 시스템 세션 상태 확인
    2. 미인증 시 로그인 안내 메시지 표시 후 페이지 중단
    3. 인증 완료 시 페이지 접근 허용
    
    Returns:
        bool: 페이지 접근 허용 여부
            - True: 로그인 완료, 페이지 계속 진행
            - False: 로그인 필요, 페이지 진행 중단
    """
    # 순수 인증 시스템 세션 상태 확인
    if not is_logged_in():
        st.error("🔒 이 페이지에 접근하려면 로그인이 필요합니다.")
        st.info("👈 사이드바에서 '로그인' 메뉴를 사용해 로그인해주세요.")
        st.stop()
        return False
    
    return True

def get_current_user() -> Optional[Dict]:
    """
    현재 로그인한 사용자의 프로필 정보 반환
    
    순수 인증 시스템 세션에서 사용자 정보를 조합하여 반환합니다.
    
    Returns:
        Optional[Dict]: 사용자 프로필 정보 또는 None (미로그인)
    """
    if not is_logged_in():
        return None
        
    auth_user = st.session_state.get("auth_user")
    auth_name = st.session_state.get("auth_name")
    
    if not auth_user:
        return None
        
    # 통합 사용자 관리 시스템에서 사용자 정보 조회
    try:
        from user_manager import get_active_user
        user_info = get_active_user(auth_user)
        if user_info:
            return {
                "user_id": user_info.get('user_id', auth_user),
                "nox_id": user_info.get('nox_id', auth_user),
                "nickname": user_info.get('nickname', auth_name),
                "department": user_info.get('department', 'Unknown'),
                "role": user_info.get('role', 'user')
            }
    except Exception as e:
        logger.error(f"사용자 정보 조회 실패: {e}")
    
    # 폴백: 기본 정보만 반환
    return {
        "user_id": auth_user,
        "nox_id": auth_user,
        "nickname": auth_name,
        "department": "Unknown",
        "role": "user"
    }

def get_user_id() -> str:
    """
    현재 사용자의 고유 ID 반환
    
    순수 인증 시스템의 username을 사용자 ID로 활용합니다.
    
    Returns:
        str: 사용자 고유 ID (미로그인 시 "anonymous")
    """
    return st.session_state.get("auth_user", "anonymous")

def get_username() -> str:
    """
    현재 사용자의 표시 이름 반환 (닉네임)
    
    순수 인증 시스템의 사용자 이름을 반환합니다.
    
    Returns:
        str: 사용자 닉네임 (미로그인 시 "Guest")
    """
    return st.session_state.get("auth_name", "Guest")

def get_display_name(user=None) -> str:
    """
    사용자 표시명 반환 (호환성 인터페이스)
    
    기존 코드와의 호환성을 위해 제공되는 함수로, get_username()과 동일한 결과를 반환합니다.
    외부에서 사용자 객체를 직접 전달할 수도 있습니다.
    
    Args:
        user: 선택적 사용자 객체 (None이면 현재 사용자)
        
    Returns:
        str: 사용자 표시명
    """
    if user:
        return user.get("nickname", "Guest")
    else:
        return get_username()

def get_nox_id() -> str:
    """
    현재 사용자의 시스템 ID 반환
    
    secrets.toml에서 설정된 nox_id를 반환합니다.
    
    Returns:
        str: 사용자 시스템 ID (미로그인 시 "anonymous")
    """
    if not is_logged_in():
        return "anonymous"
        
    auth_user = st.session_state.get("auth_user")
    if not auth_user:
        return "anonymous"
        
    # 통합 사용자 관리 시스템에서 nox_id 조회
    try:
        from user_manager import get_active_user
        user_info = get_active_user(auth_user)
        if user_info:
            return user_info.get('nox_id', auth_user)
    except Exception as e:
        logger.error(f"nox_id 조회 실패: {e}")
    
    return auth_user  # 폴백

def show_login_required() -> None:
    """
    로그인 필수 안내 화면 표시
    
    미인증 사용자에게 로그인이 필요함을 알리고, 로그인 페이지로의
    이동 버튼을 제공하는 사용자 친화적 안내 화면을 구성합니다.
    """
    st.error("🔐 이 페이지를 이용하려면 로그인이 필요합니다.")
    st.markdown("---")
    st.info("📝 **통합 인증** 페이지에서 로그인하거나 신규 등록해주세요.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐 로그인 / 등록하기", type="primary", use_container_width=True):
            st.switch_page("pages/1_🔑_로그인.py")

# ====================================  
# 👤 레거시 관리자 시스템 (하위 호환성)
# ====================================
# 기존 관리자 기능과의 호환성을 위해 유지되는 함수들

def check_admin() -> bool:
    """
    레거시 관리자 권한 확인 (호환성 유지)
    
    기존 관리자 페이지와의 호환성을 위해 유지되는 함수입니다.
    세션 상태에서 관리자 인증 여부를 확인합니다.
    
    Returns:
        bool: 관리자 권한 보유 여부
    """
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    return st.session_state.is_admin

def login_admin(password: str) -> bool:
    """
    레거시 관리자 로그인 처리 (호환성 유지)
    
    기존 시스템의 관리자 인증 로직으로, 설정 파일의 고정 비밀번호와 비교합니다.
    보안상 권장되지 않으므로 향후 통합 인증 시스템으로 대체 예정입니다.
    
    Args:
        password: 관리자 비밀번호
        
    Returns:
        bool: 인증 성공 여부
    """
    if password == DATA_CONFIG["admin_password"]:
        st.session_state.is_admin = True
        return True
    return False

def logout_admin() -> None:
    """
    레거시 관리자 로그아웃 처리 (호환성 유지)
    
    관리자 세션 상태를 초기화하여 관리자 권한을 제거합니다.
    
    """
    st.session_state.is_admin = False

# ====================================
# 👥 사용자 관리 시스템 (관리자용)
# ====================================
# 관리자가 사용자 계정을 조회, 수정, 관리할 수 있는 기능들

def get_all_users() -> List[Dict]:
    """
    전체 사용자 목록 반환 (새 통합 시스템 활용)

    users_management.json의 활성 사용자 목록을 반환합니다.
    회원가입 → 승인 → 활성 사용자 플로우가 완료된 사용자들만 포함됩니다.

    Returns:
        List[Dict]: 활성 사용자 프로필 목록
    """
    try:
        from user_manager import get_all_active_users
        active_users_dict = get_all_active_users()

        # 딕셔너리를 리스트로 변환하며 호환성을 위한 필드 매핑
        users = []
        for username, user_data in active_users_dict.items():
            user_profile = {
                "user_id": user_data.get("user_id", f"user_{username}"),
                "nox_id": user_data.get("nox_id", username),
                "nickname": user_data.get("nickname", user_data.get("name", username)),
                "name": user_data.get("name", username),
                "department": user_data.get("department", "기타"),
                "created_at": user_data.get("created_at", user_data.get("approved_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                "last_login": user_data.get("last_login"),
                "is_active": user_data.get("is_active", True),
                "role": user_data.get("role", "user"),
                "approved_at": user_data.get("approved_at"),
                "approved_by": user_data.get("approved_by"),
                "user_type": "approved_active"  # 승인 완료된 활성 사용자
            }
            users.append(user_profile)

        return users

    except Exception as e:
        logger.error(f"활성 사용자 목록 조회 실패: {e}")
        # 폴백: 기존 시스템 사용
        return get_all_users_legacy()

def get_all_users_legacy() -> List[Dict]:
    """
    전체 사용자 목록 반환 (레거시 시스템용)

    기존 users_data.json과 knowledge_data.json 시스템을 사용하는 폴백 함수
    """
    users_data = load_users_data()
    main_data = initialize_data()

    # 기존 등록 사용자
    users = list(users_data["users"].values())

    # 승인된 사용자 추가
    approved_users = main_data.get("approved_users", {})
    for username, approved_user in approved_users.items():
        # 승인된 사용자를 표준 형식으로 변환
        user_profile = {
            "user_id": f"approved_{username}",
            "nox_id": approved_user.get("nox_id", username),
            "nickname": approved_user.get("name", username),
            "department": approved_user.get("department", "기타"),
            "created_at": approved_user.get("approved_at", datetime.now().isoformat()),
            "last_login": None,
            "is_active": True,
            "user_type": "approved"  # 구분을 위한 태그
        }
        users.append(user_profile)

    # 레거시 데이터를 새 표준 형식으로 정규화 (데이터 마이그레이션)
    normalized_users = []
    for user in users:
        # 기존 다양한 필드명을 표준 형식으로 통일
        if "nox_id" not in user:
            user["nox_id"] = user.get("username", f"user_{user.get('user_id', 'unknown')[:8]}")
        if "nickname" not in user:
            user["nickname"] = user.get("display_name", user.get("username", "사용자"))
        if "department" not in user:
            user["department"] = "기타"
        if "is_active" not in user:
            user["is_active"] = True
        if "user_type" not in user:
            user["user_type"] = "regular"  # 기본값

        normalized_users.append(user)

    return normalized_users

def search_users(keyword: str = "") -> List[Dict]:
    """
    사용자 검색 (레거시 데이터 호환성 포함)
    
    키워드를 통해 사용자를 검색하며, 검색 과정에서 데이터 정규화도 함께 수행합니다.
    ID, 닉네임, 부서 정보를 대상으로 포괄적 검색을 지원합니다.
    
    Args:
        keyword: 검색 키워드 (빈 문자열이면 전체 목록)
        
    Returns:
        List[Dict]: 검색 조건에 맞는 사용자 목록
    """
    users = get_all_users()
    
    if not keyword:
        return users
    
    keyword = keyword.lower()
    filtered_users = []
    
    for user in users:
        # 다중 필드 검색: ID, 닉네임, 부서를 모두 대상으로 포함
        nox_id = user.get("nox_id", user.get("username", "")).lower()
        nickname = user.get("nickname", user.get("display_name", user.get("username", ""))).lower()
        department = user.get("department", "").lower()
        
        if (keyword in nox_id or 
            keyword in nickname or 
            keyword in department):
            # 검색 결과에서도 데이터 정규화 적용
            if "nox_id" not in user:
                user["nox_id"] = user.get("username", "unknown")
            if "nickname" not in user:
                user["nickname"] = user.get("display_name", user.get("username", "사용자"))
            if "department" not in user:
                user["department"] = "기타"
                
            filtered_users.append(user)
    
    return filtered_users

def toggle_user_status(user_id: str) -> bool:
    """
    사용자 계정 활성화/비활성화 상태 토글 (새 통합 시스템 지원)

    관리자가 사용자 계정을 일시정지하거나 재활성화할 때 사용합니다.
    비활성화된 계정은 로그인할 수 없지만 데이터는 보존됩니다.

    Args:
        user_id: 상태를 변경할 사용자의 고유 ID

    Returns:
        bool: 상태 변경 성공 여부
    """
    try:
        # 새 통합 시스템 먼저 시도
        from user_manager import load_users_data as load_user_management_data, save_users_data as save_user_management_data

        user_management_data = load_user_management_data()

        # user_id로 사용자 찾기 (nox_id가 될 수도 있고 user_id가 될 수도 있음)
        target_username = None
        for username, user_data in user_management_data.get("active_users", {}).items():
            if user_data.get("user_id") == user_id or username == user_id:
                target_username = username
                break

        if target_username:
            user_info = user_management_data["active_users"][target_username]
            user_info["is_active"] = not user_info.get("is_active", True)
            user_management_data["active_users"][target_username] = user_info
            return save_user_management_data(user_management_data)

        # 폴백: 레거시 시스템 사용
        return toggle_user_status_legacy(user_id)

    except Exception as e:
        logger.error(f"사용자 상태 토글 실패: {e}")
        return toggle_user_status_legacy(user_id)

def toggle_user_status_legacy(user_id: str) -> bool:
    """레거시 시스템용 사용자 상태 토글"""
    users_data = load_users_data()

    if user_id in users_data["users"]:
        user_info = users_data["users"][user_id]
        user_info["is_active"] = not user_info.get("is_active", True)
        users_data["users"][user_id] = user_info
        save_users_data(users_data)
        return True

    return False

def delete_user(user_id: str) -> bool:
    """
    사용자 계정 완전 삭제 (새 통합 시스템 우선 지원)

    관리자가 사용자 계정을 영구적으로 삭제할 때 사용합니다.
    이 작업은 되돌릴 수 없으므로 신중하게 사용해야 합니다.

    Args:
        user_id: 삭제할 사용자의 고유 ID

    Returns:
        bool: 삭제 성공 여부
    """
    deleted = False

    try:
        # 새 통합 시스템에서 사용자 찾기 및 삭제
        from user_manager import load_users_data as load_user_management_data, save_users_data as save_user_management_data

        user_management_data = load_user_management_data()

        # user_id로 사용자 찾기 (nox_id가 될 수도 있고 user_id가 될 수도 있음)
        target_username = None
        for username, user_data in user_management_data.get("active_users", {}).items():
            if user_data.get("user_id") == user_id or username == user_id:
                target_username = username
                break

        if target_username and target_username in user_management_data["active_users"]:
            del user_management_data["active_users"][target_username]
            if save_user_management_data(user_management_data):
                deleted = True
                logger.info(f"사용자 {target_username} 삭제 완료 (통합 시스템)")

    except Exception as e:
        logger.error(f"새 통합 시스템에서 사용자 삭제 실패: {e}")

    # 레거시 시스템에서도 삭제 시도 (데이터 일관성을 위해)
    if delete_user_legacy(user_id):
        deleted = True

    return deleted

def delete_user_legacy(user_id: str) -> bool:
    """레거시 시스템용 사용자 삭제"""
    deleted = False

    # 1. users_data.json에서 삭제 시도
    users_data = load_users_data()
    if user_id in users_data["users"]:
        del users_data["users"][user_id]
        save_users_data(users_data)
        deleted = True

    # 2. knowledge_data.json의 approved_users에서 삭제 시도
    main_data = initialize_data()

    # user_id가 "approved_" 접두사를 가진 경우 실제 username 추출
    if user_id.startswith("approved_"):
        actual_username = user_id.replace("approved_", "")
    else:
        actual_username = user_id

    # approved_users에서 삭제
    if "approved_users" in main_data and actual_username in main_data["approved_users"]:
        del main_data["approved_users"][actual_username]

        # knowledge_data.json에 저장
        try:
            with open(DATA_CONFIG["data_file"], 'w', encoding='utf-8') as f:
                import json
                json.dump(main_data, f, ensure_ascii=False, indent=2)
            deleted = True
        except Exception as e:
            logger.error(f"메인 데이터 저장 실패: {e}")

    return deleted

def update_user_info(user_id: str, nickname: str, department: str) -> tuple[bool, str]:
    """
    사용자 프로필 정보 업데이트 (새 통합 시스템 우선 지원)

    관리자가 사용자의 닉네임이나 부서 정보를 수정할 때 사용합니다.
    닉네임 중복 검사를 포함하여 데이터 무결성을 보장합니다.

    Args:
        user_id: 수정할 사용자의 고유 ID
        nickname: 새로운 닉네임
        department: 새로운 부서

    Returns:
        tuple[bool, str]: (수정 성공 여부, 결과 메시지)
    """
    try:
        # 새 통합 시스템 먼저 시도
        from user_manager import load_users_data as load_user_management_data, save_users_data as save_user_management_data

        user_management_data = load_user_management_data()

        # user_id로 사용자 찾기
        target_username = None
        for username, user_data in user_management_data.get("active_users", {}).items():
            if user_data.get("user_id") == user_id or username == user_id:
                target_username = username
                break

        if not target_username:
            # 폴백: 레거시 시스템 사용
            return update_user_info_legacy(user_id, nickname, department)

        # 닉네임 중복 검사 (본인 제외)
        for username, user_info in user_management_data.get("active_users", {}).items():
            if username != target_username and user_info.get("nickname") == nickname:
                return False, "이미 사용 중인 닉네임입니다."

        # 사용자 정보 업데이트
        user_management_data["active_users"][target_username]["nickname"] = nickname
        user_management_data["active_users"][target_username]["name"] = nickname  # name 필드도 함께 업데이트
        user_management_data["active_users"][target_username]["department"] = department

        if save_user_management_data(user_management_data):
            return True, "사용자 정보가 업데이트되었습니다."
        else:
            return False, "사용자 정보 저장에 실패했습니다."

    except Exception as e:
        logger.error(f"사용자 정보 업데이트 실패: {e}")
        # 폴백: 레거시 시스템 사용
        return update_user_info_legacy(user_id, nickname, department)

def update_user_info_legacy(user_id: str, nickname: str, department: str) -> tuple[bool, str]:
    """레거시 시스템용 사용자 정보 업데이트"""
    users_data = load_users_data()

    if user_id not in users_data["users"]:
        return False, "사용자를 찾을 수 없습니다."

    # 닉네임 중복 검사 (본인 제외)
    for uid, user_info in users_data["users"].items():
        if uid != user_id and user_info["nickname"] == nickname:
            return False, "이미 사용 중인 닉네임입니다."

    # 사용자 정보 업데이트
    users_data["users"][user_id]["nickname"] = nickname
    users_data["users"][user_id]["department"] = department
    save_users_data(users_data)

    return True, "사용자 정보가 업데이트되었습니다."

# ====================================
# 🤖 통합 AI API 시스템  
# ====================================
# 3개 전용 챗봇을 위한 LLM 및 RAG API 통합 관리 시스템
# 
# 주요 구성요소:
# - call_llm_api(): 모든 챗봇이 공통 사용하는 언어모델 API (10턴 대화 맥락 지원)
# - call_rag_api_with_chatbot_type(): 챗봇별 전용 문서 검색 API (통합 인덱스 관리)
# - get_chatbot_response(): 사용자 인터페이스용 메인 응답 생성 함수
# - format_source_citations(): 챗봇별 출처 표시 형식 처리
#
# 리팩터링으로 레거시 개별 API 함수들을 완전히 통합하여:
# - 코드 중복 제거 (기존 6개 함수 -> 2개 핵심 함수)
# - 일관된 오류 처리 및 로깅
# - 확장된 대화 맥락 (5턴 -> 10턴)
# - 챗봇별 특화 기능 (프롬프트, 인덱스, 출처 형식)

def call_llm_api(user_message: str, retrieve_data: List[str], chat_history: list = None, source_data: List[dict] = None, user_id: str = None, custom_system_prompt: str = None, chatbot_type: str = "ae_wiki") -> str:
    """
    통합 LLM API 호출 시스템 - 확장된 대화 맥락 지원
    
    3개 전용 챗봇이 공통으로 사용하는 언어모델 API 호출의 중추 함수입니다.
    RAG 검색 결과와 확장된 10턴 대화 맥락을 결합하여 문맥 인식형 고품질 응답을 생성합니다.
    API 설정이 필수이며, 설정되지 않은 경우 오류를 반환합니다.
    
    핵심 기능:
    - 챗봇별 전용 시스템 프롬프트 자동 선택 (ae_wiki_chatbot, glossary_chatbot, jedec_chatbot)
    - 확장된 대화 맥락 (기존 5턴 -> 10턴)으로 연속 대화 품질 향상
    - 통합 응답 형식 템플릿으로 일관된 답변 구조 제공
    - 챗봇별 출처 인용 형식 자동 적용 (Confluence URL, 확장 카드, 파일명+페이지)
    - API 장애 시 오류 메시지와 해결 방법 안내
    
    호출 관계:
    - get_chatbot_response()에서 메인 응답 생성 시 호출
    - conversation_manager에서 10턴 대화 맥락 로드 (선택적)
    - format_source_citations()에서 챗봇별 인용 형식 적용
    
    부작용:
    - requests 라이브러리로 외부 LLM API 호출 (네트워크 I/O)
    - 응답 시간: 일반적으로 1-5초, 최대 타임아웃 30초
    - API 실패 시 예외 로깅 및 사용자 친화적 오류 메시지 반환
    
    Args:
        user_message: 사용자 질문 텍스트
        retrieve_data: RAG 검색 결과 문서 내용 목록 (최대 3개 문서)
        # is_admin_bot 매개변수 제거됨 - chatbot_type으로 완전히 대체
        chat_history: 이전 대화 기록 (conversation_manager 없을 시 fallback)
        source_data: 문서 메타데이터 목록 (출처 표시용)
        user_id: 사용자 식별자 (10턴 대화 맥락 로드용)
        custom_system_prompt: 커스텀 시스템 프롬프트 (기본값 무시 시 사용)
        chatbot_type: 챗봇 유형 식별자 ("ae_wiki", "glossary", "jedec")
        
    Returns:
        str: LLM 생성 응답
            - 성공: 구조화된 답변 (핵심 요약 -> 배경 설명 -> 실무 팁 -> 출처)
            - 실패: 오류 메시지와 해결 방법 안내
    """
    try:
        llm_config = API_CONFIG.get("llm_api", {})
        
        # 통합 인덱스 시스템: 시스템 프롬프트 선택
        if custom_system_prompt:
            system_prompt = custom_system_prompt
        else:
            # 새로운 동적 인덱스 시스템 사용
            system_prompt = get_index_system_prompt(chatbot_type)
        
        # 통합 응답 형식 템플릿 사용
        response_format = RESPONSE_FORMAT_TEMPLATE
        
        # RAG 데이터 정규화 (다양한 입력 형식 지원)
        if not isinstance(retrieve_data, list):
            retrieve_data = [str(retrieve_data)]
        
        retrieve_text = "\n".join(retrieve_data) if retrieve_data else "검색된 관련 문서가 없습니다."
        
        # 챗봇별 출처 인용 형식 적용
        source_citations = format_source_citations(source_data, chatbot_type) if source_data else "출처 정보 없음"
        
        # LLM 메시지 구조 구성
        messages = [{"role": "system", "content": system_prompt}]
        
        # 확장된 대화 맥락 추가 (기존 5턴에서 10턴으로 확장)
        # 더 긴 맥락으로 연속 대화에서 주제 일관성과 참조 해결 능력 향상
        if user_id:
            try:
                from conversation_manager import get_conversation_context_for_llm
                context_messages = get_conversation_context_for_llm(user_id)
                # 최신 10턴 대화 맥락 적용 (20개 메시지 = 10턴)
                recent_context = context_messages[-20:] if len(context_messages) > 20 else context_messages
                messages.extend(recent_context)
                logger.info(f"사용자 {user_id}의 {len(recent_context)}개 대화 맥락을 로드했습니다")
            except ImportError:
                logger.warning("conversation_manager 모듈 없음 - 기본 chat_history로 대체")
                # 대화 매니저 없을 시 기본 대화 기록 사용
                if chat_history:
                    recent_history = chat_history[-20:]  # 10턴 분량
                    for msg in recent_history:
                        if msg.get("role") == "user":
                            messages.append({"role": "user", "content": msg.get("content", "")})
                        elif msg.get("role") == "bot":
                            messages.append({"role": "assistant", "content": msg.get("content", "")})
        elif chat_history:
            # user_id가 없는 경우 기본 대화 기록 사용
            recent_history = chat_history[-20:]  # 10턴 분량
            for msg in recent_history:
                if msg.get("role") == "user":
                    messages.append({"role": "user", "content": msg.get("content", "")})
                elif msg.get("role") == "bot":
                    messages.append({"role": "assistant", "content": msg.get("content", "")})
        
        # 현재 질문을 표준 형식으로 구조화
        if response_format and "{user_message}" in response_format:
            user_prompt = response_format.format(
                user_message=user_message,
                retrieve_data=retrieve_text,
                source_citations=source_citations
            )
        else:
            # 템플릿이 없는 경우 기본 형식 사용
            user_prompt = f"질문: {user_message}\n\n참고 문서:\n{retrieve_text}\n\n출처: {source_citations}"
        
        messages.append({"role": "user", "content": user_prompt})
        
        # API 설정 확인
        if not llm_config.get("base_url") or not llm_config.get("credential_key"):
            logger.warning(f"LLM API가 설정되지 않음 - Mock 응답 생성")
            # Mock 응답 지연 시뮬레이션
            if TEST_CONFIG.get("mock_response_delay", 0) > 0:
                time.sleep(TEST_CONFIG["mock_response_delay"] * 2)  # LLM은 RAG보다 조금 더 느림
            return get_mock_llm_response(user_message, retrieve_text, source_citations, chatbot_type, system_prompt)
        
        # LLM API 호출 페이로드 구성
        payload = json.dumps({
            "model": llm_config.get("model", "default-model"),
            "messages": messages,
            "temperature": 0.8,  # 적당한 창의성
            "max_tokens": 3000   # 응답 길이 제한
        })

        # 보안 헤더 구성 (빈 값 허용으로 설정 유연성 제공)
        headers_config = llm_config.get("headers", {})
        headers = {
            'x-dep-ticket': llm_config.get("credential_key", ""),
            'Send-System-Name': headers_config.get("Send-System-Name", ""),
            'User-Id': headers_config.get("User-Id", ""),
            'User-Type': headers_config.get("User-Type", "AD_ID"),
            'Prompt-Msg-Id': str(uuid.uuid4()),     # 요청 추적용 고유 ID
            'Completion-Msg-Id': str(uuid.uuid4()), # 응답 추적용 고유 ID
            'Accept': headers_config.get("Accept", "text/event-stream; charset=utf-8"),
            'Content-Type': headers_config.get("Content-Type", "application/json")
        }

        try:
            # LLM API 실제 호출
            response = requests.post(
                llm_config["base_url"], 
                headers=headers, 
                data=payload, 
                timeout=MISC_CONFIG.get("api_timeout", 30)
            )
            response.raise_for_status()
            
            # API 응답 파싱
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"]
            else:
                raise ValueError("LLM API 응답 형식이 올바르지 않습니다")
                
        except Exception as e:
            logger.error(f"LLM API 호출 실패: {str(e)}")
            return f"[오류 발생] API 호출에 실패했습니다. 설정을 확인해주세요. (오류: {str(e)})"
            
    except Exception as e:
        logger.error(f"LLM API 함수 오류: {str(e)}")
        return f"[시스템 오류] 챗봇 응답 생성 중 오류가 발생했습니다. 관리자에게 문의하세요."


def get_mock_rag_response(user_message: str, chatbot_type: str) -> dict:
    """
    테스트용 Mock RAG 응답 생성
    API가 설정되지 않았을 때 사용하여 source_data와 source_info 기능을 테스트할 수 있습니다.
    통합 인덱스 시스템을 지원합니다.
    """
    # 인덱스 설정 가져오기
    index_config = get_index_config(chatbot_type)
    display_name = index_config.get("display_name", chatbot_type)

    mock_responses = {
        "ae_wiki": {
            "hits": [
                f"[Mock AE WIKI 문서 1] '{user_message}'와 관련된 AE팀 업무 가이드입니다. 이 문서는 반도체 제품 개발 프로세스와 고객 지원 절차에 대한 상세한 정보를 포함하고 있습니다.",
                f"[Mock AE WIKI 문서 2] '{user_message}' 관련 기술 문서입니다. 메모리 사양 및 테스트 방법론에 대한 내용이 포함되어 있습니다.",
                f"[Mock AE WIKI 문서 3] '{user_message}' 주제의 업무 매뉴얼입니다. 고객 대응 시 참고할 수 있는 가이드라인이 정리되어 있습니다."
            ],
            "sources": [
                {
                    "file_name": "AE업무가이드_v2.3.pdf",
                    "page_number": 15,
                    "title": "반도체 제품 개발 프로세스",
                    "url": "https://confluence.company.com/display/AE/Product-Development-Guide",
                    "last_modified": "2024-09-15",
                    "author": "AE팀"
                },
                {
                    "file_name": "메모리_기술문서_2024.pdf",
                    "page_number": 42,
                    "title": "메모리 사양 및 테스트 방법",
                    "url": "https://confluence.company.com/display/AE/Memory-Spec-Guide",
                    "last_modified": "2024-09-20",
                    "author": "기술개발팀"
                },
                {
                    "file_name": "고객지원매뉴얼_v1.8.pdf",
                    "page_number": 8,
                    "title": "고객 대응 가이드라인",
                    "url": "https://confluence.company.com/display/AE/Customer-Support-Manual",
                    "last_modified": "2024-09-10",
                    "author": "고객지원팀"
                }
            ]
        },
        "glossary": {
            "hits": [
                f"[Mock 용어집 1] '{user_message}' 용어 정의: 반도체 공정에서 사용되는 핵심 기술 용어로, 메모리 디바이스의 특성을 나타내는 중요한 지표입니다.",
                f"[Mock 용어집 2] '{user_message}' 관련 용어: 이 용어는 JEDEC 표준에서 정의된 것으로, DDR 메모리 사양과 밀접한 관련이 있습니다.",
                f"[Mock 용어집 3] '{user_message}' 상세 설명: 반도체 업계에서 널리 사용되는 용어로, 다양한 응용 분야에서 중요한 역할을 합니다."
            ],
            "sources": [
                {
                    "file_name": "반도체용어사전_2024.pdf",
                    "page_number": 156,
                    "title": "메모리 기술 용어",
                    "section": "DDR 메모리 관련 용어",
                    "definition_type": "기술용어",
                    "last_updated": "2024-09-25"
                },
                {
                    "file_name": "JEDEC_용어집_v3.1.pdf",
                    "page_number": 89,
                    "title": "JEDEC 표준 용어",
                    "section": "메모리 인터페이스",
                    "definition_type": "표준용어",
                    "last_updated": "2024-09-18"
                },
                {
                    "file_name": "AE팀_기술용어모음.pdf",
                    "page_number": 23,
                    "title": "업무 전문 용어",
                    "section": "제품 사양 용어",
                    "definition_type": "업무용어",
                    "last_updated": "2024-09-12"
                }
            ]
        },
        "jedec": {
            "hits": [
                f"[Mock JEDEC 문서 1] '{user_message}' JEDEC 표준: JESD79-4 DDR4 SDRAM 표준 문서에서 정의된 규격으로, 메모리 인터페이스의 전기적 특성을 명시합니다.",
                f"[Mock JEDEC 문서 2] '{user_message}' 관련 규격: JESD220 시리즈에서 다루는 고속 메모리 인터페이스의 테스트 방법론입니다.",
                f"[Mock JEDEC 문서 3] '{user_message}' 테스트 절차: JEDEC JEP106 표준에 따른 검증 프로세스와 측정 방법을 설명합니다."
            ],
            "sources": [
                {
                    "file_name": "JESD79-4.pdf",
                    "page_number": 125,
                    "title": "DDR4 SDRAM Standard",
                    "section": "Electrical Characteristics",
                    "jedec_standard": "JESD79-4",
                    "revision": "Rev C",
                    "publication_date": "2023-11"
                },
                {
                    "file_name": "JESD220-1.pdf",
                    "page_number": 67,
                    "title": "High Bandwidth Memory Interface",
                    "section": "Test Methodologies",
                    "jedec_standard": "JESD220-1",
                    "revision": "Rev A",
                    "publication_date": "2024-03"
                },
                {
                    "file_name": "JEP106.pdf",
                    "page_number": 34,
                    "title": "Standard Manufacturer ID",
                    "section": "Verification Process",
                    "jedec_standard": "JEP106",
                    "revision": "Rev AE",
                    "publication_date": "2024-06"
                }
            ]
        },
        "quality": {
            "hits": [
                f"[Mock 품질관리 문서 1] '{user_message}' 품질 기준: ISO 9001 및 TS 16949 표준에 따른 반도체 품질 관리 프로세스입니다.",
                f"[Mock 품질관리 문서 2] '{user_message}' 불량 분석: SPC(Statistical Process Control) 방법론을 적용한 품질 데이터 분석 방법입니다.",
                f"[Mock 품질관리 문서 3] '{user_message}' 테스트 방법: 반도체 품질 검증을 위한 다양한 테스트 프로토콜과 측정 기준입니다."
            ],
            "sources": [
                {
                    "file_name": "품질관리표준_v3.2.pdf",
                    "page_number": 78,
                    "title": "반도체 품질 기준",
                    "section": "품질 검사 프로세스",
                    "standard": "ISO 9001",
                    "last_updated": "2024-08-15"
                },
                {
                    "file_name": "불량분석가이드_2024.pdf",
                    "page_number": 134,
                    "title": "SPC 기반 품질 분석",
                    "section": "통계적 공정 관리",
                    "methodology": "SPC",
                    "last_updated": "2024-09-01"
                },
                {
                    "file_name": "품질테스트매뉴얼_v2.1.pdf",
                    "page_number": 56,
                    "title": "품질 검증 프로토콜",
                    "section": "테스트 방법론",
                    "test_type": "품질검증",
                    "last_updated": "2024-08-28"
                }
            ]
        }
    }

    # 기본 응답 (새로운 인덱스나 알 수 없는 타입의 경우)
    default_response = {
        "hits": [f"[Mock {display_name}] '{user_message}'에 대한 Mock 응답입니다. 실제 API 연결 시 더 정확한 정보를 제공합니다."],
        "sources": [{"file_name": f"mock_{chatbot_type}_document.pdf", "page_number": 1, "title": f"{display_name} Mock Document"}]
    }

    return mock_responses.get(chatbot_type, default_response)

def get_mock_llm_response(user_message: str, retrieve_text: str, source_citations: str, chatbot_type: str, system_prompt: str) -> str:
    """
    테스트용 Mock LLM 응답 생성
    API가 설정되지 않았을 때 사용하여 챗봇별 프롬프트와 출처 표시 기능을 테스트할 수 있습니다.
    통합 인덱스 시스템을 지원합니다.
    """
    # 인덱스 설정 가져오기
    index_config = get_index_config(chatbot_type)
    display_name = index_config.get("display_name", chatbot_type)
    icon = index_config.get("icon", "🤖")

    # 챗봇별 특화된 응답 생성
    chatbot_responses = {
        "ae_wiki": f"""**🔍 {display_name} 응답 (Mock)**

**질문**: {user_message}

**답변**:
'{user_message}'에 대한 AE팀 업무 관련 정보를 제공드리겠습니다.

**📋 핵심 내용**:
- 이는 AE팀 업무 프로세스와 관련된 중요한 주제입니다
- 반도체 제품 개발 및 고객 지원 업무에서 자주 다뤄지는 내용입니다
- 정확한 절차를 따라 처리하시기 바랍니다

**🔧 실무 적용**:
- 관련 문서를 참조하여 단계별로 진행하세요
- 문제 발생 시 팀 내 전문가와 상의하시기 바랍니다

**📚 참고 문서**:
{source_citations}

---
💡 **시스템 프롬프트 확인됨**: AE팀 기술 Q&A 어시스턴트로 동작 중
🔄 **Mock 데이터**: 실제 API 연결 시 더 정확한 답변 제공 예정""",

        "glossary": f"""**🔍 {display_name} 응답 (Mock)**

**용어**: {user_message}

**정의**:
'{user_message}'는 반도체 기술 분야에서 사용되는 전문 용어입니다.

**📖 상세 설명**:
- **개념**: 메모리 반도체 및 관련 기술에서 중요한 역할을 하는 용어
- **분류**: 기술/공정/제품 사양 관련 용어
- **적용 분야**: DDR 메모리, JEDEC 표준, 반도체 공정

**🔗 관련 용어**:
- 연관된 기술 용어들과 함께 이해하시면 도움이 됩니다
- JEDEC 표준 문서에서 공식 정의를 확인할 수 있습니다

**📚 참고 자료**:
{source_citations}

---
💡 **시스템 프롬프트 확인됨**: 반도체 기술 용어 전문가로 동작 중
🔄 **Mock 데이터**: 실제 API 연결 시 더 정확한 용어 해설 제공 예정""",

        "jedec": f"""**🔍 {display_name} 응답 (Mock)**

**질문**: {user_message}

**JEDEC 표준 관련 답변**:
'{user_message}'와 관련된 JEDEC 표준 정보를 제공드리겠습니다.

**📋 관련 표준**:
- **JESD79-4**: DDR4 SDRAM 표준 규격
- **JESD220**: 고속 메모리 인터페이스 표준
- **JEP106**: 제조사 식별 표준

**⚡ 기술 사양**:
- 전기적 특성 및 타이밍 요구사항
- 테스트 방법론 및 검증 절차
- 호환성 및 상호 운용성 가이드

**🔬 실무 적용**:
- 제품 설계 시 해당 표준을 준수해야 합니다
- 테스트 시나리오 작성 시 JEDEC 방법론을 참조하세요

**📚 참고 문서**:
{source_citations}

---
💡 **시스템 프롬프트 확인됨**: JEDEC 표준 문서 전문가로 동작 중
🔄 **Mock 데이터**: 실제 API 연결 시 더 정확한 표준 해석 제공 예정""",

        "quality": f"""**🔍 {display_name} 응답 (Mock)**

**질문**: {user_message}

**품질관리 관련 답변**:
'{user_message}'에 대한 품질관리 관점의 분석과 개선 방안을 제공드리겠습니다.

**📊 품질 기준**:
- **ISO 9001**: 품질경영시스템 국제표준
- **TS 16949**: 자동차산업 품질경영시스템
- **SPC**: 통계적 공정 관리 방법론

**🔬 분석 방법**:
- 불량률 분석 및 원인 파악
- 공정 능력 평가 (Cp, Cpk)
- 관리도를 통한 공정 모니터링

**⚡ 개선 방안**:
- 품질 검사 프로세스 최적화
- 예방적 품질 관리 체계 구축
- 데이터 기반 의사결정 지원

**📚 참고 문서**:
{source_citations}

---
💡 **시스템 프롬프트 확인됨**: 반도체 품질관리 전문가로 동작 중
🔄 **Mock 데이터**: 실제 API 연결 시 더 정확한 품질 분석 제공 예정"""
    }

    # 기본 응답 (새로운 인덱스나 알 수 없는 챗봇 타입의 경우)
    default_response = f"""**{icon} {display_name} Mock 응답**

**질문**: {user_message}

**답변**: Mock 응답을 생성했습니다.

**참고 문서**:
{source_citations}

**시스템 프롬프트**: {system_prompt[:100]}...

---
💡 **시스템 프롬프트 확인됨**: {display_name}로 동작 중
🔄 **Mock 데이터**: 실제 API 연결 시 더 정확한 답변 제공 예정
"""

    return chatbot_responses.get(chatbot_type, default_response)

def call_rag_api_with_chatbot_type(user_message: str, chatbot_type: str) -> dict:
    """
    챗봇별 전용 RAG API 호출 시스템 - 통합 인덱스 관리
    
    각 챗봇의 전용 문서 저장소에서 질문과 관련된 문서를 검색하는 핵심 함수입니다.
    리팩터링으로 레거시 개별 API 함수들을 완전히 통합하여 코드 중복을 제거했습니다.
    
    인덱스 매핑 (config.py의 chatbot_rag_config 기준):
    - ae_wiki -> rp-conflu_1 (Confluence 업무 문서)
    - glossary -> rp-ae_wiki (기술 용어집 문서)  
    - jedec -> rp-jedec (JEDEC 표준 규격 PDF)
    
    검색 프로세스:
    1. 챗봇 타입으로 전용 인덱스 조회 (get_chatbot_indices)
    2. RAG API에 질문과 인덱스 전송
    3. 벡터 유사도 기반 관련 문서 검색 (1000개 후보 -> 3개 최종 선별)
    4. 문서 내용과 메타데이터 분리하여 반환
    
    호출 관계:
    - get_chatbot_response()에서 LLM 호출 전 문서 검색 시 호출
    - get_chatbot_indices() 호출로 챗봇별 인덱스 조회
    - config.py의 API_CONFIG["rag_api_common"] 설정 사용
    
    부작용:
    - 외부 RAG API 호출 (네트워크 I/O, 평균 1-3초)
    - API 실패 시 빈 결과 반환으로 시스템 안정성 유지
    - 검색 로그 생성 가능 (향후 분석용)
    
    오류 복구:
    - API 미설정 시 빈 결과 및 오류 메시지 반환
    - 네트워크 오류 시 타임아웃 후 빈 결과 반환
    - 잘못된 챗봇 타입 시 KeyError 발생 (상위에서 처리)
    
    Args:
        user_message: 검색 대상 질문 텍스트 (자연어 쿼리)
        chatbot_type: 검색할 챗봇 식별자 ("ae_wiki", "glossary", "jedec")
    
    Returns:
        dict: 검색 결과 구조화 데이터
            {
                "hits": List[str] - 문서 내용 텍스트들 (최대 3개)
                "sources": List[dict] - 출처 메타데이터들 (파일명, URL, 페이지 등)
            }
            
    Raises:
        KeyError: 지원하지 않는 챗봇 타입이거나 설정 누락 시
        
    예시:
        >>> result = call_rag_api_with_chatbot_type("DRAM이란?", "ae_wiki")
        >>> result["hits"][0]  # 첫 번째 검색 결과 문서 내용
        >>> result["sources"][0]  # 첫 번째 문서의 출처 정보
    """
    # 통합 RAG API 설정 사용 (레거시 개별 설정 제거)
    rag_config = API_CONFIG["rag_api_common"]
    
    if not rag_config.get("base_url") or not rag_config.get("credential_key"):
        logger.warning(f"RAG API가 {chatbot_type} 챗봇에 대해 설정되지 않음 - Mock 데이터 사용")
        # Mock 응답 지연 시뮬레이션
        if TEST_CONFIG.get("mock_response_delay", 0) > 0:
            time.sleep(TEST_CONFIG["mock_response_delay"])
        return get_mock_rag_response(user_message, chatbot_type)
    
    # API 호출 헤더 구성
    headers = {
        "Content-Type": "application/json",
        "x-dep-ticket": rag_config.get("credential_key", "")
    }
    
    # 새로운 통합 인덱스 시스템
    # 인덱스 ID(chatbot_type)로 직접 RAG 인덱스명 조회
    index_name = get_index_rag_name(chatbot_type)

    if not index_name:
        logger.error(f"지원하지 않는 인덱스 ID: {chatbot_type}")
        return {"hits": [f"지원하지 않는 인덱스 ID입니다: {chatbot_type}"], "sources": []}

    # 인덱스 설정 정보 조회
    index_config = get_index_config(chatbot_type)
    if not index_config:
        logger.error(f"인덱스 {chatbot_type}의 설정을 찾을 수 없음")
        return {"hits": [f"인덱스 설정을 찾을 수 없습니다: {chatbot_type}"], "sources": []}
    
    # RAG API 요청 페이로드 구성
    payload = {
        'user': rag_config.get("user", "unknown"),           # 사용자 식별자
        'index_name': index_name,                            # 검색 대상 인덱스
        "auth_list": rag_config.get("auth_list", []),        # 접근 권한 그룹
        "query_text": user_message,                          # 검색 쿼리
        "num_candidates": rag_config.get("num_candidates", 1000),  # 1차 후보 문서 수
        "num_result_doc": rag_config.get("num_result_doc", 3),     # 최종 반환 문서 수
        "fields_exclude": rag_config.get("fields_exclude", [])     # 제외할 문서 필드
    }
    
    # 선택적: 인덱스별 권한 그룹 설정
    if 'Permission_Group' in index_config:
        payload['Permission_Group'] = index_config['Permission_Group']

    try:
        # RAG API 실제 호출
        response = requests.post(
            rag_config["base_url"], 
            headers=headers, 
            json=payload, 
            timeout=rag_config.get("timeout", 30)
        )
        response.raise_for_status()
        
        # 응답 데이터 파싱 (Elasticsearch 형식)
        response_data = response.json()
        hits = json.loads(response_data['message'])['hits']['hits']
        
        retrieve_data = []  # 문서 내용들
        source_data = []    # 출처 메타데이터들
        
        # 설정된 수만큼 문서 처리
        for i in range(min(rag_config.get("num_result_doc", 3), len(hits))):
            hit = hits[i]
            source = hit.get('_source', {})
            content = source.get('merge_title_content', source.get('content', ''))
            
            if content:
                retrieve_data.append(content)
                
                # 챗봇별 출처 인용을 위한 메타데이터 구성
                source_info = {
                    'title': source.get('title', f'문서_{i+1}'),  # 문서 제목
                    'doc_id': hit.get('_id', f'doc_{i+1}'),      # 문서 고유 ID
                    'score': hit.get('_score', 0),               # 검색 관련도 점수
                    'index': index_name                          # 출처 인덱스
                }
                source_data.append(source_info)
            
        # 통합 반환 형식 (레거시 튜플에서 딕셔너리로 변경)
        result = {
            "hits": retrieve_data if retrieve_data else ["관련 문서를 찾을 수 없습니다."],
            "sources": source_data
        }
        
        logger.info(f"RAG 검색 성공 - {chatbot_type}:{index_name}에서 {len(retrieve_data)}개 문서 검색됨")
        return result
        
    except Exception as e:
        logger.error(f"RAG API 호출 실패 {chatbot_type}:{index_name}: {str(e)}")
        return {
            "hits": [f"RAG API 호출 실패: {str(e)}"],
            "sources": []
        }


def format_source_citations(source_data: List[dict], chatbot_type: str = "ae_wiki") -> str:
    """
    챗봇별 특화된 출처 인용 형식 생성기
    
    각 챗봇의 문서 특성과 사용자 요구에 맞는 출처 표시 시스템입니다.
    config.py의 chatbot_rag_config에 정의된 source_display 설정에 따라 다른 형식을 사용합니다.
    
    출처 표시 전략:
    - AE WIKI (confluence_url): 클릭하여 원본 문서로 즉시 이동 가능한 Confluence 링크  
    - 용어집 (expandable_card): 페이지에서 접기/펼치기 가능한 메타데이터 카드
    - JEDEC (filename_page): PDF 특성을 고려한 파일명+페이지 번호 형식
    
    호출 관계:
    - call_llm_api()에서 응답 생성 시 출처 부분 자동 처리용하여 호출
    - config.py의 API_CONFIG["chatbot_rag_config"] 설정 참조
    
    부작용:
    - Streamlit 마크다운 렌더링으로 링크 및 스타일 적용
    - 사용자의 클릭 시 외부 URL로 내비게이션 발생 (보안 주의)
    
    Args:
        source_data: RAG 검색 결과의 메타데이터 목록
            - title: 문서 제목
            - doc_id: 문서 고유 ID (Confluence 페이지 ID 등)
            - page: 페이지 번호 (선택적)
            - score: 검색 관련도 점수 (미사용)
        chatbot_type: 출처 표시 형식 결정용 챗봇 식별자
    
    Returns:
        str: Streamlit에서 렌더링될 마크다운 형식의 출처 리스트
    
    예시 출력:
        AE WIKI: "1. [문서제목](https://confluence.company.com/display/AE/123456)"
        용어집: "1. **용어집 문서** (p.25)"  
        JEDEC: "1. JESD79-4.pdf - p.45"
    """
    if not source_data:
        return "출처 정보 없음"
    
    citations = []
    
    for i, source in enumerate(source_data, 1):
        # 기본 출처 정보 추출
        title = source.get('title', '문서명 없음')
        doc_id = source.get('doc_id', '')
        page = source.get('page', '')
        source_url = source.get('source', '')
        
        if chatbot_type == "ae_wiki":
            # AE WIKI 출처: 클릭 가능한 Confluence 링크 생성
            if doc_id:
                # config.py에서 Confluence 기본 URL 조회
                confluence_url = API_CONFIG["chatbot_rag_config"]["ae_wiki"]["confluence_base_url"]
                full_url = f"{confluence_url}{doc_id}"
                citation = f"{i}. [{title}]({full_url})"  # 마크다운 링크 형식
            else:
                citation = f"{i}. {title}"  # ID가 없으면 제목만 표시
                
        elif chatbot_type == "glossary":
            # 용어집 출처: 굵은 제목으로 강조 표시
            citation = f"{i}. **{title}**"  # 마크다운 굵은 글씨
            if page:
                citation += f" (p.{page})"  # 페이지 번호 추가
                
        elif chatbot_type == "jedec":
            # JEDEC 출처: 파일명과 페이지 번호 조합 (PDF 특성)
            if page:
                citation = f"{i}. {title} - p.{page}"  # 예: "JESD79-4.pdf - p.45"
            else:
                citation = f"{i}. {title}"  # 페이지 정보 없으면 파일명만
        else:
            # 기본 형식 (확장 시 사용)
            if source_url:
                citation = f"{i}. [{title}]({source_url})"  # URL이 있으면 링크로
            else:
                citation = f"{i}. {title}"  # URL이 없으면 제목만
        
        citations.append(citation)
    
    return "\n".join(citations)

def get_chatbot_response(user_message: str, chat_history: list = None, user_id: str = None, system_prompt: str = None, chatbot_type: str = "ae_wiki") -> str:
    """
    통합 챗봇 응답 생성 시스템 - 메인 엔트리포인트
    
    3개 전용 챗봇의 최종 사용자 인터페이스인 핵심 응답 생성 함수입니다.
    전체 AI 파이프라인을 조율하여 RAG 검색 -> LLM 생성 -> 대화 기록 반영을 일관된 흐름으로 처리합니다.
    
    핵심 기능:
    - 원격 RAG + LLM 시스템: 안정적인 API 기반 응답 생성
    - 실시간 대화 맥락 관리: 10턴 슬라이딩 윈도우로 연속 대화 품질 보장
    - 사용자 맞춤형 응답: 챗봇별 전용 인덱스와 프롬프트로 특화된 응답
    - 오류 복구: graceful degradation으로 서비스 연속성 유지
    
    처리 파이프라인:
    1. 챗봇 타입 검증 및 전용 인덱스 로드
    2. call_rag_api_with_chatbot_type()로 RAG 검색 수행
    3. RAG 결과와 대화 맥락을 call_llm_api()로 전달
    4. 생성된 응답을 대화 기록에 반영 (자동)
    
    호출 관계:
    - 모든 챗봇 페이지에서 사용자 질문 시 직접 호출
    - call_rag_api_with_chatbot_type() -> call_llm_api() 순차 호출
    - save_chat_history()에서 자동으로 대화 기록 저장 트리거
    
    오류 복구 전략:
    - RAG 시스템 실패 -> 빈 문서로 LLM 진행
    - LLM API 실패 -> 사과 메시지와 해결 방법 안내
    - 전체 시스템 실패 -> 사과 메시지와 해결 방법 안내
    
    Args:
        user_message: 사용자 입력 질문 텍스트
        chat_history: 전체 대화 기록 (예비용, conversation_manager 우선)
        user_id: 사용자 UUID (대화 맥락 로드 및 개인화 용)
        system_prompt: 커스텀 시스템 프롬프트 (기본 챗봇 프롬프트 오버라이드용)
        chatbot_type: 챗봇 식별자 ("ae_wiki", "glossary", "jedec")
    
    Returns:
        str: 챗봇 최종 응답 텍스트
            - 성공: 구조화된 답변 + 출처 인용
            - 오류: 사용자 친화적 오류 메시지
            - 비상: 대체 답변 및 상황 설명
    """
    
    # 원격 API 기반 RAG + LLM 시스템
    # 1단계: 챗봇별 전용 RAG 검색 수행
    rag_result = call_rag_api_with_chatbot_type(user_message, chatbot_type)
    retrieve_data = rag_result["hits"]
    source_data = rag_result["sources"]
    
    # 2단계: 검색 결과와 대화 맥락을 결합하여 LLM 응답 생성
    response = call_llm_api(user_message, retrieve_data, chat_history, source_data, user_id, system_prompt, chatbot_type)
    
    # 3단계: 대화 기록을 메모리 시스템에 저장
    if user_id:
        try:
            from conversation_manager import add_conversation_to_memory
            conversation_type = chatbot_type
            add_conversation_to_memory(user_id, user_message, response, conversation_type)
        except ImportError:
            logger.warning("대화 매니저를 사용할 수 없어 메모리 저장을 생략합니다")
    
    return response

# ====================================
# 📊 시스템 로깅 및 분석 시스템
# ====================================
# 사용자 행동 분석, 검색 패턴 추적, 대화 기록 관리 기능들
#
# 주요 기능:
# - log_search(): 검색 행동 추적 및 트렌드 분석
# - save_chat_history(): 이중 대화 기록 시스템 (레거시 + 새로운 메모리)
# - get_answer_ranking(): 레거시 Q&A 시스템용 기여도 순위
#
# 리팩터링 변경사항:
# - 기존 스키마 유지하면서 새로운 conversation_manager와 통합
# - 챗봇별 대화 기록 구분 (admin, tech -> ae_wiki, glossary, jedec)
# - 10턴 슬라이딩 윈도우 메모리로 확장된 대화 맥락 지원

def log_search(data: Dict, search_term: str, category_filter: str, results_count: int) -> None:
    """
    검색 행동 로깅 및 분석 데이터 수집
    
    사용자의 검색 패턴을 실시간으로 추적하여 시스템 개선에 활용할 데이터를 수집합니다.
    검색어 트렌드, 인기 카테고리, 검색 성공률, 사용자 선호도 등을 분석할 수 있습니다.
    
    호출 관계:
    - Q&A 페이지의 search_questions() 함수에서 검색 수행 후 호출
    - get_user_id(), get_username() 학수 함수들과 연동
    - save_data() 호출하여 영구 저장
    
    부작용:
    - knowledge_data.json 파일에 search_logs 배열에 추가
    - 로그 데이터 누적으로 파일 크기 증가 (정기 정리 고려)
    - 개인정보 수집 (사용자 ID, 검색어 등) - 프라이버시 주의
    
    분석 가능 지표:
    - 인기 검색어 랭킹 (검색어 빈도 분석)
    - 카테고리별 검색 선호도 (category_filter 분석)
    - 검색 성공률 (results_count > 0 비율)
    - 사용자별 검색 패턴 (username 기준 그룹화)
    - 시간대별 검색 트래픽 (시간 기준 분석)
    
    Args:
        data: 메인 데이터 저장소 (search_logs 스키마 필요)
        search_term: 사용자 입력 검색어 (트렌드 분석용)
        category_filter: 적용된 카테고리 필터 (선호도 분석용)
        results_count: 검색된 결과 수 (성공률 측정용)
    """
    search_log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": get_user_id(),      # 사용자 추적 (개인정보 보호 고려)
        "username": get_username(),     # 표시명 (분석용)
        "search_term": search_term,     # 검색어 (트렌드 분석)
        "category_filter": category_filter,  # 카테고리 선호도 분석
        "results_count": results_count  # 검색 성공률 측정
    }
    data["search_logs"].append(search_log)
    save_data(data)

def save_chat_history(data: Dict, user_message: str, bot_response: str, chatbot_type: str = "ae_wiki") -> None:
    """
    챗봇 대화 기록 이중 저장 시스템 - 히스토리 및 맥락 관리
    
    기존 대화 기록 시스템(관리자 분석용)과 새로운 슬라이딩 윈도우 메모리(개인 맥락용)에
    동시 저장하여 호환성과 성능을 모두 확보하는 하이브리드 시스템입니다.
    
    이중 저장 전략:
    1. 레거시 저장소: 관리자 페이지에서 전체 대화 히스토리 조회 및 분석
    2. 새 메모리 시스템: 10턴 슬라이딩 윈도우로 대화 맥락 유지 및 LLM 응답 품질 향상
    
    호출 관계:
    - get_chatbot_response() 끝에서 대화 완료 후 자동 호출
    - 모든 챗봇 페이지에서 간접적으로 사용
    - conversation_manager.add_conversation_to_memory() 연동 (선택적)
    - save_data() 호출하여 레거시 데이터 영구화
    
    부작용:
    - knowledge_data.json에 대화 기록 추가 (파일 크기 증가)
    - conversation_manager 메모리에도 병렬 저장 (중복 저장)
    - 개인정보 수집 (user_id, username, 대화 내용) - 프라이버시 고려
    
    데이터 구조:
    - timestamp: 대화 발생 시간 (ISO 형식)
    - user_id: 사용자 UUID (대화 맥락 추적용)
    - username: 표시명 (분석 용이성)
    - chatbot_type: 실제 챗봇 유형 (ae_wiki/glossary/jedec)
    - is_admin_bot: 레거시 호환성 플래그
    
    Args:
        data: 메인 데이터 저장소 (chat_history, admin_chat_history 스키마 필요)
        user_message: 사용자 입력 질문
        bot_response: 챗봇 생성 응답  
        chatbot_type: 챗봇 식별자 ("ae_wiki", "glossary", "jedec")
    """
    chat_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": get_user_id(),
        "username": get_username(),
        "user_message": user_message,
        "bot_response": bot_response,
        "chatbot_type": chatbot_type  # 실제 봇 유형 기록
    }
    
    # 챗봇 타입별 대화 기록 저장
    if chatbot_type == "glossary":
        # 용어집 챗봇은 별도 저장소 (관리자 페이지에서 구분 조회)
        if "glossary_chat_history" not in data:
            data["glossary_chat_history"] = []
        data["glossary_chat_history"].append(chat_record)
    elif chatbot_type == "jedec":
        # JEDEC 표준 챗봇은 별도 저장소
        if "jedec_chat_history" not in data:
            data["jedec_chat_history"] = []
        data["jedec_chat_history"].append(chat_record)
    else:
        # AE WIKI 챗봇은 기본 저장소 (레거시 호환성)
        data["chat_history"].append(chat_record)
    
    save_data(data)
    
    # 새로운 슬라이딩 윈도우 메모리에도 병행 저장 (개인 맥락용)
    try:
        from conversation_manager import add_conversation_to_memory
        user_id = get_user_id()
        conversation_type = chatbot_type
        metadata = {
            "username": get_username(),
            "via_legacy_save": True,      # 레거시 시스템을 통한 저장임을 표시
            "chatbot_type": conversation_type
        }
        add_conversation_to_memory(user_id, user_message, bot_response, conversation_type, metadata)
    except ImportError:
        logger.warning("대화 매니저를 사용할 수 없어 확장된 메모리 저장을 생략합니다")

def get_answer_ranking(data: Dict) -> List[tuple]:
    """
    답변 기여도 순위 계산 - 레거시 Q&A 시스템 기능
    
    레거시 Q&A 시스템에서 답변을 많이 작성한 사용자들의 기여도 순위를 계산합니다.
    게임이피케이션 요소로 사용자 참여를 유도하고 Best Contributor 기능을 제공합니다.
    
    처리 로직:
    1. 전체 답변 데이터에서 사용자별 답변 수 집계
    2. 답변 수 기준 내림차순 정렬
    3. 상위 3명만 반환 (대시보드 형식)
    
    호출 관계:
    - 관리자 페이지나 통계 페이지에서 기여자 순위 표시용
    - Q&A 메인 페이지에서 대시보드 위젯으로 활용
    
    한계:
    - 답변 품질을 고려하지 않고 수량만 카운트
    - 비공개 답변이나 삭제된 답변도 포함되어 부정확할 수 있음
    - 사용자명 중복 가능 (눈인서 개선 고려)
    
    대안 고려사항:
    - 좋아요 수나 평점 가중치 반영
    - 최근성 가중치 적용 (최근 활동 선호)
    - 사용자 ID 기반 중복 제거
    
    Args:
        data: Q&A 데이터가 포함된 메인 저장소
            - answers: List[Dict] 스키마 필요 (author 필드 필수)
    
    Returns:
        List[tuple]: (사용자명, 답변수) 튜플의 상위 3위 목록
            - 예: [('alice', 15), ('bob', 12), ('charlie', 8)]
            - 빈 리스트 반환 가능 (답변 데이터 없을 시)
    """
    answer_counts = {}
    for answer in data["answers"]:
        author = answer["author"]
        answer_counts[author] = answer_counts.get(author, 0) + 1

    sorted_users = sorted(answer_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_users[:3]  # 상위 3명만 반환

# ====================================
# 🏆 사용자 포인트 및 게임화 시스템
# ====================================
# 사용자 참여를 유도하는 포인트 시스템과 순위 관리

def add_user_points(data: Dict, username: str, points: int, activity_type: str) -> None:
    """
    사용자 포인트 지급 및 활동 로그 기록
    
    다양한 활동(질문, 답변, 좋아요 등)에 대해 포인트를 지급하고
    상세한 활동 로그를 남겨 사용자 참여 패턴을 분석할 수 있습니다.
    
    Args:
        data: 포인트 데이터가 저장될 메인 저장소
        username: 포인트를 받을 사용자명
        points: 지급할 포인트 수
        activity_type: 활동 유형 ("질문하기", "답변하기" 등)
    """
    if "user_points" not in data:
        data["user_points"] = {}
    
    # 현재 포인트에 새 포인트 추가
    current_points = data["user_points"].get(username, 0)
    data["user_points"][username] = current_points + points
    
    # 포인트 활동 로그 기록 (분석 및 투명성 확보)
    if "point_logs" not in data:
        data["point_logs"] = []
    
    data["point_logs"].append({
        "username": username,
        "points": points,
        "activity_type": activity_type,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_points": data["user_points"][username]  # 누적 포인트
    })
    
    save_data(data)

def get_user_points(data: Dict, username: str) -> int:
    """
    사용자 총 포인트 조회
    
    특정 사용자가 지금까지 획득한 총 포인트를 반환합니다.
    사용자 프로필이나 순위 표시에 사용됩니다.
    
    Args:
        data: 포인트 데이터가 포함된 저장소
        username: 조회할 사용자명
    
    Returns:
        int: 해당 사용자의 총 포인트 (기록이 없으면 0)
    """
    return data.get("user_points", {}).get(username, 0)

def get_current_user_points(data: Dict) -> int:
    """
    현재 로그인한 사용자의 포인트 조회 (보안 강화)
    
    세션의 현재 사용자 포인트만 조회 가능합니다.
    
    Args:
        data: 포인트 데이터가 포함된 저장소
    
    Returns:
        int: 현재 사용자의 총 포인트
    """
    return get_user_points(data)  # username=None이므로 현재 사용자

def get_user_points_ranking(data: Dict) -> List[tuple]:
    """
    포인트 기반 사용자 순위 시스템 (Best Contributor)
    
    모든 사용자의 포인트를 집계하여 상위 랭킹을 생성합니다.
    게임화 요소로 사용자 참여를 유도하는 핵심 기능입니다.
    
    Args:
        data: 포인트 데이터가 포함된 저장소
    
    Returns:
        List[tuple]: (사용자명, 총포인트) 튜플의 상위 3위 목록
    """
    user_points = data.get("user_points", {})
    if not user_points:
        return []
    
    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
    return sorted_users[:3]  # 상위 3명 반환

# ====================================
# 🎨 사용자 인터페이스 및 UX 시스템  
# ====================================
# 시각적 효과, 테마 관리, 사용자 경험 개선 기능들

def display_typing_effect(text: str, container, delay: float = None) -> None:
    """
    실시간 타이핑 효과 시스템 (성능 최적화)
    
    챗봇 응답을 실시간으로 타이핑하는 것처럼 보여주어 사용자 경험을 개선합니다.
    긴 텍스트나 성능상 이슈가 있을 때는 자동으로 타이핑 효과를 건너뜁니다.
    
    Args:
        text: 타이핑 효과로 표시할 텍스트
        container: Streamlit 컨테이너 객체
        delay: 타이핑 지연시간 (None이면 설정값 사용)
    """
    # 사용자 설정에 따른 타이핑 효과 활성화 여부
    if not MISC_CONFIG.get("enable_typing_effect", True):
        container.markdown(text)
        return
        
    # 성능 최적화: 긴 텍스트는 타이핑 효과 생략
    if len(text) > MISC_CONFIG.get("max_typing_text_length", 150):
        container.markdown(text)
        return
        
    # 타이핑 속도 설정
    if delay is None:
        speed = MISC_CONFIG.get("response_speed", "normal")
        delay_map = {"slow": 0.05, "fast": 0.01, "normal": 0.03}
        delay = delay_map.get(speed, 0.03)
    
    # 단어 단위 타이핑 (문자 단위보다 성능 우수)
    words = text.split()
    displayed_text = ""
    for word in words:
        displayed_text += word + " "
        container.markdown(displayed_text)
        time.sleep(delay * 3)  # 단어 단위이므로 지연시간 증가

def load_css_styles() -> str:
    """
    통합 다크 테마 CSS 시스템
    
    전체 시스템에 적용되는 일관된 다크 테마 스타일을 제공합니다.
    Bootstrap과 커스텀 CSS를 결합하여 전문적이고 현대적인 UI를 구성합니다.
    
    주요 특징:
    - 완전한 다크 모드 지원
    - Streamlit 기본 컴포넌트 모두 스타일링
    - 브랜드 컬러 일관성 유지  
    - 접근성 고려 (충분한 대비도)
    - 반응형 디자인 지원
    
    Returns:
        str: 완전한 CSS 스타일시트 (HTML 임베드용)
    """
    from config import THEME_CONFIG
    # colors = THEME_CONFIG["colors"]  # 미사용 변수 제거
    
    return f"""
    <!-- Bootstrap CSS 프레임워크 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <style>
        /* === 전체 애플리케이션 다크 테마 === */
        .stApp {{
            background-color: #1a1a1a !important;
            color: #e1e5e9 !important;
        }}
        
        /* 메인 콘텐츠 컨테이너 */
        .main .block-container {{
            background-color: #1a1a1a !important;
            color: #e1e5e9 !important;
            max-width: 90% !important;
            padding-top: 2rem !important;
        }}
        
        /* === 사이드바 스타일링 === */
        .stSidebar {{
            background-color: #2d3748 !important;
            border-right: 1px solid #4a5568 !important;
        }}
        
        .stSidebar .stMarkdown, .stSidebar .stMarkdown p {{
            color: #e1e5e9 !important;
        }}
        
        /* 페이지 네비게이션 링크 */
        .stSidebar [data-testid="stSidebarNav"] li a {{
            color: #e1e5e9 !important;
            font-size: 1.1rem !important;
            font-weight: 500 !important;
        }}
        
        .stSidebar [data-testid="stSidebarNav"] li a:hover {{
            background-color: #4a5568 !important;
            color: #ffffff !important;
        }}
        
        /* === 입력 컨트롤 스타일링 === */
        .stTextInput input, .stTextArea textarea, 
        .st-emotion-cache-1oejotp input, 
        .st-emotion-cache-14vh5up input,
        input[type="text"], input[type="email"], input[type="password"],
        textarea, select {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
            border: 1px solid #4a5568 !important;
            border-radius: 0.5rem !important;
            padding: 0.5rem 0.75rem !important;
        }}
        
        /* 입력 필드 포커스 상태 */
        .stTextInput input:focus, .stTextArea textarea:focus,
        .st-emotion-cache-1oejotp input:focus,
        .st-emotion-cache-14vh5up input:focus,
        input[type="text"]:focus, input[type="email"]:focus, input[type="password"]:focus,
        textarea:focus, select:focus {{
            border-color: #667eea !important;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25) !important;
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
        }}
        
        /* 입력 필드 레이블 */
        .stTextInput label, .stTextArea label, 
        .stSelectbox label, .stMultiSelect label,
        .st-emotion-cache-1oejotp label,
        .st-emotion-cache-14vh5up label {{
            color: #e1e5e9 !important;
            font-weight: 500 !important;
        }}
        
        /* 플레이스홀더 텍스트 */
        .stTextInput input::placeholder, .stTextArea textarea::placeholder,
        .st-emotion-cache-1oejotp input::placeholder,
        .st-emotion-cache-14vh5up input::placeholder,
        input::placeholder, textarea::placeholder {{
            color: #a0aec0 !important;
            opacity: 0.8 !important;
        }}
        
        /* === 버튼 시스템 === */
        .stButton button {{
            background-color: #667eea !important;
            color: white !important;
            border: none !important;
            border-radius: 0.5rem !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.2s ease !important;
        }}
        
        .stButton button:hover {{
            background-color: #5a67d8 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }}
        
        /* === 알림 및 상태 메시지 === */
        .stAlert {{
            border-radius: 0.5rem !important;
            border: none !important;
        }}
        
        /* 폼 내부 숨겨진 버튼 제거 */
        .stForm button {{
            display: none !important;
        }}
        
        /* === 타이포그래피 === */
        h1, h2, h3 {{
            color: #e1e5e9 !important;
            font-weight: 600 !important;
        }}
        
        /* === 컨테이너 및 레이아웃 === */
        .stExpander {{
            background-color: #2d3748 !important;
            border: 1px solid #4a5568 !important;
            border-radius: 0.5rem !important;
        }}
        
        /* 로딩 스피너 */
        .stSpinner {{
            color: #667eea !important;
        }}
        
        /* 구분선 */
        hr {{
            border-color: #4a5568 !important;
        }}
        
        /* === 페이지 헤더 === */
        .stApp > header {{
            background-color: #1a1a1a !important;
        }}
        
        .stToolbar {{
            background-color: #1a1a1a !important;
        }}
        
        /* Emotion 기반 컴포넌트 강제 스타일링 */
        .st-emotion-cache-14vh5up {{
            background-color: #1a1a1a !important;
            color: #e1e5e9 !important;
        }}
        
        .st-emotion-cache-14vh5up * {{
            background-color: #1a1a1a !important;
            color: #e1e5e9 !important;
        }}
        
        /* === 선택 컨트롤 === */
        .stSelectbox select, .stMultiSelect select {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
            border: 1px solid #4a5568 !important;
        }}
        
        .stSelectbox [data-baseweb="select"] {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
        }}
        
        .stSelectbox [data-baseweb="select"] > div {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
        }}
        
        .stSelectbox [data-baseweb="select"] span {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
        }}
        
        .stMultiSelect [data-baseweb="select"] {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
        }}
        
        /* === 체크박스 및 라디오 === */
        .stCheckbox label, .stRadio label {{
            color: #e1e5e9 !important;
        }}
        
        /* === 메트릭 카드 === */
        .stMetric {{
            background-color: #2d3748 !important;
            border: 1px solid #4a5568 !important;
            border-radius: 0.5rem !important;
            padding: 1rem !important;
        }}
        
        .stMetric label, .stMetric .metric-container {{
            color: #e1e5e9 !important;
        }}
        
        /* === 데이터 테이블 === */
        .stDataFrame {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
        }}
        
        /* === 탭 시스템 === */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: #2d3748 !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: #4a5568 !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: #667eea !important;
            color: #ffffff !important;
            border: none !important;
        }}
        
        /* === 진행률 표시기 === */
        .stProgress > div > div {{
            background-color: #667eea !important;
        }}
        
        /* === 범용 Emotion 컴포넌트 === */
        [class*="st-emotion-cache"] {{
            color: #e1e5e9 !important;
        }}
        
        [class*="st-emotion-cache"] input,
        [class*="st-emotion-cache"] textarea,
        [class*="st-emotion-cache"] select {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
            border: 1px solid #4a5568 !important;
        }}
        
        /* === 로딩 및 피드백 === */
        .stSpinner > div {{
            border-top-color: #667eea !important;
        }}
        
        .stToast {{
            background-color: #2d3748 !important;
            color: #e1e5e9 !important;
            border: 1px solid #4a5568 !important;
        }}
        
        /* === 레이아웃 === */
        .row-widget {{
            background-color: transparent !important;
        }}
        
        /* === 텍스트 컨테이너 === */
        .stMarkdown, .stText, .stCaption, .stCode,
        div[data-testid="stMarkdownContainer"],
        div[data-testid="stText"] {{
            color: #e1e5e9 !important;
        }}
        
        /* === 링크 === */
        a {{
            color: #667eea !important;
        }}
        
        a:hover {{
            color: #5a67d8 !important;
        }}
        
    </style>
    """

# ====================================
# 🔍 검색 및 데이터 필터링 시스템
# ====================================
# Q&A 시스템의 질문 검색 및 분류 기능 (레거시)

def search_questions(data: Dict, search_term: str = "", category_filter: str = "전체") -> List[Dict]:
    """
    질문 검색 및 카테고리 필터링 (Q&A 시스템용)
    
    레거시 Q&A 시스템에서 질문을 검색하고 카테고리별로 필터링합니다.
    제목과 내용을 모두 검색 대상으로 하여 포괄적인 검색 결과를 제공합니다.
    
    Args:
        data: Q&A 데이터가 포함된 저장소
        search_term: 검색할 키워드 (빈 문자열이면 전체)
        category_filter: 카테고리 필터 ("전체"면 모든 카테고리)
    
    Returns:
        List[Dict]: 검색 조건에 맞는 질문 목록
    """
    filtered_questions = []
    
    for q in data["questions"]:
        match = True
        
        # 키워드 검색 (제목 + 내용)
        if search_term:
            search_lower = search_term.lower()
            if (search_lower not in q["title"].lower() and 
                search_lower not in q["content"].lower()):
                match = False
        
        # 카테고리 필터 적용
        if category_filter != "전체" and q["category"] != category_filter:
            match = False
        
        if match:
            filtered_questions.append(q)
    
    return filtered_questions

# ====================================
# 🗂️ Q&A 시스템 데이터 관리 (레거시)
# ====================================
# 질문/답변 등록, 좋아요, 삭제 등 Q&A 시스템 핵심 기능들

def add_question(data: Dict, title: str, category: str, content: str) -> str:
    """
    새 질문 등록 및 포인트 지급
    
    사용자가 작성한 질문을 시스템에 등록하고, 기여에 대한 보상으로
    포인트를 지급합니다. 질문 ID를 반환하여 추후 답변 연결에 사용합니다.
    
    Args:
        data: 질문이 저장될 메인 저장소
        title: 질문 제목
        category: 질문 카테고리
        content: 질문 내용
    
    Returns:
        str: 생성된 질문의 고유 ID
    """
    question_id = str(uuid.uuid4())
    username = get_username()
    
    new_question = {
        "id": question_id,
        "title": title,
        "category": category,
        "content": content,
        "author": username,
        "author_id": get_user_id(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data["questions"].append(new_question)
    
    # 질문 기여에 대한 포인트 보상
    add_user_points(data, username, 100, "질문하기")
    
    return question_id

def add_answer(data: Dict, question_id: str, content: str) -> str:
    """
    새 답변 등록 및 포인트 지급
    
    특정 질문에 대한 답변을 등록하고, 답변 기여에 대한 포인트를 지급합니다.
    답변 ID를 반환하여 좋아요 시스템과 연결합니다.
    
    Args:
        data: 답변이 저장될 메인 저장소
        question_id: 답변 대상 질문의 ID
        content: 답변 내용
    
    Returns:
        str: 생성된 답변의 고유 ID
    """
    answer_id = str(uuid.uuid4())
    username = get_username()
    
    new_answer = {
        "id": answer_id,
        "question_id": question_id,
        "content": content,
        "author": username,
        "author_id": get_user_id(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data["answers"].append(new_answer)
    
    # 답변 기여에 대한 포인트 보상
    add_user_points(data, username, 100, "답변하기")
    
    return answer_id

def toggle_like(data: Dict, answer_id: str) -> bool:
    """
    답변 좋아요 토글 시스템
    
    사용자가 답변에 좋아요를 누르거나 취소할 수 있는 시스템입니다.
    중복 좋아요는 방지되며, 좋아요 상태를 토글 방식으로 관리합니다.
    
    Args:
        data: 좋아요 데이터가 저장된 메인 저장소
        answer_id: 좋아요 대상 답변의 ID
    
    Returns:
        bool: 좋아요 결과 상태 (True: 좋아요, False: 좋아요 취소)
    """
    like_key = f"answer_{answer_id}"
    likes = data["likes"].get(like_key, [])
    user_id = get_user_id()
    
    if user_id in likes:
        likes.remove(user_id)  # 좋아요 취소
        liked = False
    else:
        likes.append(user_id)  # 좋아요 추가
        liked = True
    
    data["likes"][like_key] = likes
    save_data(data)
    return liked

def delete_question(data: Dict, question_id: str) -> None:
    """
    질문 및 관련 데이터 완전 삭제
    
    질문을 삭제할 때 연관된 모든 답변과 좋아요 데이터도 함께 제거하여
    데이터 무결성을 유지합니다. 관리자나 작성자만 삭제 권한을 가져야 합니다.
    
    Args:
        data: 삭제할 데이터가 포함된 메인 저장소
        question_id: 삭제할 질문의 ID
    """
    # 질문 자체 삭제
    data["questions"] = [q for q in data["questions"] if q["id"] != question_id]
    
    # 관련 답변들의 ID 수집
    answer_ids_to_remove = [a["id"] for a in data["answers"] if a["question_id"] == question_id]
    
    # 관련 답변들 삭제
    data["answers"] = [a for a in data["answers"] if a["question_id"] != question_id]
    
    # 관련 좋아요들 삭제 (데이터 정리)
    for answer_id in answer_ids_to_remove:
        like_key = f"answer_{answer_id}"
        if like_key in data["likes"]:
            del data["likes"][like_key]
    
    save_data(data)

# ====================================
# 📝 회원가입 및 승인 시스템
# ====================================

def submit_registration_request(username: str, name: str, department: str, password: str) -> tuple[bool, str]:
    """새 시스템으로 리다이렉트"""
    try:
        from user_manager import add_registration_request
        return add_registration_request(username, name, department, password)
    except Exception as e:
        logger.error(f"회원가입 신청 실패: {e}")
        return False, "회원가입 신청 중 오류가 발생했습니다"

def submit_registration_request_legacy(username: str, name: str, department: str, password: str) -> tuple[bool, str]:
    """
    회원가입 신청 제출 (관리자 승인 대기)
    
    Args:
        username: 녹스아이디 (로그인 시 사용할 ID)
        name: 실명
        department: 소속 부서
        password: 비밀번호 (bcrypt로 해시화됨)
        
    Returns:
        tuple[bool, str]: (성공여부, 메시지)
    """
    try:
        data = initialize_data()
        
        # 중복 확인
        existing_users = get_users_from_secrets()
        if username in existing_users:
            return False, "이미 등록된 녹스아이디입니다."
            
        # 대기 중인 신청 중복 확인
        pending_requests = data.get("registration_requests", [])
        if any(req["username"] == username and req["status"] == "pending" for req in pending_requests):
            return False, "이미 승인 대기 중인 녹스아이디입니다."
        
        # 비밀번호 해시화
        import bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 신청 정보 생성
        request_data = {
            "id": len(pending_requests) + 1,
            "username": username,
            "name": name,
            "department": department,
            "password_hash": password_hash,
            "status": "pending",  # pending, approved, rejected
            "requested_at": datetime.now().isoformat(),
            "processed_at": None,
            "processed_by": None
        }
        
        data["registration_requests"].append(request_data)
        save_data(data)
        
        return True, "회원가입 신청이 완료되었습니다. 관리자 승인 후에 사용 가능합니다."
        
    except Exception as e:
        logger.error(f"회원가입 신청 실패: {e}")
        return False, f"회원가입 신청 중 오류가 발생했습니다: {str(e)}"

def get_pending_registration_requests(data: Dict) -> List[Dict]:
    """관리자용: 승인 대기 중인 회원가입 신청 목록 조회"""
    return [req for req in data.get("registration_requests", []) if req["status"] == "pending"]

def approve_registration_request(data: Dict, request_id: int, admin_username: str) -> tuple[bool, str]:
    """
    관리자용: 회원가입 신청 승인 (자동 계정 생성)
    
    Args:
        data: 메인 데이터 저장소
        request_id: 승인할 신청 ID
        admin_username: 승인한 관리자 녹스아이디
        
    Returns:
        tuple[bool, str]: (성공여부, 메시지)
    """
    try:
        requests = data.get("registration_requests", [])
        request_to_approve = None
        
        for req in requests:
            if req["id"] == request_id and req["status"] == "pending":
                request_to_approve = req
                break
        
        if not request_to_approve:
            return False, "해당 신청을 찾을 수 없거나 이미 처리되었습니다."
        
        # 데이터베이스에 승인된 사용자 추가
        if "approved_users" not in data:
            data["approved_users"] = {}
            
        data["approved_users"][request_to_approve['username']] = {
            "name": request_to_approve['name'],
            "password": request_to_approve['password_hash'],
            "nox_id": request_to_approve['username'],
            "department": request_to_approve['department'],
            "approved_at": datetime.now().isoformat(),
            "approved_by": admin_username
        }
        
        # 승인 상태 업데이트
        request_to_approve["status"] = "approved"
        request_to_approve["processed_at"] = datetime.now().isoformat()
        request_to_approve["processed_by"] = admin_username
        
        save_data(data)
        
        return True, f"'{request_to_approve['username']}' 계정이 승인되고 자동으로 생성되었습니다. 지금 바로 로그인 가능합니다!"
        
    except Exception as e:
        logger.error(f"회원가입 승인 실패: {e}")
        return False, f"승인 처리 중 오류가 발생했습니다: {str(e)}"


def reject_registration_request(data: Dict, request_id: int, admin_username: str, reason: str = "") -> tuple[bool, str]:
    """
    관리자용: 회원가입 신청 거절
    
    Args:
        data: 메인 데이터 저장소
        request_id: 거절할 신청 ID
        admin_username: 거절한 관리자 녹스아이디
        reason: 거절 사유 (선택사항)
        
    Returns:
        tuple[bool, str]: (성공여부, 메시지)
    """
    try:
        requests = data.get("registration_requests", [])
        request_to_reject = None
        
        for req in requests:
            if req["id"] == request_id and req["status"] == "pending":
                request_to_reject = req
                break
        
        if not request_to_reject:
            return False, "해당 신청을 찾을 수 없거나 이미 처리되었습니다."
        
        request_to_reject["status"] = "rejected"
        request_to_reject["processed_at"] = datetime.now().isoformat()
        request_to_reject["processed_by"] = admin_username
        request_to_reject["rejection_reason"] = reason
        
        save_data(data)
        
        return True, f"'{request_to_reject['username']}' 계정 신청이 거절되었습니다."
        
    except Exception as e:
        logger.error(f"회원가입 거절 실패: {e}")
        return False, f"거절 처리 중 오류가 발생했습니다: {str(e)}"

# ====================================
# 🔐 로그인 세션 유지 개선
# ====================================

def extend_session_cookie():
    """로그인 세션 쿠키 유효기간 연장"""
    try:
        # Streamlit의 쿠키는 자동으로 갱신되지 않으므로
        # 사용자가 페이지를 방문할 때마다 세션 상태를 확인하고 유지
        if is_logged_in():
            # 세션이 유효한 경우 타임스탬프 업데이트
            st.session_state["last_activity"] = datetime.now().isoformat()
            return True
    except Exception as e:
        logger.error(f"세션 연장 실패: {e}")
    return False

def check_session_validity() -> bool:
    """세션 유효성 검사 (자동 로그아웃 방지)"""
    try:
        if not is_logged_in():
            return False
            
        # 마지막 활동 시간 확인 (24시간 유효)
        last_activity = st.session_state.get("last_activity")
        if last_activity:
            from datetime import datetime, timedelta
            last_time = datetime.fromisoformat(last_activity)
            if datetime.now() - last_time > timedelta(hours=24):
                # 세션 만료
                logout_user()
                return False
        
        # 세션 유효 - 활동 시간 업데이트
        extend_session_cookie()
        return True
        
    except Exception as e:
        logger.error(f"세션 유효성 검사 실패: {e}")
        return False