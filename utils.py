"""
======================================================================
AE WIKI 통합 챗봇 시스템 - 통합 유틸리티 모듈 (utils.py)
======================================================================

📋 파일 역할:
- 기존 코드와의 호환성을 위한 통합 진입점
- 모든 주요 기능을 각 전문 모듈에서 임포트
- 레거시 코드가 수정 없이 작동하도록 지원

🔧 모듈 구조:
1. data_manager.py - 데이터 관리 (JSON 파일 처리)
2. auth_manager.py - 사용자 인증 및 세션 관리
3. api_manager.py - AI API 통신 (RAG, LLM)
4. chat_manager.py - 채팅 기록 및 검색 로그
5. ui_components.py - UI 컴포넌트 및 스타일
6. qa_manager.py - Q&A 시스템 관리

🔗 임포트 방식:
from utils import function_name  # 기존 방식 유지
"""

import os
import sys
import logging
import streamlit as st

# 로거 설정
logger = logging.getLogger(__name__)

# ====================================
# 📁 데이터 관리 모듈
# ====================================
try:
    from data_manager import (
        initialize_data,
        save_data,
        load_data,
        initialize_users_data,
        save_users_data,
        load_users_data
    )
    logger.info("데이터 관리 모듈 로드 완료")
except ImportError as e:
    logger.error(f"데이터 관리 모듈 로드 실패: {e}")
    # 호환성을 위한 기본 구현
    def initialize_data():
        return {}
    def save_data(data):
        pass
    def load_data():
        return {}
    def initialize_users_data():
        return {}
    def save_users_data(data):
        pass
    def load_users_data():
        return {}

# ====================================
# 🔐 인증 관리 모듈
# ====================================
try:
    from auth_manager import (
        get_users_from_secrets,
        verify_password,
        simple_login,
        is_logged_in,
        setup_session_after_login,
        logout_user,
        initialize_session_state,
        restore_login_from_storage,
        require_login,
        show_login_required,
        get_current_user,
        get_user_id,
        get_username,
        get_display_name,
        get_knox_id,
        check_admin,
        login_admin,
        logout_admin,
        extend_session_cookie,
        check_session_validity
    )
    logger.info("인증 관리 모듈 로드 완료")
except ImportError as e:
    logger.error(f"인증 관리 모듈 로드 실패: {e}")
    # 기본 스텁 함수들
    def require_login():
        return True
    def get_user_id():
        return "anonymous"
    def get_current_user():
        return None
    def get_username():
        return "anonymous"

# ====================================
# 🤖 API 관리 모듈
# ====================================
try:
    from api_manager import (
        call_llm_api,
        call_rag_api_with_chatbot_type,
        format_source_citations
    )
    logger.info("API 관리 모듈 로드 완료")
except ImportError as e:
    logger.error(f"API 관리 모듈 로드 실패: {e}")
    def call_llm_api(*args, **kwargs):
        return "API 관리 모듈을 로드할 수 없습니다."
    def call_rag_api_with_chatbot_type(*args, **kwargs):
        return {"documents": [], "source_info": []}
    def format_source_citations(*args, **kwargs):
        return ""

# ====================================
# 💬 채팅 관리 모듈
# ====================================
try:
    from chat_manager import (
        save_chat_history,
        log_search,
        get_user_chat_history,
        get_chatbot_usage_stats,
        get_search_analytics,
        cleanup_old_logs,
        export_chat_history
    )
    logger.info("채팅 관리 모듈 로드 완료")
except ImportError as e:
    logger.error(f"채팅 관리 모듈 로드 실패: {e}")
    def save_chat_history(
        data,
        user_message,
        bot_response,
        chatbot_type="ae_wiki",
        user_id=None,
        **kwargs
    ):
        """
        통합 대화 로그 저장.
        - user_id: Knox ID 권장 (없으면 자동 추정)
        - chatbot_type: ae_wiki / glossary / jedec / tripmate / lab ...
        """
        from datetime import datetime

        # Knox ID가 없으면 시스템에서 추정
        try:
            from utils import get_username
            resolved_user = user_id or get_username() or "anonymous"
        except Exception:
            resolved_user = user_id or "anonymous"

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": resolved_user,
            "user_message": str(user_message),
            "bot_response": str(bot_response),
            "chatbot_type": chatbot_type,
        }

        # 통합 로그 저장
        data.setdefault("chat_history", []).append(entry)

        # (선택) 챗봇별 별도 리스트도 병행 유지
        per_bot_key_map = {
            "ae_wiki": "ae_wiki_chat_history",
            "glossary": "glossary_chat_history",
            "jedec": "jedec_chat_history",
            "tripmate": "tripmate_chat_history",
            "lab": "lab_chat_history",
        }

        per_key = per_bot_key_map.get(chatbot_type)
        if per_key:
            data.setdefault(per_key, []).append(entry)

        # 저장
        try:
            from utils import save_data as _save
            _save(data)
        except Exception:
            pass  # 저장 오류 시 무시 (앱 죽지 않게)

        return entry

    def log_search(*args, **kwargs):
        pass

# ====================================
# 🎨 UI 컴포넌트 모듈
# ====================================
try:
    from ui_components import (
        display_typing_effect,
        load_css_styles,
        create_metric_card,
        create_status_badge,
        create_info_card,
        create_alert_box,
        show_loading_spinner,
        create_gradient_text,
        apply_animation
    )
    logger.info("UI 컴포넌트 모듈 로드 완료")
except ImportError as e:
    logger.error(f"UI 컴포넌트 모듈 로드 실패: {e}")
    def display_typing_effect(*args, **kwargs):
        pass
    def load_css_styles():
        return ""

# ====================================
# ❓ Q&A 관리 모듈
# ====================================
try:
    from qa_manager import (
        search_questions,
        add_question,
        add_answer,
        toggle_like,
        delete_question,
        get_answer_ranking,
        get_question_statistics,
        submit_registration_request,
        get_pending_registration_requests,
        approve_registration_request,
        reject_registration_request,
        get_qa_activity_summary
    )
    logger.info("Q&A 관리 모듈 로드 완료")
except ImportError as e:
    logger.error(f"Q&A 관리 모듈 로드 실패: {e}")
    def search_questions(*args, **kwargs):
        return []
    def add_question(*args, **kwargs):
        return ""
    def add_answer(*args, **kwargs):
        return ""

# ====================================
# 🔧 설정 모듈
# ====================================
try:
    from config import API_CONFIG, CHATBOT_INDICES, get_index_config, DATA_CONFIG
    logger.info("설정 모듈 로드 완료")
except ImportError as e:
    logger.error(f"설정 모듈 로드 실패: {e}")
    API_CONFIG = {}
    CHATBOT_INDICES = {}
    DATA_CONFIG = {}
    def get_index_config(index_id):
        return {}

# ====================================
# 🔧 헬퍼 함수들
# ====================================
def get_index_system_prompt(chatbot_type: str) -> str:
    """인덱스별 시스템 프롬프트 반환"""
    try:
        config = get_index_config(chatbot_type)
        return config.get("system_prompt", "당신은 전문 AI 어시스턴트입니다.")
    except:
        return "당신은 전문 AI 어시스턴트입니다."

def get_index_rag_name(chatbot_type: str) -> str:
    """인덱스별 RAG 인덱스명 반환"""
    try:
        config = get_index_config(chatbot_type)
        return config.get("index_name", f"rp-{chatbot_type}")
    except:
        return f"rp-{chatbot_type}"

def get_chatbot_response(user_message: str, chat_history=None, user_id=None, system_prompt=None, chatbot_type="ae_wiki") -> str:
    """통합 챗봇 응답 생성"""
    try:
        # RAG 검색
        rag_result = call_rag_api_with_chatbot_type(user_message, chatbot_type)
        retrieve_data = rag_result.get("documents", [])
        source_data = rag_result.get("source_info", [])

        # LLM 응답 생성
        response = call_llm_api(
            user_message=user_message,
            retrieve_data=retrieve_data,
            chat_history=chat_history,
            source_data=source_data,
            user_id=user_id,
            custom_system_prompt=system_prompt,
            chatbot_type=chatbot_type
        )

        return response

    except Exception as e:
        logger.error(f"챗봇 응답 생성 중 오류: {e}")
        return f"죄송합니다. 시스템 오류가 발생했습니다: {str(e)}"

# ====================================
# 🔧 포인트 시스템 관리
# ====================================
def award_points(points: int, activity: str) -> bool:
    """어디서 호출하든 안전하게 포인트 지급"""
    data = initialize_data()        # data 스코프 문제 방지
    key = get_points_key()           # Unknown 방지

    if not key:
        return False

    add_user_points(data, key, points, activity)  # 내부에서 save_data()까지 함
    return True

def get_points_key() -> str:
    """포인트 적립/조회에 사용할 유일한 키 = knox_id"""
    user = get_current_user()

    # 1) user dict 기반
    if user:
        key = (user.get("knox_id") or user.get("username") or "").strip()
        if key:
            return key

    # 2) 세션 기반 fallback (auth_manager가 저장함)
    key = (st.session_state.get("auth_knox_id") or
           st.session_state.get("auth_user") or "").strip()
    return key

def add_user_points(data, username: str, points: int, activity_type: str) -> None:
    """사용자 포인트 추가"""
    try:
        if "user_points" not in data:
            data["user_points"] = {}

        current_points = data["user_points"].get(username, 0)
        data["user_points"][username] = current_points + points

        save_data(data)
        logger.info(f"포인트 추가: {username} +{points} ({activity_type})")

    except Exception as e:
        logger.error(f"포인트 추가 실패: {e}")

def get_user_points(data, username: str) -> int:
    """사용자 포인트 조회"""
    try:
        return data.get("user_points", {}).get(username, 0)
    except Exception as e:
        logger.error(f"포인트 조회 실패: {e}")
        return 0

def get_current_user_points(data) -> int:
    key = get_points_key()
    return data.get("user_points", {}).get(key, 0)

def set_user_points(data, username: str, new_points: int, admin_user: str = None) -> bool:
    """사용자 포인트 설정 (관리자 기능)"""
    try:
        if "user_points" not in data:
            data["user_points"] = {}

        old_points = data["user_points"].get(username, 0)
        data["user_points"][username] = new_points

        save_data(data)
        logger.info(f"포인트 설정: {username} {old_points} -> {new_points} (by {admin_user})")
        return True

    except Exception as e:
        logger.error(f"포인트 설정 실패: {e}")
        return False

def adjust_user_points(data, username: str, point_change: int, reason: str = "", admin_user: str = None) -> bool:
    """사용자 포인트 조정 (관리자 기능)"""
    try:
        if "user_points" not in data:
            data["user_points"] = {}

        old_points = data["user_points"].get(username, 0)
        new_points = max(0, old_points + point_change)  # 음수 방지
        data["user_points"][username] = new_points

        save_data(data)
        logger.info(f"포인트 조정: {username} {old_points} -> {new_points} ({point_change:+d}) (by {admin_user})")
        return True

    except Exception as e:
        logger.error(f"포인트 조정 실패: {e}")
        return False

def get_user_points_ranking(data) -> list:
    """사용자 포인트 랭킹 조회"""
    try:
        user_points = data.get("user_points", {})
        ranking = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
        return ranking
    except Exception as e:
        logger.error(f"포인트 랭킹 조회 실패: {e}")
        return []

def get_all_user_points(data) -> dict:
    """전체 사용자 포인트 조회"""
    try:
        return data.get("user_points", {})
    except Exception as e:
        logger.error(f"전체 사용자 포인트 조회 실패: {e}")
        return {}

def get_point_change_history(data, username: str = None, limit: int = 50) -> list:
    """포인트 변경 기록 조회"""
    try:
        history = data.get("point_change_history", [])

        # 특정 사용자 필터링
        if username:
            history = [h for h in history if h.get("username") == username]

        # 최신순 정렬 및 제한
        history = sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)
        return history[:limit]
    except Exception as e:
        logger.error(f"포인트 변경 기록 조회 실패: {e}")
        return []

def cleanup_duplicate_points_data(data, method: str = "keep_current") -> bool:
    """중복 포인트 데이터 정리"""
    try:
        from datetime import datetime

        user_points = data.get("user_points", {})
        users_list = get_all_users()
        user_dict = {user.get("knox_id", user.get("user_id", "")): user for user in users_list}

        # 중복 데이터 찾기
        duplicates_found = []
        for username in list(user_points.keys()):
            # knox_id가 아닌 경우 (레거시 이름 기반)
            if username not in [user.get("knox_id", "") for user in users_list]:
                # 실제 사용자 이름과 매칭되는지 확인
                matching_user = None
                for user in users_list:
                    if user.get("name", "") == username or user.get("nickname", "") == username:
                        matching_user = user
                        break

                if matching_user and matching_user.get("knox_id") in user_points:
                    legacy_key = username
                    current_key = matching_user.get("knox_id")
                    legacy_points = user_points.get(legacy_key, 0)
                    current_points = user_points.get(current_key, 0)

                    duplicates_found.append({
                        "legacy_key": legacy_key,
                        "legacy_points": legacy_points,
                        "current_key": current_key,
                        "current_points": current_points
                    })

        # 중복 데이터 처리
        for dup in duplicates_found:
            if method == "keep_current":
                # 현재 데이터 유지, 레거시 삭제
                if dup["legacy_key"] in user_points:
                    del user_points[dup["legacy_key"]]
            elif method == "keep_higher":
                # 더 높은 포인트 값 유지
                max_points = max(dup["legacy_points"], dup["current_points"])
                user_points[dup["current_key"]] = max_points
                if dup["legacy_key"] in user_points:
                    del user_points[dup["legacy_key"]]
            elif method == "sum_points":
                # 포인트 합산
                total_points = dup["legacy_points"] + dup["current_points"]
                user_points[dup["current_key"]] = total_points
                if dup["legacy_key"] in user_points:
                    del user_points[dup["legacy_key"]]

        # 변경사항 저장
        data["user_points"] = user_points
        save_data(data)

        logger.info(f"중복 포인트 데이터 정리 완료: {len(duplicates_found)}건 처리 (방법: {method})")
        return True

    except Exception as e:
        logger.error(f"중복 포인트 데이터 정리 실패: {e}")
        return False

# ====================================
# 🔧 사용자 관리 함수들
# ====================================
def validate_knox_id(knox_id: str):
    """Knox ID 유효성 검사"""
    if not knox_id or len(knox_id.strip()) == 0:
        return False, "Knox ID를 입력해주세요."
    if len(knox_id) < 3:
        return False, "Knox ID는 최소 3자 이상이어야 합니다."
    if not knox_id.replace("_", "").replace("-", "").replace(".", "").isalnum():
        return False, "Knox ID는 영문자, 숫자, _, -, . 만 사용 가능합니다."
    return True, "유효한 Knox ID입니다."

def validate_nickname(nickname: str):
    """닉네임 유효성 검사"""
    if not nickname or len(nickname.strip()) == 0:
        return False, "닉네임을 입력해주세요."
    if len(nickname) < 2:
        return False, "닉네임은 최소 2자 이상이어야 합니다."
    if len(nickname) > 20:
        return False, "닉네임은 최대 20자까지 가능합니다."
    return True, "유효한 닉네임입니다."

def validate_department(department: str):
    """부서 유효성 검사"""
    if not department or len(department.strip()) == 0:
        return False, "부서를 입력해주세요."
    if len(department) < 2:
        return False, "부서명은 최소 2자 이상이어야 합니다."
    return True, "유효한 부서명입니다."

def get_all_users():
    """모든 사용자 조회 (user_manager.py의 active_users 사용)"""
    try:
        from user_manager import get_all_active_users

        # user_manager.py는 딕셔너리를 반환하므로 리스트로 변환
        active_users_dict = get_all_active_users()

        # 딕셔너리의 값들을 리스트로 변환
        users_list = []
        for knox_id, user_data in active_users_dict.items():
            # 리스트 형식으로 변환 (하위 호환성을 위해)
            user_dict = {
                "user_id": user_data.get("user_id", ""),
                "knox_id": knox_id,
                "username": knox_id,  # 호환성
                "nickname": user_data.get("nickname", user_data.get("name", "")),
                "name": user_data.get("name", ""),
                "department": user_data.get("department", ""),
                "is_active": user_data.get("is_active", True),
                "created_at": user_data.get("created_at", ""),
                "last_login": user_data.get("last_login", "")
            }
            users_list.append(user_dict)

        return users_list

    except Exception as e:
        logger.error(f"사용자 목록 조회 실패: {e}")
        return []

def search_users(keyword: str = ""):
    """사용자 검색"""
    try:
        users = get_all_users()
        if not keyword:
            return users

        keyword = keyword.lower()
        filtered_users = []

        for user in users:
            if (keyword in user.get("username", "").lower() or
                keyword in user.get("nickname", "").lower() or
                keyword in user.get("knox_id", "").lower() or
                keyword in user.get("department", "").lower()):
                filtered_users.append(user)

        return filtered_users
    except Exception as e:
        logger.error(f"사용자 검색 실패: {e}")
        return []

def toggle_user_status(user_id: str) -> bool:
    """사용자 상태 토글 (user_manager.py 사용)"""
    try:
        from user_manager import load_users_data as load_user_mgr_data, save_users_data as save_user_mgr_data

        users_data = load_user_mgr_data()
        active_users = users_data.get("active_users", {})

        # user_id로 사용자 찾기
        for knox_id, user_data in active_users.items():
            if user_data.get("user_id") == user_id:
                # is_active 상태 토글
                current_status = user_data.get("is_active", True)
                user_data["is_active"] = not current_status
                save_user_mgr_data(users_data)
                logger.info(f"사용자 상태 토글: {knox_id} -> {user_data['is_active']}")
                return True

        logger.warning(f"사용자를 찾을 수 없음: user_id={user_id}")
        return False

    except Exception as e:
        logger.error(f"사용자 상태 토글 실패: {e}")
        return False

def delete_user(user_id: str) -> bool:
    """사용자 삭제 (user_manager.py 사용)"""
    try:
        from user_manager import load_users_data as load_user_mgr_data, save_users_data as save_user_mgr_data

        users_data = load_user_mgr_data()
        active_users = users_data.get("active_users", {})

        # user_id로 사용자 찾아서 삭제
        knox_id_to_delete = None
        for knox_id, user_data in active_users.items():
            if user_data.get("user_id") == user_id:
                knox_id_to_delete = knox_id
                break

        if knox_id_to_delete:
            del active_users[knox_id_to_delete]
            save_user_mgr_data(users_data)
            logger.info(f"사용자 삭제: {knox_id_to_delete}")
            return True

        logger.warning(f"삭제할 사용자를 찾을 수 없음: user_id={user_id}")
        return False

    except Exception as e:
        logger.error(f"사용자 삭제 실패: {e}")
        return False

def update_user_info(user_id: str, nickname: str, department: str):
    """사용자 정보 수정 (user_manager.py 사용)"""
    try:
        from user_manager import load_users_data as load_user_mgr_data, save_users_data as save_user_mgr_data

        users_data = load_user_mgr_data()
        active_users = users_data.get("active_users", {})

        # user_id로 사용자 찾아서 수정
        for knox_id, user_data in active_users.items():
            if user_data.get("user_id") == user_id:
                user_data["nickname"] = nickname
                user_data["department"] = department
                save_user_mgr_data(users_data)
                logger.info(f"사용자 정보 수정: {knox_id} - {nickname}, {department}")
                return True, "사용자 정보가 수정되었습니다."

        logger.warning(f"수정할 사용자를 찾을 수 없음: user_id={user_id}")
        return False, "사용자를 찾을 수 없습니다."

    except Exception as e:
        logger.error(f"사용자 정보 수정 실패: {e}")
        return False, f"수정 중 오류 발생: {str(e)}"

# Legacy support functions for existing code
def submit_registration_request_legacy(username: str, name: str, department: str, password: str):
    """레거시 등록 요청 함수"""
    return submit_registration_request(username, name, department, password)

# ===============================================================
# 👤 사용자 표시용 ID/닉네임 변환 유틸 (로그/랭킹 공용)
# ===============================================================

def resolve_user_label(user_key: str) -> str:
    """
    저장 데이터에 쓰이는 사용자 키(예: knox_id / username / user_id / 세션UUID)를
    화면 표시용 닉네임(없으면 실명, 없으면 원래 키)으로 변환한다.
    """
    try:
        from utils import get_all_users  # self-import 회피
        users = get_all_users()
    except Exception:
        return user_key or "Unknown"

    for u in users:
        if user_key in (u.get("knox_id"), u.get("username"),
                        u.get("user_id"), u.get("name")):
            return u.get("nickname") or u.get("name") or \
                   u.get("knox_id") or user_key

    return user_key or "Unknown"

def resolve_to_knox_id(user_key: str) -> str:
    """
    저장 키를 Knox ID(회사 계정 ID)로 변환.
    일치하는 사용자가 없으면 원래 값을 그대로 반환한다.
    """
    try:
        from utils import get_all_users
        users = get_all_users()
    except Exception:
        return user_key or "Unknown"

    for u in users:
        if user_key in (u.get("knox_id"), u.get("username"),
                        u.get("user_id"), u.get("name")):
            return u.get("knox_id") or user_key

    return user_key or "Unknown"

logger.info("Utils 모듈 로드 완료")