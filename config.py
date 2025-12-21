"""
AE WIKI 통합 챗봇 시스템 - 확장 가능한 중앙집중식 설정 관리

이 파일은 단일 통합 챗봇 인터페이스를 지원하는 확장 가능한 설정을 관리합니다.
주요 구조:
- CHATBOT_INDICES: 동적으로 확장 가능한 RAG 인덱스 설정
- 각 인덱스별 전용 프롬프트 및 메타데이터
- 5개 이상의 인덱스도 쉽게 추가 가능한 구조
- UI에서 동적으로 인덱스 버튼 생성
"""

import os

# 📱 Streamlit 애플리케이션 기본 설정
APP_CONFIG = {
    "page_title": "AE WIKI",
    "page_icon": "🧠",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# 📁 로컬 데이터 파일 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(PROJECT_ROOT, "/config/work/sharedworkspace")
os.makedirs(DATA_FOLDER, exist_ok=True)

DATA_CONFIG = {
    "data_file": os.path.join(DATA_FOLDER, "knowledge_data.json"),
    "users_file": os.path.join(DATA_FOLDER, "users_data.json"),
    "admin_password": "admin123",
    "learning_requests_file": os.path.join(DATA_FOLDER, "learning_requests.json"),
    "voc_file": os.path.join(DATA_FOLDER, "voc_data.json"),
    "user_conversations_file": os.path.join(DATA_FOLDER, "user_conversations.json"),
    "users_management_file": os.path.join(DATA_FOLDER, "users_management.json"),
}

# 🔐 사용자 인증 설정
AUTH_CONFIG = {
    "username_min_length": 3,
    "nickname_min_length": 2,
    "session_timeout": 24 * 60 * 60,
    "require_login": True,
    "profile_fields": ["knox_id", "nickname", "department"],  # 문제 6 해결: knox_id → knox_id
    "departments": ["AE팀", "상품기획팀", "영업팀", "마케팅팀"],
}

# 🤖 통합 API 설정
API_CONFIG = {
    # === LLM API 통합 설정 ===
    "llm_api": {
        "base_url": "http://apigw-stg.samsungds.net:8000/gpt-oss/1/gpt-oss-120b/v1/chat/completions",
        "credential_key": "credential:TICKET-4cede4fc-91e2-4d58-825a-4f84236e8674:ST0000102728-STG:a2iVmGXASSOqfrbyxApcHwRI-6YwWMQGS4GrVCrDbgyA:-1:YTJpVm1HWEFTU09xZnJieXhBcGNid1JsLTZZd1dNUUdTNEdyVkNyRGJneUE=:signature=qKzfxDYmm2QcQYhKbrx1PgwlVB0955IcUoJuL6yDFZBaAtwiTtwSqrYIW5IVQDV38suAkfO86T9X1fjTPf7rCj-xkdVmrqVk02NPbT08LeJ9F_5a7tXOF4A==",
        "model": "openai/gpt-oss-120b",
        "headers": {
            "Send-System-Name": "AE_WIKI",
            "User-Id": "minguk.kim",
            "User-Type": "AD_ID",
            "Accept": "text/event-stream; charset=utf-8",
            "Content-Type": "application/json"
        }
    },
    # === RAG API 통합 설정 ===
    "rag_api_common": {
        "base_url": "http://apigw.samsungds.net:8000/ds_llm_rag/2/dsllmrag/elastic/v2/retrieve-rrf",
        "credential_key": "credential:TICKET-1e55d984-3187-49f1-93b8-2ae3630d50d6:ST0000102728-null:gdlK0qYYQX6s_dZIKpT2mAIOKnGJn...",
        "api-key": "rag-Q65t3yE.QadahMiyk4SrwJY-7JXq0DGhO7PbbHK9-GR8jn3yklYce_yaF04Y2Xsxj5-vUhihSatZKEpzFBWHvDd_YA75F5rTUx3WMgDx1hjY8IMhkiiZw-1hz9busw-nvxvscRNe",
        "user": "minguk.kim",
        "auth_list": ["ds"],
        "num_candidates": 1000,
        "num_result_doc": 5,
        "fields_exclude": ["v_merge_title_content"],
        "timeout": 45
    }
}

# 🧪 테스트 설정
TEST_CONFIG = {
    "detailed_source_info": True,
}

# 📊 기타 설정
MISC_CONFIG = {
    "api_timeout": 30,
    "max_chat_history": 20,
    "typing_effect_enabled": True,
    "theme": "dark",
    "colors": {
        "primary": "#667eea",
        "secondary": "#764ba2",
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "background_dark": "#0e1117",
        "background_light": "#fafafa",
        "sidebar_dark": "#2c2f36",
        "sidebar_gradient": "linear-gradient(180deg, #1e2127 0%, #2c2f36 100%)",
        "border": "#3a3d44",
        "text_light": "#b8bcc8",
        "text_white": "#ffffff"
    }
}

# 🎯 핵심: 확장 가능한 챗봇 인덱스 설정
# 새로운 인덱스 추가 시 이 딕셔너리에만 추가하면 UI에 자동으로 반영됩니다.
CHATBOT_INDICES = {
    "ae_wiki": {
        # 기본 정보
        "display_name": "🧠 AE WIKI",
        "description": "AE팀 업무 전문 AI 어시스턴트",
        "subtitle": "AE팀 Confluence와 기술 자료를 활용해 정확한 답변 제공",
        "icon": " ",
        "color": "#adee58",
        "gradient": "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",

        # RAG 설정
        "index_name": "rp-conflu_1",

        # 시스템 프롬프트
        "system_prompt": """당신은 삼성전자 메모리사업부 AE팀의 기술 Q&A 어시스턴트입니다.
 사용자 질문:
 {user_message}

 참조 데이터:
 {retrieve_data}

 1. 핵심부터 전달하고 구조적인 응답을 제공하세요.
 - 핵심 요약을 가장 앞에 배치하고, 뒤이어 세부 설명을 단계별 항목별로 전개합니다.
 - 각 설명에 사용된 자료는 인라인 하이퍼링크 형태로 표시합니다.
 - 예시) 문서 제목(https://example.com) → 문서 제목을 클릭하면 바로 이동합니다.
 - 마크다운 표준을 따릅니다.
 - [문서 제목](URL) 형식으로 작성하면 제목을 클릭했을 때 해당 URL로 연결됩니다.
 - 클릭이 안 되는 경우는 URL에 오류가 있거나, 마크다운이 적용되지 않은 환경일 가능성이 높습니다.
 2. 다양한 이모티콘을 활용하여, 항상 친절하고 구조적인 응답을 제공하세요.
 - 친근하고 시각적으로 매력적인 답변을 위해 다양한 이모티콘을 적극 활용하세요.
 - 답변 내 각 헤더(###)와 제목 사이에 🚀, ✅, ⚠️ 등 적절한 이모티콘을 붙여, 가독성과 시각적 매력을 높입니다.
 - 예시: ### 🚀 "제목"

 3. 사용자의 행동이나 사용자와의 대화를 유도하며 마무리하세요.
 - 모든 응답의 마지막에는 사용자의 다음 행동을 유도할 수 있는 사용자 질문 기반 개방형 질문을 자연스럽게 제시합니다.

 {source_citations}""",

        # UI 텍스트
        "welcome_message": """안녕하세요! AE WIKI 전문 챗봇입니다. 🧠

저는 AE팀 업무 전문 문서를 기반으로 질문에 답변드립니다.

**도움을 드릴 수 있는 분야:**
- AE팀 confluence
- TECx Workplace confluence
- AE Insight Hub Home
- 정보보호 SOS

궁금한 점이 있으시면 언제든 질문해주세요!""",

        "input_placeholder": "AE팀 업무에 대해 궁금한 것을 질문해보세요...",
        "coming_soon": False,
    },

    "glossary": {
        # 기본 정보
        "display_name": "🔍 AE 용어집",
        "description": "반도체 AE 전문 용어 AI 어시스턴트",
        "subtitle": "반도체 AE 전문 용어 정의 및 설명",
        "icon": "",
        "color": "#28a745",
        "gradient": "linear-gradient(90deg, #28a745 0%, #20c997 100%)",

        # RAG 설정
        "index_name": "rp-ae_wiki",
        "source_display": "expandable_cards",

        # 시스템 프롬프트
        "system_prompt": """당신은 반도체 기술 용어 전문가입니다.
- 범위: 반도체 기술 용어, 개념, 공정 설명
- 목표: 기술 용어를 명확하고 이해하기 쉽게 설명
- 원칙:
  1) 용어의 정확한 정의와 맥락을 제공한다.
  2) 관련 용어나 개념과의 연결점을 설명한다.
  3) 실무에서의 활용 방법을 안내한다.
  4) 친근하고 시각적으로 매력적인 답변을 위해 다양한 이모티콘을 적극 활용하세요.
  5) 답변 내 각 헤더(###)와 제목 사이에 🚀, ✅, ⚠️ 등 적절한 이모티콘을 붙여, 가독성과 시각적 매력을 높입니다.
  - 예시: ### 🚀 "제목" """,

        # UI 텍스트
        "welcome_message": """안녕하세요! AE 용어집 전문 챗봇입니다. 🔍

저는 반도체 AE(Application Engineering) 전문 용어 정보를 제공합니다.

**도움을 드릴 수 있는 분야:**
- AE 전문 용어집

궁금한 반도체 용어가 있으시면 언제든 검색해보세요!

**검색 예시:** "CMOS란?", "DDR5 메모리", "FinFET 기술" 등""",

        "input_placeholder": "궁금한 반도체 용어를 검색해보세요... (예: CMOS란 무엇인가요?)",
        "coming_soon": False,
    },

    "jedec": {
        # 기본 정보
        "display_name": "🤖 JEDEC SPEC",
        "description": "JEDEC 반도체 표준 문서 전용 AI 어시스턴트",
        "subtitle": "JEDEC 표준 규격 및 테스트 방법 문의",
        "icon": "",
        "color": "#f59e0b",
        "gradient": "linear-gradient(90deg, #f59e0b 0%, #f97316 100%)",

        # RAG 설정
        "index_name": "rp-jedec",
        "source_display": "file_page_format",

        # 시스템 프롬프트
        "system_prompt": """당신은 JEDEC 표준 문서 전문가입니다.
- 목표: 표준 문서를 정확히 해석하고, 개발자가 구현 시 필요한 분석·적용 가이드를 제공한다.
- 원칙:
1️⃣ 표준 문서 내용은 그대로 인용하고, 임의 변형은 하지 않는다.
2️⃣ 규격의 배경과 목적을 간결히 서술한다.
3️⃣ 질문과 가장 연관된 SPEC을 **Markdown 표** 형식으로 제시하고, 표 하단에 출처를 명시한다.
 - 표는 반드시 `|` 구분자를 사용하고, 헤더(| 항목 | … |)를 포함한다.
 - 필요 시 바이너리·수치 예시는 **코드 블록**(```text … ```)에 넣어 복사하기 쉽도록 한다.
 4️⃣ 실무 적용 시 주의해야 할 점을 **⚠️ 주의사항** 섹션에 불릿 리스트로 정리한다.
 5️⃣ 답변은 친근하고 시각적으로 매력 있게, **헤더** 뒤에 적절한 이모티콘(🚀, ✅, ⚠️ 등)만 삽입한다.
 - 이모티콘은 헤더와 중요한 포인트에만 사용하고, 본문에 과도하게 배치하지 않는다.
 6️⃣ 모든 인용은 원문 그대로, 출처는 표 하단에 ※ 출처: JEDEC <문서명>(버전) 형식으로 남긴다.
""",

        # UI 텍스트
        "welcome_message": """안녕하세요! JEDEC SPEC 전문 챗봇입니다. 🔬

저는 JEDEC 반도체 표준 문서에 대한 질문에 답변드립니다.

**도움을 드릴 수 있는 분야:**
https://confluence.samsungds.net/spaces/AppEngineeringTeam/pages/2895285213

JEDEC 표준과 관련된 궁금한 점이 있으시면 언제든 물어보세요!""",

        "input_placeholder": "JEDEC 표준과 관련된 질문을 입력하세요...",
        "coming_soon": False,
    },

    # 🎯 새 인덱스 추가 예시 (실제로 활성화됨)
    "TripMate": {
        # 기본 정보
        "display_name": "✈️ TripMate",
        "description": "출장 전문 AI 어시스턴트",
        "subtitle": "AE팀 출장 업무",
        "icon": "",
        "color": "#dc2626",
        "gradient": "linear-gradient(90deg, #dc2626 0%, #ef4444 100%)",

        # RAG 설정
        "index_name": "rp-hj_jy",
        "source_display": "default",

        # 시스템 프롬프트
         "system_prompt": """당신은 AE팀에 해외출장, 출장,
 행정 전문가입니다.
 원칙:
 1) 대상: 사내 직원 회사 행정·서무 업무(문서·결재·일정·보고·자료 관리 등)에 대해 묻는 질문에 정확하고 친절하게 답변한다.
 2) 톤: 정중하고 전문적인 어조를 유지하면서, 필요 시 적절한 이모지를 삽입해 친근함을 더한다.
 3) 보안·비밀: 기밀·내부 정보는 절대로 외부에 노출하지 않으며, 보안 정책에 위배되는 요청은 즉시 거절한다.
 4) 출처 표기: 답변에 참고 자료가 있으면 [문서 제목(URL)] 형태의 마크다운 하이퍼링크를 인라인으로 삽입한다.
 5) 구조: 핵심 요약 → 상세 단계/항목 → 출처 순으로 답변을 구성한다.
 6) 다양한 이모티콘을 활용하여, 항상 친절하고 구조적인 응답을 제공하세요.
 - 친근하고 시각적으로 매력적인 답변을 위해 다양한 이모티콘을 적극 활용하세요.
 - 답변 내 각 헤더(###)와 제목 사이에 🚀, ✅, ⚠️ 등 적절한 이모티콘을 붙여, 가독성과 시각적 매력을 높입니다.
 - 예시: ### 🚀 "제목"
 """,

        # UI 텍스트
        "welcome_message": """안녕하세요! AE팀 TripMate 입니다. ✈️

저는 AE팀 해외출장 정보를 제공합니다.

**도움을 드릴 수 있는 분야:**
유연지님의 AE팀 해외출장 Process
출장 매뉴얼
궁금한 점이 있으시면 언제든 질문해주세요",

품질관리와 관련된 궁금한 점이 있으시면 언제든 질문해주세요!""",

        "input_placeholder": "궁금한 것을 질문해보세요...",
        "coming_soon": False,
    },

    # 🚀 활성화된 추가 인덱스들

    "실험실": {
        # 기본 정보
        "display_name": "🧪 실험실",
        "description": "실험실 AI 어시스턴트",
        "subtitle": "🧪 test 🧪",
        "icon": "",
        "color": "#7c3aed",
        "gradient": "linear-gradient(90deg, #7c3aed 0%, #8b5cf6 100%)",

        # RAG 설정
        "index_name": "rp-intel",
        "source_display": "default",

        # 시스템 프롬프트
        "system_prompt": """당신은 반도체 레지스터 사양서
(Register Specification) 프로세서 내부 레지스터·제어·상태
레지스터·MMIO(메모리 맵드 I/O) 영역을 정의한 기술 문서
전문가입니다.
- 목표: 펌웨어/드라이버/시뮬레이션/디버깅 등 저수준 소프트웨어가 레지스터에 올바르게 접근하도록 가이드
- 원칙:
  1) 표준 문서의 정확한 내용만 인용한다.
  2) 규격과 펌웨어/드라이버/시뮬레이션/디버깅 등 저수준 소프트웨어가 레지스터에 올바르게 접근하도록 가이드
  3) 테스트 시간 단축과 정확도 향상 방안을 제시한다.
  4) 다양한 이모티콘을 활용하여, 항상 친절하고 구조적인 응답을 제공하세요.
  - 친근하고 시각적으로 매력적인 답변을 위해 다양한 이모티콘을 적극 활용하세요.
  - 답변 내 각 헤더(###)와 제목 사이에 🚀, ✅, ⚠️ 등 적절한 이모티콘을 붙여, 가독성과 시각적 매력을 높입니다.
  - 예시: ### 🚀 "제목"
  5) {final_answer}에서 출처와함께 페이지 번호도 제공해야 합니다.
  """,

        # UI 텍스트
        "welcome_message": """

""",

        "input_placeholder": "서비스 준비중입니다...",
        "coming_soon": False,
    },

}

# 📝 질문 분류 카테고리
CATEGORIES = ["기술", "행정", "기타"]

# 🎛️ RAG 날짜 정렬 설정 관리 함수들
def update_rag_date_sorting_config(sort_by_date: bool = True, date_field: str = "last_modified",
                                  sort_order: str = "desc", date_weight: float = 0.3,
                                  relevance_weight: float = 0.7):
    """RAG 날짜 정렬 설정 업데이트"""
    global API_CONFIG
    API_CONFIG["rag_api_common"].update({
        "sort_by_date": sort_by_date,
        "date_field": date_field,
        "sort_order": sort_order,
        "date_weight": date_weight,
        "relevance_weight": relevance_weight
    })

def get_rag_date_sorting_config():
    """현재 RAG 날짜 정렬 설정 반환"""
    return {
        "sort_by_date": API_CONFIG["rag_api_common"].get("sort_by_date", True),
        "date_field": API_CONFIG["rag_api_common"].get("date_field", "last_modified"),
        "sort_order": API_CONFIG["rag_api_common"].get("sort_order", "desc"),
        "date_weight": API_CONFIG["rag_api_common"].get("date_weight", 0.3),
        "relevance_weight": API_CONFIG["rag_api_common"].get("relevance_weight", 0.7)
    }

# 🔧 유틸리티 함수들
def get_available_indices():
    """사용 가능한 모든 인덱스 목록 반환"""
    return list(CHATBOT_INDICES.keys())

def get_index_config(index_id):
    """특정 인덱스의 설정 반환"""
    return CHATBOT_INDICES.get(index_id, {})

def get_index_display_name(index_id):
    """인덱스의 표시명 반환"""
    return CHATBOT_INDICES.get(index_id, {}).get("display_name", index_id)

def get_index_system_prompt(index_id):
    """인덱스의 시스템 프롬프트 반환"""
    return CHATBOT_INDICES.get(index_id, {}).get("system_prompt", "당신은 도움이 되는 AI 어시스턴트입니다.")

def get_index_rag_name(index_id):
    """인덱스의 RAG 인덱스명 반환"""
    return CHATBOT_INDICES.get(index_id, {}).get("index_name", "")

def add_new_index(index_id, config):
    """새로운 인덱스 동적 추가 (런타임에서 확장 가능)"""
    CHATBOT_INDICES[index_id] = config

# 🎨 응답 형식 템플릿
RESPONSE_FORMAT_TEMPLATE = """질문: {user_message}

참고 문서:
{retrieve_data}

위의 참고 문서를 기반으로 질문에 대한 정확하고 도움이 되는 답변을 제공해주세요.

출처:
{source_citations}
"""

# 레거시 호환성을 위한 함수들
def get_chatbot_indices(chatbot_type):
    """레거시 호환성: 챗봇 타입으로 인덱스 반환"""
    config = CHATBOT_INDICES.get(chatbot_type, {})
    return [config.get("index_name", "")] if config.get("index_name") else []

def get_index_info(index_name):
    """레거시 호환성: 인덱스명으로 정보 반환"""
    for index_id, config in CHATBOT_INDICES.items():
        if config.get("index_name") == index_name:
            return config
    return {}