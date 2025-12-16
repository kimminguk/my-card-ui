"""
======================================================================
AE WIKI 통합 챗봇 시스템 - 인증 관리 모듈 (auth_manager.py)
======================================================================

📋 파일 역할:
- 사용자 인증 및 세션 관리
- 로그인/로그아웃 처리
- 권한 확인 및 접근 제어
- 관리자 인증 시스템

🔧 주요 기능:
1. 사용자 인증 (로그인/로그아웃)
2. 세션 상태 관리
3. 권한 확인 및 접근 제어
4. 관리자 인증 시스템
5. 사용자 정보 조회

🔗 연동 관계:
- user_manager.py: 통합 사용자 관리 시스템과 연동
- 모든 페이지: require_login()으로 접근 제어
- data_manager.py: 사용자 데이터 관리
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# 로거 설정
logger = logging.getLogger(__name__)

# ====================================
# 🔐 기본 인증 시스템
# ====================================

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

def simple_login(username: str, password: str) -> Tuple[bool, str, dict]:
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
                'knox_id': user_data.get('knox_id', username),
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

# ====================================
# 📊 세션 상태 관리
# ====================================

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
            st.session_state["auth_knox_id"] = user_info.get("knox_id", username)
            st.session_state["auth_department"] = user_info.get("department", "기타")
            logger.info(f"사용자 {username}({name}) 로그인 성공 - 세션 정보 설정 완료")
        else:
            # 기본 정보로 설정
            st.session_state["auth_knox_id"] = username
            st.session_state["auth_department"] = "기타"
            logger.warning(f"사용자 {username}의 추가 정보를 찾을 수 없음")
    except Exception as e:
        # 오류 발생 시 기본 로그인은 유지
        st.session_state["auth_knox_id"] = username
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
    auth_keys = ["auth_user", "auth_name", "auth_knox_id", "auth_department"]
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

# ====================================
# 🛡️ 접근 제어
# ====================================

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

def show_login_required() -> None:
    """
    로그인 필요 안내 메시지 표시

    미인증 사용자에게 로그인이 필요하다는 안내를 표시합니다.
    """
    st.error("🔒 이 페이지에 접근하려면 로그인이 필요합니다.")
    st.info("👈 사이드바에서 '로그인' 메뉴를 사용해 로그인해주세요.")

# ====================================
# 👤 사용자 정보 조회
# ====================================

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
                "knox_id": user_info.get('knox_id', auth_user),
                "nickname": user_info.get('nickname', auth_name),
                "department": user_info.get('department', 'Unknown'),
                "role": user_info.get('role', 'user')
            }
    except Exception as e:
        logger.error(f"사용자 정보 조회 실패: {e}")

    # 폴백: 기본 정보만 반환
    return {
        "user_id": auth_user,
        "knox_id": auth_user,
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
    사용자의 표시 이름 반환

    Args:
        user: 사용자 정보 딕셔너리 (None이면 현재 사용자)

    Returns:
        str: 표시할 사용자 이름
    """
    if user:
        return user.get('nickname', user.get('name', user.get('user_id', 'Unknown')))
    else:
        return get_username()

def get_knox_id() -> str:
    """
    현재 사용자의 NOX ID 반환

    Returns:
        str: NOX ID (미로그인 시 "unknown")
    """
    return st.session_state.get("auth_knox_id", "unknown")

# ====================================
# 👨‍💼 관리자 인증
# ====================================

def check_admin() -> bool:
    """
    관리자 권한 확인

    Returns:
        bool: 관리자 권한 여부
    """
    if not is_logged_in():
        return False

    try:
        from user_manager import is_admin_user
        username = get_user_id()
        return is_admin_user(username)
    except Exception as e:
        logger.error(f"관리자 권한 확인 실패: {e}")
        return False

def login_admin(password: str) -> bool:
    """
    관리자 로그인 처리

    Args:
        password: 관리자 비밀번호

    Returns:
        bool: 로그인 성공 여부
    """
    # 현재 사용자가 이미 관리자인지 확인
    if check_admin():
        st.session_state["admin_logged_in"] = True
        return True

    # 관리자 비밀번호 확인 (단순 구현)
    try:
        admin_password = st.secrets.get("admin", {}).get("password", "admin123")
        if password == admin_password:
            st.session_state["admin_logged_in"] = True
            return True
    except Exception as e:
        logger.error(f"관리자 로그인 확인 실패: {e}")

    return False

def logout_admin() -> None:
    """
    관리자 로그아웃 처리
    """
    if "admin_logged_in" in st.session_state:
        del st.session_state["admin_logged_in"]
    logger.info("관리자 로그아웃 완료")

# ====================================
# 🍪 세션 관리
# ====================================

def extend_session_cookie():
    """
    세션 쿠키 연장 (호환성 함수)

    현재 구현에서는 브라우저 세션을 사용하므로 별도 처리 불필요
    """
    pass

def check_session_validity() -> bool:
    """
    세션 유효성 확인

    Returns:
        bool: 세션 유효성 여부
    """
    return is_logged_in()