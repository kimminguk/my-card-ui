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
        load_users_data,
        DATA_CONFIG
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
        get_nox_id,
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

# ====================================
# 🤖 API 관리 모듈
# ====================================
try:
    from api_manager import (
        call_llm_api,
        get_mock_rag_response,
        get_mock_llm_response,
        call_rag_api_with_chatbot_type,
        format_source_citations
    )
    logger.info("API 관리 모듈 로드 완료")
except ImportError as e:
    logger.error(f"API 관리 모듈 로드 실패: {e}")

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

# Config import
try:
    from config import API_CONFIG, CHATBOT_INDICES, get_index_config, DATA_CONFIG
    logger.info("설정 모듈 로드 완료")
except ImportError as e:
    logger.error(f"설정 모듈 로드 실패: {e}")
    API_CONFIG = {}
    CHATBOT_INDICES = {}
    # 폴백 DATA_CONFIG
    import os
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = os.path.join(PROJECT_ROOT, "datalog")
    os.makedirs(DATA_FOLDER, exist_ok=True)
    DATA_CONFIG = {
        "data_file": os.path.join(DATA_FOLDER, "knowledge_data.json"),
        "users_file": os.path.join(DATA_FOLDER, "users_data.json"),
    }

def get_index_system_prompt(chatbot_type: str) -> str:
    """
    인덱스별 시스템 프롬프트 반환

    Args:
        chatbot_type: 챗봇 타입 ID

    Returns:
        str: 해당 인덱스의 시스템 프롬프트
    """
    try:
        config = get_index_config(chatbot_type)
        return config.get("system_prompt", "당신은 전문 AI 어시스턴트입니다.")
    except:
        return "당신은 전문 AI 어시스턴트입니다."

def get_index_rag_name(chatbot_type: str) -> str:
    """
    인덱스별 RAG 인덱스명 반환

    Args:
        chatbot_type: 챗봇 타입 ID

    Returns:
        str: 해당 인덱스의 RAG 인덱스명
    """
    try:
        config = get_index_config(chatbot_type)
        return config.get("index_name", f"rp-{chatbot_type}")
    except:
        return f"rp-{chatbot_type}"

# Helper functions that are still needed locally
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
        (today - timedelta(days=1)).strftime("%Y-%m-%d"),  # 어제 (최신)
        (today - timedelta(days=7)).strftime("%Y-%m-%d"),  # 1주일 전
        (today - timedelta(days=30)).strftime("%Y-%m-%d"), # 1달 전
    ]

    mock_responses = {
        "ae_wiki": {
            "retrieved_documents": [
                f"[{dates[0]}] 최신 AE팀 업무 가이드라인 v2.1에 따르면...",
                f"[{dates[1]}] AE팀 프로세스 업데이트 사항은...",
                f"[{dates[2]}] 기존 AE팀 매뉴얼에서는..."
            ],
            "source_info": [
                {"source": "AE 업무 매뉴얼 v2.1", "page": "1", "last_modified": dates[0], "relevance_score": 0.95, "date_score": 1.0},
                {"source": "AE 프로세스 가이드", "page": "3", "last_modified": dates[1], "relevance_score": 0.88, "date_score": 0.8},
                {"source": "AE 업무 매뉴얼 v1.0", "page": "2", "last_modified": dates[2], "relevance_score": 0.82, "date_score": 0.3}
            ]
        },
        "glossary": {
            "retrieved_documents": [
                f"[{dates[0]}] 최신 반도체 용어 정의 업데이트: CMOS는...",
                f"[{dates[1]}] 반도체 기술 용어집 개정판에서...",
                f"[{dates[2]}] 기존 용어 정의서에 따르면..."
            ],
            "source_info": [
                {"source": "반도체 용어집 v3.0", "page": "45", "last_modified": dates[0], "relevance_score": 0.92, "date_score": 1.0},
                {"source": "반도체 기술 용어", "page": "12", "last_modified": dates[1], "relevance_score": 0.87, "date_score": 0.8},
                {"source": "반도체 용어집 v2.0", "page": "33", "last_modified": dates[2], "relevance_score": 0.85, "date_score": 0.3}
            ]
        },
        "jedec": {
            "retrieved_documents": [
                f"[{dates[0]}] JEDEC 최신 표준 JESD79-5A 규격에 의하면...",
                f"[{dates[1]}] JEDEC 표준 업데이트 내용은...",
                f"[{dates[2]}] 기존 JEDEC 표준문서에서는..."
            ],
            "source_info": [
                {"source": "JEDEC JESD79-5A", "page": "15", "last_modified": dates[0], "relevance_score": 0.94, "date_score": 1.0},
                {"source": "JEDEC 업데이트", "page": "8", "last_modified": dates[1], "relevance_score": 0.89, "date_score": 0.8},
                {"source": "JEDEC JESD79-4", "page": "22", "last_modified": dates[2], "relevance_score": 0.86, "date_score": 0.3}
            ]
        },
        "quality": {
            "retrieved_documents": [
                f"[{dates[0]}] 최신 품질관리 프로세스 v2.0에서는...",
                f"[{dates[1]}] 품질 기준 업데이트 사항...",
                f"[{dates[2]}] 기존 품질관리 문서에 따르면..."
            ],
            "source_info": [
                {"source": "품질관리 프로세스 v2.0", "page": "5", "last_modified": dates[0], "relevance_score": 0.93, "date_score": 1.0},
                {"source": "품질 기준 가이드", "page": "18", "last_modified": dates[1], "relevance_score": 0.86, "date_score": 0.8},
                {"source": "품질관리 매뉴얼 v1.5", "page": "12", "last_modified": dates[2], "relevance_score": 0.84, "date_score": 0.3}
            ]
        },
        "test_engineering": {
            "retrieved_documents": [
                f"[{dates[0]}] 최신 테스트엔지니어링 가이드 v3.1에서는...",
                f"[{dates[1]}] ATE 장비 운영 업데이트...",
                f"[{dates[2]}] 기존 테스트 방법론에서는..."
            ],
            "source_info": [
                {"source": "테스트엔지니어링 가이드 v3.1", "page": "7", "last_modified": dates[0], "relevance_score": 0.91, "date_score": 1.0},
                {"source": "ATE 운영 매뉴얼", "page": "25", "last_modified": dates[1], "relevance_score": 0.88, "date_score": 0.8},
                {"source": "테스트 방법론 v2.0", "page": "14", "last_modified": dates[2], "relevance_score": 0.83, "date_score": 0.3}
            ]
        },
        "design": {
            "retrieved_documents": [
                f"[{dates[0]}] 최신 설계엔지니어링 표준 v4.0에서는...",
                f"[{dates[1]}] 회로 설계 가이드라인 업데이트...",
                f"[{dates[2]}] 기존 설계 방법론에 따르면..."
            ],
            "source_info": [
                {"source": "설계엔지니어링 표준 v4.0", "page": "11", "last_modified": dates[0], "relevance_score": 0.96, "date_score": 1.0},
                {"source": "회로 설계 가이드", "page": "31", "last_modified": dates[1], "relevance_score": 0.89, "date_score": 0.8},
                {"source": "설계 방법론 v3.0", "page": "19", "last_modified": dates[2], "relevance_score": 0.87, "date_score": 0.3}
            ]
        }
    }

    result = mock_responses.get(chatbot_type, mock_responses["ae_wiki"])
    result.update({
        "total_found": len(result["retrieved_documents"]),
        "search_time": round(random.uniform(0.1, 0.5), 3),
        "sorted_by_date": True
    })

    return result

def get_mock_llm_response(user_message: str, retrieve_text: str, source_citations: str, chatbot_type: str, system_prompt: str) -> str:
    """Mock LLM 응답 생성 (인덱스별 프롬프트 적용)"""
    from config import get_index_config

    # 인덱스 설정 가져오기
    index_config = get_index_config(chatbot_type)
    display_name = index_config.get("display_name", chatbot_type)

    # 시스템 프롬프트에 따른 전문 분야별 답변 생성
    if "AE팀" in system_prompt or "ae_wiki" in chatbot_type:
        context = "AE팀 업무 관련 정보를 제공드리겠습니다."
        expertise = "- 이는 AE팀 업무 프로세스와 관련된 중요한 주제입니다\n- 반도체 제품 개발 및 고객 지원 업무에서 자주 다뤄지는 내용입니다\n- 정확한 절차를 따라 처리하시기 바랍니다"
        docs = "1. 반도체 제품 개발 프로세스\n2. 메모리 사양 및 테스트 방법\n3. 고객 대응 가이드라인"
    elif "용어" in system_prompt or "glossary" in chatbot_type:
        context = "반도체 기술 분야에서 사용되는 전문 용어입니다."
        expertise = "- **개념**: 메모리 반도체 및 관련 기술에서 중요한 역할을 하는 용어\n- **분류**: 기술/공정/제품 사양 관련 용어\n- **적용 분야**: DDR 메모리, JEDEC 표준, 반도체 공정"
        docs = "1. **메모리 기술 용어**\n2. **JEDEC 표준 용어**\n3. **업무 전문 용어**"
    elif "JEDEC" in system_prompt or "jedec" in chatbot_type:
        context = "JEDEC 표준 문서 기반으로 답변드리겠습니다."
        expertise = "- **표준 규격**: 메모리 및 반도체 표준 준수 사항\n- **테스트 방법**: 표준 검증 절차 및 방법론\n- **호환성**: 업계 표준 호환성 요구사항"
        docs = "1. **JEDEC 표준 문서**\n2. **메모리 사양서**\n3. **테스트 방법론**"
    elif "품질" in system_prompt or "quality" in chatbot_type:
        context = "반도체 품질관리 분야의 전문 정보를 제공드리겠습니다."
        expertise = "- **품질 기준**: 반도체 제품 품질 표준 및 측정 방법\n- **불량 분석**: 원인 파악 및 개선 방안 제시\n- **프로세스**: 품질 관리 최적화 방법론"
        docs = "1. **품질 관리 프로세스**\n2. **불량 분석 방법**\n3. **ISO/TS 표준**"
    elif "테스트" in system_prompt or "test" in chatbot_type:
        context = "반도체 테스트엔지니어링 전문 정보를 제공드리겠습니다."
        expertise = "- **ATE 장비**: 자동 테스트 장비 운영 및 최적화\n- **테스트 프로그램**: 효율적인 테스트 방법론\n- **수율 분석**: 불량 패턴 분석 및 개선"
        docs = "1. **ATE 장비 운영**\n2. **테스트 프로그램 개발**\n3. **수율 개선 방법**"
    elif "설계" in system_prompt or "design" in chatbot_type:
        context = "반도체 설계엔지니어링 전문 정보를 제공드리겠습니다."
        expertise = "- **회로 설계**: 아날로그/디지털 회로 최적화\n- **레이아웃**: 면적 효율성 및 성능 최적화\n- **시뮬레이션**: SPICE 기반 설계 검증"
        docs = "1. **회로 설계 가이드**\n2. **레이아웃 최적화**\n3. **시뮬레이션 방법론**"
    else:
        context = "전문적인 답변을 제공드리겠습니다."
        expertise = "- 관련 기술 문서를 참조하여 답변드립니다\n- 정확한 정보를 바탕으로 설명드립니다"
        docs = "1. 관련 기술 문서\n2. 전문 자료"

    return f"""**🔍 {display_name} 응답 (Mock)**

**질문**: {user_message}

**답변**:
'{user_message}'에 대한 {context}

**📋 핵심 내용**:
{expertise}

**🔧 실무 적용**:
- 관련 문서를 참조하여 단계별로 진행하세요
- 문제 발생 시 팀 내 전문가와 상의하시기 바랍니다

**📚 참고 문서**:
{docs}

---
💡 **시스템 프롬프트 확인됨**: {display_name}로 동작 중
🔄 **Mock 데이터**: 실제 API 연결 시 더 정확한 답변 제공 예정"""

def call_rag_api_with_chatbot_type(user_message: str, chatbot_type: str) -> dict:
    """RAG API 호출 (실제 API 또는 Mock)"""
    from config import API_CONFIG, TEST_CONFIG, get_index_rag_name

    # Mock 모드인 경우
    if TEST_CONFIG.get("enable_mock_mode", True):
        return get_mock_rag_response(user_message, chatbot_type)

    # 실제 RAG API 호출
    try:
        import requests
        from datetime import datetime

        # RAG API 설정
        rag_config = API_CONFIG["rag_api_common"]
        base_url = rag_config["base_url"]

        if not base_url:
            logger.warning("RAG API base_url이 설정되지 않음. Mock 응답으로 대체")
            return get_mock_rag_response(user_message, chatbot_type)

        # 인덱스명 가져오기
        index_name = get_index_rag_name(chatbot_type)
        if not index_name:
            logger.warning(f"인덱스명을 찾을 수 없음: {chatbot_type}")
            return get_mock_rag_response(user_message, chatbot_type)

        # 요청 페이로드 구성
        payload = {
            "query": user_message,
            "index_name": index_name,
            "num_candidates": rag_config["num_candidates"],
            "num_result_doc": rag_config["num_result_doc"],
            "fields_exclude": rag_config["fields_exclude"],
            "user": rag_config["user"],
            "auth_list": rag_config["auth_list"]
        }

        # 날짜 기반 정렬 설정 추가
        if rag_config.get("sort_by_date", False):
            payload.update({
                "sort_config": {
                    "enable_date_sort": True,
                    "date_field": rag_config.get("date_field", "last_modified"),
                    "sort_order": rag_config.get("sort_order", "desc"),
                    "date_weight": rag_config.get("date_weight", 0.3),
                    "relevance_weight": rag_config.get("relevance_weight", 0.7),
                    "current_date": datetime.now().isoformat()
                }
            })

        # API 호출
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {rag_config['credential_key']}" if rag_config['credential_key'] else None
        }
        headers = {k: v for k, v in headers.items() if v is not None}

        response = requests.post(
            f"{base_url}/search",
            json=payload,
            headers=headers,
            timeout=rag_config["timeout"]
        )

        if response.status_code == 200:
            result = response.json()

            # 응답 데이터 정규화
            retrieved_documents = []
            source_info = []

            for doc in result.get("documents", []):
                retrieved_documents.append(doc.get("content", ""))
                source_info.append({
                    "source": doc.get("source", "Unknown"),
                    "page": doc.get("page", "1"),
                    "date": doc.get(rag_config.get("date_field", "last_modified"), ""),
                    "relevance_score": doc.get("score", 0.0),
                    "date_score": doc.get("date_score", 0.0)
                })

            return {
                "retrieved_documents": retrieved_documents,
                "source_info": source_info,
                "total_found": result.get("total_found", len(retrieved_documents)),
                "search_time": result.get("search_time", 0),
                "sorted_by_date": True
            }
        else:
            logger.error(f"RAG API 호출 실패: {response.status_code}")
            return get_mock_rag_response(user_message, chatbot_type)

    except Exception as e:
        logger.error(f"RAG API 호출 중 오류: {e}")
        return get_mock_rag_response(user_message, chatbot_type)

def call_llm_api(user_message: str, retrieve_data, chat_history=None, source_data=None, user_id=None, custom_system_prompt=None, chatbot_type="ae_wiki") -> str:
    """LLM API 호출 (Mock 버전)"""
    retrieve_text = " ".join(retrieve_data) if retrieve_data else ""
    source_citations = "Mock 출처 정보"
    system_prompt = custom_system_prompt or get_index_system_prompt(chatbot_type)

    return get_mock_llm_response(user_message, retrieve_text, source_citations, chatbot_type, system_prompt)

def format_source_citations(source_data, chatbot_type="ae_wiki") -> str:
    """출처 정보 포맷팅"""
    if not source_data:
        return "출처: Mock 데이터"

    citations = []
    for source in source_data:
        if isinstance(source, dict):
            source_name = source.get("source", "Unknown")
            page = source.get("page", "1")
            citations.append(f"📄 {source_name} (p.{page})")
        else:
            citations.append(f"📄 {source}")

    return "\n".join(citations)

def get_chatbot_response(user_message: str, chat_history=None, user_id=None, system_prompt=None, chatbot_type="ae_wiki") -> str:
    """통합 챗봇 응답 생성"""
    try:
        # RAG 검색
        rag_result = call_rag_api_with_chatbot_type(user_message, chatbot_type)
        retrieve_data = rag_result.get("retrieved_documents", [])
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
        logger.error(f"챗봇 응답 생성 실패: {e}")
        return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

# ====================================
# 💬 채팅 관리 기본 함수들
# ====================================

def save_chat_history(data, user_message: str, bot_response: str, chatbot_type: str = "ae_wiki") -> None:
    """채팅 기록 저장"""
    try:
        if "chat_history" not in data:
            data["chat_history"] = []

        chat_entry = {
            "timestamp": str(datetime.now()),
            "user_message": user_message,
            "bot_response": bot_response,
            "chatbot_type": chatbot_type,
            "user_id": get_user_id()
        }

        data["chat_history"].append(chat_entry)

        # 최근 100개만 유지
        if len(data["chat_history"]) > 100:
            data["chat_history"] = data["chat_history"][-100:]

        save_data(data)
        logger.info(f"채팅 기록 저장 완료: {chatbot_type}")

    except Exception as e:
        logger.error(f"채팅 기록 저장 실패: {e}")

def log_search(data, search_term: str, category_filter: str, results_count: int) -> None:
    """검색 로그 저장"""
    try:
        if "search_logs" not in data:
            data["search_logs"] = []

        search_entry = {
            "timestamp": str(datetime.now()),
            "search_term": search_term,
            "category_filter": category_filter,
            "results_count": results_count,
            "user_id": get_user_id()
        }

        data["search_logs"].append(search_entry)
        save_data(data)

    except Exception as e:
        logger.error(f"검색 로그 저장 실패: {e}")

# ====================================
# 📊 포인트 시스템 기본 함수들
# ====================================

def add_user_points(data, username: str, points: int, activity_type: str) -> None:
    """사용자 포인트 추가"""
    try:
        if "user_points" not in data:
            data["user_points"] = {}

        if username not in data["user_points"]:
            data["user_points"][username] = 0

        data["user_points"][username] += points
        save_data(data)

    except Exception as e:
        logger.error(f"포인트 추가 실패: {e}")

def get_user_points(data, username: str) -> int:
    """사용자 포인트 조회"""
    try:
        return data.get("user_points", {}).get(username, 0)
    except:
        return 0

def get_current_user_points(data) -> int:
    """현재 사용자 포인트 조회"""
    username = get_user_id()
    return get_user_points(data, username)

def set_user_points(data, username: str, new_points: int, admin_user: str = None) -> bool:
    """
    사용자 포인트 설정 (관리자 기능)

    Args:
        data: 메인 데이터
        username: 대상 사용자명
        new_points: 새로운 포인트 값
        admin_user: 관리자 사용자명

    Returns:
        bool: 성공 여부
    """
    try:
        if "user_points" not in data:
            data["user_points"] = {}

        old_points = data["user_points"].get(username, 0)
        data["user_points"][username] = max(0, new_points)  # 음수 방지

        # 포인트 변경 로그 기록
        if "point_changes" not in data:
            data["point_changes"] = []

        change_log = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "old_points": old_points,
            "new_points": new_points,
            "admin_user": admin_user or get_user_id(),
            "change_type": "manual_adjustment"
        }
        data["point_changes"].append(change_log)

        # 최근 100개 로그만 유지
        if len(data["point_changes"]) > 100:
            data["point_changes"] = data["point_changes"][-100:]

        save_data(data)
        logger.info(f"포인트 조정 완료: {username} {old_points} -> {new_points} (by {admin_user})")
        return True

    except Exception as e:
        logger.error(f"포인트 설정 실패: {e}")
        return False

def adjust_user_points(data, username: str, point_change: int, reason: str = "", admin_user: str = None) -> bool:
    """
    사용자 포인트 조정 (관리자 기능)

    Args:
        data: 메인 데이터
        username: 대상 사용자명
        point_change: 포인트 변경량 (양수: 추가, 음수: 차감)
        reason: 조정 사유
        admin_user: 관리자 사용자명

    Returns:
        bool: 성공 여부
    """
    try:
        if "user_points" not in data:
            data["user_points"] = {}

        old_points = data["user_points"].get(username, 0)
        new_points = max(0, old_points + point_change)  # 음수 방지
        data["user_points"][username] = new_points

        # 포인트 변경 로그 기록
        if "point_changes" not in data:
            data["point_changes"] = []

        change_log = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "old_points": old_points,
            "new_points": new_points,
            "point_change": point_change,
            "reason": reason,
            "admin_user": admin_user or get_user_id(),
            "change_type": "manual_adjustment"
        }
        data["point_changes"].append(change_log)

        # 최근 100개 로그만 유지
        if len(data["point_changes"]) > 100:
            data["point_changes"] = data["point_changes"][-100:]

        save_data(data)
        logger.info(f"포인트 조정 완료: {username} {old_points} -> {new_points} ({point_change:+d}) (by {admin_user})")
        return True

    except Exception as e:
        logger.error(f"포인트 조정 실패: {e}")
        return False

def get_all_user_points(data) -> dict:
    """
    모든 사용자 포인트 정보 조회 (데이터 통합)

    Args:
        data: 메인 데이터

    Returns:
        dict: 사용자별 포인트 정보 (nox_id 기준으로 통합)
    """
    try:
        raw_points = data.get("user_points", {})

        # 사용자 정보 가져오기
        users_list = get_all_users()
        user_mapping = {}

        # nox_id와 name 매핑 생성
        for user in users_list:
            nox_id = user.get('nox_id', '')
            name = user.get('nickname', user.get('name', ''))
            if nox_id:
                user_mapping[name] = nox_id  # name -> nox_id 매핑

        # 포인트 데이터 통합
        unified_points = {}

        for key, points in raw_points.items():
            # nox_id 기준으로 통합
            if key in user_mapping:
                # 이름으로 저장된 데이터를 nox_id로 변환
                nox_id = user_mapping[key]
                if nox_id in unified_points:
                    # 중복 데이터가 있으면 더 큰 값 사용 (최신 데이터 우선)
                    unified_points[nox_id] = max(unified_points[nox_id], points)
                else:
                    unified_points[nox_id] = points
            elif key in [user.get('nox_id', '') for user in users_list]:
                # 이미 nox_id로 저장된 데이터
                unified_points[key] = points
            else:
                # 매핑되지 않은 데이터는 그대로 유지
                unified_points[key] = points

        return unified_points

    except Exception as e:
        logger.error(f"포인트 데이터 통합 실패: {e}")
        return data.get("user_points", {})

def get_point_change_history(data, username: str = None, limit: int = 50) -> list:
    """
    포인트 변경 기록 조회

    Args:
        data: 메인 데이터
        username: 특정 사용자 (None이면 전체)
        limit: 최대 조회 개수

    Returns:
        list: 포인트 변경 기록 목록
    """
    try:
        all_changes = data.get("point_changes", [])

        if username:
            # 특정 사용자의 기록만 필터링
            user_changes = [change for change in all_changes if change.get("username") == username]
            return sorted(user_changes, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
        else:
            # 전체 기록
            return sorted(all_changes, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    except Exception as e:
        logger.error(f"포인트 기록 조회 실패: {e}")
        return []

def cleanup_duplicate_points_data(data, method: str = "keep_higher") -> bool:
    """
    중복된 포인트 데이터 정리 (관리자 기능)

    Args:
        data: 메인 데이터
        method: 정리 방법
            - "keep_current": 현재 데이터 유지 (레거시 데이터 삭제)
            - "keep_higher": 더 높은 포인트 값 유지
            - "sum_points": 포인트 합산 후 현재 키로 통합

    Returns:
        bool: 정리 성공 여부
    """
    try:
        raw_points = data.get("user_points", {})
        users_list = get_all_users()

        # 사용자 매핑 생성
        user_mapping = {}
        for user in users_list:
            nox_id = user.get('nox_id', '')
            name = user.get('nickname', user.get('name', ''))
            if nox_id and name:
                user_mapping[name] = nox_id

        # 통합된 포인트 데이터 생성
        cleaned_points = {}
        removed_keys = []

        for key, points in raw_points.items():
            if key in user_mapping:
                # 이름으로 저장된 데이터를 nox_id로 변환
                nox_id = user_mapping[key]

                if nox_id in cleaned_points:
                    # 중복이 있는 경우 method에 따라 처리
                    if method == "keep_current":
                        # 현재 nox_id 데이터 유지, 레거시만 제거
                        pass  # 기존 nox_id 값 유지
                    elif method == "keep_higher":
                        # 더 높은 값 유지
                        cleaned_points[nox_id] = max(cleaned_points[nox_id], points)
                    elif method == "sum_points":
                        # 포인트 합산
                        cleaned_points[nox_id] += points
                else:
                    cleaned_points[nox_id] = points

                removed_keys.append(key)
            else:
                # 매핑되지 않은 데이터는 그대로 유지
                cleaned_points[key] = points

        # 데이터 업데이트
        data["user_points"] = cleaned_points

        # 정리 로그 기록
        if removed_keys:
            if "data_cleanup_logs" not in data:
                data["data_cleanup_logs"] = []

            cleanup_log = {
                "timestamp": datetime.now().isoformat(),
                "operation": "points_data_cleanup",
                "method": method,
                "removed_keys": removed_keys,
                "admin_user": get_user_id() if 'get_user_id' in globals() else "system"
            }
            data["data_cleanup_logs"].append(cleanup_log)

        save_data(data)
        logger.info(f"포인트 데이터 정리 완료 ({method}): {len(removed_keys)}개 중복 제거")
        return True

    except Exception as e:
        logger.error(f"포인트 데이터 정리 실패: {e}")
        return False

# ====================================
# 🎨 UI 컴포넌트 기본 함수들
# ====================================

def display_typing_effect(text: str, container, delay: float = None) -> None:
    """타이핑 효과 표시 (간소화 버전)"""
    container.markdown(text)

def load_css_styles() -> str:
    """CSS 스타일 로드 (기본 스타일)"""
    return """
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
    """

# ====================================
# 📝 Q&A 시스템 기본 함수들
# ====================================

def search_questions(data, search_term: str = "", category_filter: str = "전체"):
    """질문 검색"""
    questions = data.get("questions", [])
    if not questions:
        return []

    # 간단한 필터링
    if category_filter != "전체":
        questions = [q for q in questions if q.get("category") == category_filter]

    if search_term:
        questions = [q for q in questions if search_term.lower() in q.get("title", "").lower()]

    return questions

def add_question(data, title: str, category: str, content: str, anonymous: bool = False) -> str:
    """질문 추가"""
    try:
        if "questions" not in data:
            data["questions"] = []

        # 익명 옵션에 따라 작성자 설정
        if anonymous:
            author = "익명"
            author_id = "anonymous"
        else:
            author = get_user_id()
            author_id = get_user_id()

        question = {
            "id": len(data["questions"]) + 1,
            "title": title,
            "category": category,
            "content": content,
            "author": author,
            "author_id": author_id,
            "timestamp": str(datetime.now())
        }

        data["questions"].append(question)
        save_data(data)
        return "질문이 성공적으로 등록되었습니다."

    except Exception as e:
        logger.error(f"질문 추가 실패: {e}")
        return "질문 등록 중 오류가 발생했습니다."

# ====================================
# 📅 날짜/시간 유틸리티
# ====================================

from datetime import datetime

# ====================================
# 🔧 기타 호환성 함수들
# ====================================

def validate_nox_id(nox_id: str):
    """NOX ID 유효성 검증"""
    return True, "유효한 ID입니다."

def validate_nickname(nickname: str):
    """닉네임 유효성 검증"""
    return True, "유효한 닉네임입니다."

def validate_department(department: str):
    """부서명 유효성 검증"""
    return True, "유효한 부서명입니다."

# ====================================
# 👥 사용자 관리 시스템 (관리자 페이지용)
# ====================================

def get_all_users():
    """
    전체 사용자 목록 반환 (새 통합 시스템 활용)

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
        return []

def search_users(keyword: str = ""):
    """
    사용자 검색

    Args:
        keyword: 검색 키워드 (빈 문자열이면 전체 목록)

    Returns:
        List[Dict]: 검색 조건에 맞는 사용자 목록
    """
    all_users = get_all_users()

    if not keyword:
        return all_users

    # 키워드로 필터링
    filtered_users = []
    keyword_lower = keyword.lower()

    for user in all_users:
        if (keyword_lower in user.get("nox_id", "").lower() or
            keyword_lower in user.get("nickname", "").lower() or
            keyword_lower in user.get("department", "").lower()):
            filtered_users.append(user)

    return filtered_users

def toggle_user_status(user_id: str) -> bool:
    """
    사용자 활성/비활성 상태 토글

    Args:
        user_id: 사용자 ID

    Returns:
        bool: 성공 여부
    """
    try:
        from user_manager import toggle_user_active_status
        return toggle_user_active_status(user_id)
    except Exception as e:
        logger.error(f"사용자 상태 토글 실패: {e}")
        return False

def delete_user(user_id: str) -> bool:
    """
    사용자 삭제

    Args:
        user_id: 사용자 ID

    Returns:
        bool: 성공 여부
    """
    try:
        from user_manager import delete_user_account
        return delete_user_account(user_id)
    except Exception as e:
        logger.error(f"사용자 삭제 실패: {e}")
        return False

def update_user_info(user_id: str, nickname: str, department: str):
    """
    사용자 정보 업데이트

    Args:
        user_id: 사용자 ID
        nickname: 새 닉네임
        department: 새 부서

    Returns:
        tuple: (성공여부, 메시지)
    """
    try:
        from user_manager import update_user_profile
        success = update_user_profile(user_id, {
            "nickname": nickname,
            "department": department
        })
        if success:
            return True, "사용자 정보가 성공적으로 업데이트되었습니다."
        else:
            return False, "사용자 정보 업데이트에 실패했습니다."
    except Exception as e:
        logger.error(f"사용자 정보 업데이트 실패: {e}")
        return False, f"업데이트 중 오류가 발생했습니다: {e}"

def get_pending_registration_requests(data):
    """
    대기 중인 회원가입 신청 목록 조회

    Args:
        data: 메인 데이터

    Returns:
        List[Dict]: 대기 중인 신청 목록
    """
    try:
        from user_manager import get_pending_requests
        return get_pending_requests()
    except Exception as e:
        logger.error(f"대기 신청 목록 조회 실패: {e}")
        return data.get("registration_requests", [])

def approve_registration_request(data, request_id: int, admin_username: str):
    """
    회원가입 신청 승인

    Args:
        data: 메인 데이터
        request_id: 신청 ID
        admin_username: 승인하는 관리자 사용자명

    Returns:
        tuple: (성공여부, 메시지)
    """
    try:
        from user_manager import approve_registration_request as approve_new
        success, message = approve_new(request_id, admin_username)
        return success, message
    except Exception as e:
        logger.error(f"신청 승인 실패: {e}")
        return False, f"승인 처리 중 오류가 발생했습니다: {e}"

def reject_registration_request(data, request_id: int, admin_username: str, reason: str = ""):
    """
    회원가입 신청 거부

    Args:
        data: 메인 데이터
        request_id: 신청 ID
        admin_username: 거부하는 관리자 사용자명
        reason: 거부 사유

    Returns:
        tuple: (성공여부, 메시지)
    """
    try:
        from user_manager import reject_registration_request as reject_new
        success, message = reject_new(request_id, admin_username, reason)
        return success, message
    except Exception as e:
        logger.error(f"신청 거부 실패: {e}")
        return False, f"거부 처리 중 오류가 발생했습니다: {e}"

# ====================================
# 📊 답변 랭킹 시스템
# ====================================

def get_answer_ranking(data):
    """답변 랭킹 조회"""
    return []  # 기본 구현

def get_user_points_ranking(data):
    """사용자 포인트 랭킹 조회"""
    user_points = data.get("user_points", {})
    ranking = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
    return ranking[:10]  # 상위 10명

# ====================================
# 📝 Q&A 추가 함수들
# ====================================

def add_answer(data, question_id: str, content: str) -> str:
    """답변 추가"""
    try:
        if "answers" not in data:
            data["answers"] = []

        answer = {
            "id": len(data["answers"]) + 1,
            "question_id": question_id,
            "content": content,
            "author": get_user_id(),
            "timestamp": str(datetime.now()),
            "likes": 0
        }

        data["answers"].append(answer)
        save_data(data)
        return "답변이 성공적으로 등록되었습니다."

    except Exception as e:
        logger.error(f"답변 추가 실패: {e}")
        return "답변 등록 중 오류가 발생했습니다."

def toggle_like(data, answer_id: str) -> bool:
    """답변 좋아요 토글"""
    try:
        user_id = get_user_id()
        if "likes" not in data:
            data["likes"] = {}

        like_key = f"{answer_id}_{user_id}"

        if like_key in data["likes"]:
            # 좋아요 취소
            del data["likes"][like_key]
            liked = False
        else:
            # 좋아요 추가
            data["likes"][like_key] = True
            liked = True

        save_data(data)
        return liked

    except Exception as e:
        logger.error(f"좋아요 토글 실패: {e}")
        return False

def delete_question(data, question_id: str) -> None:
    """질문 삭제"""
    try:
        questions = data.get("questions", [])
        data["questions"] = [q for q in questions if str(q.get("id")) != str(question_id)]

        # 관련 답변도 삭제
        answers = data.get("answers", [])
        data["answers"] = [a for a in answers if str(a.get("question_id")) != str(question_id)]

        save_data(data)

    except Exception as e:
        logger.error(f"질문 삭제 실패: {e}")

# ====================================
# 📝 회원가입 신청 시스템
# ====================================

def submit_registration_request(username: str, name: str, department: str, password: str):
    """
    회원가입 신청 제출 (새 시스템으로 리다이렉트)

    Args:
        username: 녹스아이디 (로그인 시 사용할 ID)
        name: 실명
        department: 소속 부서
        password: 비밀번호

    Returns:
        tuple: (성공여부, 메시지)
    """
    try:
        from user_manager import add_registration_request
        return add_registration_request(username, name, department, password)
    except Exception as e:
        logger.error(f"회원가입 신청 실패: {e}")
        return False, "회원가입 신청 중 오류가 발생했습니다"

def submit_registration_request_legacy(username: str, name: str, department: str, password: str):
    """
    회원가입 신청 제출 (레거시 시스템)

    Args:
        username: 녹스아이디
        name: 실명
        department: 소속 부서
        password: 비밀번호

    Returns:
        tuple: (성공여부, 메시지)
    """
    try:
        import bcrypt

        # 비밀번호 해시화
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # 메인 데이터에 신청 정보 저장
        data = initialize_data()

        if "registration_requests" not in data:
            data["registration_requests"] = []

        # 중복 신청 확인
        for existing_request in data["registration_requests"]:
            if existing_request.get("username") == username:
                return False, "이미 신청한 계정입니다. 승인 대기 중입니다."

        # 새 신청 추가
        request = {
            "id": len(data["registration_requests"]) + 1,
            "username": username,
            "name": name,
            "department": department,
            "password": hashed_password.decode('utf-8'),
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }

        data["registration_requests"].append(request)
        save_data(data)

        return True, "회원가입 신청이 완료되었습니다. 관리자 승인을 기다려주세요."

    except Exception as e:
        logger.error(f"회원가입 신청 실패: {e}")
        return False, f"회원가입 신청 중 오류가 발생했습니다: {e}"

# 로깅 메시지
logger.info("통합 유틸리티 모듈 로드 완료 - 모듈형 구조로 리팩토링됨")