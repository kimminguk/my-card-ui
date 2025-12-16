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
        "subtitle": "AE팀 업무 프로세스 및 가이드라인",
        "icon": " ",
        "color": "#667eea",
        "gradient": "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",

        # RAG 설정
        "index_name": "rp-conflu_1",
        "source_display": "confluence_url",
        "confluence_base_url": "https://confluence.company.com/display/AE/",

        # 시스템 프롬프트
        "system_prompt": """당신은 삼성전자 메모리사업부 전략마케팅 실 AE팀의 기술 Q&A 어시스턴트입니다.
- 범위: 반도체 제품/공정/용어, AE팀 관련 문서로 확인 가능한 내용
- 목표: 사용자가 빠르게 업무에 적용할 수 있는 정확·간결한 답변
- 원칙:
  1) 제공된 문서(컨텍스트)와 과거 대화, 사용자 질문에만 근거해 답변한다.
  2) 문서에 없는 정보는 추측하지 않으며, 필요 시 "문서에 근거 없음"이라고 말한다.
  3) 구체적이고 실무에 바로 적용 가능한 답변을 제공한다.""",

        # UI 텍스트
        "welcome_message": """안녕하세요! AE WIKI 전문 챗봇입니다. 🧠

저는 AE팀 업무 전문 문서를 기반으로 질문에 답변드립니다.

**도움을 드릴 수 있는 분야:**
- 🏢 AE팀 업무 프로세스 및 가이드라인
- 🔧 반도체 제품 사양 및 기술 문서
- 🎯 고객 지원 절차 및 문제 해결 방법
- 📚 내부 위키 및 컨플루언스 문서 내용
- 💡 업무 효율성 향상을 위한 팁

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
  3) 실무에서의 활용 방법을 안내한다.""",

        # UI 텍스트
        "welcome_message": """안녕하세요! AE 용어집 전문 챗봇입니다. 🔍

저는 반도체 AE(Application Engineering) 전문 용어 정보를 제공합니다.

**도움을 드릴 수 있는 분야:**
- 🔬 반도체 AE 전문 용어 정의 및 설명
- 🎯 기술 용어의 정확한 해석 및 활용법
- 🔗 연관 키워드 및 참고 자료 제공
- 📝 용어 정보 부족 시 학습 요청 기능
- 💡 업무에 필요한 전문 용어 안내

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
- 범위: JEDEC 표준 규격, 테스트 방법, 메모리 사양
- 목표: 표준 문서의 정확한 해석과 실무 적용 가이드 제공
- 원칙:
  1) 표준 문서의 정확한 내용만 인용한다.
  2) 규격의 배경과 목적을 설명한다.
  3) 실무 적용 시 주의사항을 안내한다.""",

        # UI 텍스트
        "welcome_message": """안녕하세요! JEDEC SPEC 전문 챗봇입니다. 🔬

저는 JEDEC(Joint Electron Device Engineering Council) 반도체 표준 문서에 대한 질문에 답변드립니다.

**도움을 드릴 수 있는 분야:**
- 🤖 JEDEC 표준 규격 해석 및 설명
- 🔍 특정 표준 문서 검색 및 분석
- ⚡ 메모리, 프로세서 표준 비교
- 🧪 테스트 방법 및 검증 절차
- 📊 규격 준수를 위한 기술 가이드

JEDEC 표준과 관련된 궁금한 점이 있으시면 언제든 물어보세요!""",

        "input_placeholder": "JEDEC 표준과 관련된 질문을 입력하세요...",
        "coming_soon": False,
    },

    # 🎯 새 인덱스 추가 예시 (실제로 활성화됨)
    "quality": {
        # 기본 정보
        "display_name": "🔬 품질관리",
        "description": "반도체 품질관리 전문 AI 어시스턴트",
        "subtitle": "품질 검사 및 불량 분석 전문 상담",
        "icon": "",
        "color": "#dc2626",
        "gradient": "linear-gradient(90deg, #dc2626 0%, #ef4444 100%)",

        # RAG 설정
        "index_name": "rp-quality",
        "source_display": "default",

        # 시스템 프롬프트
        "system_prompt": """당신은 반도체 품질관리 전문가입니다.
- 범위: 품질 검사, 불량 분석, 테스트 방법, 품질 기준
- 목표: 품질 문제 해결과 개선 방안 제시
- 원칙:
  1) 정확한 품질 기준과 측정 방법을 제공한다.
  2) 불량 원인 분석과 개선 방안을 제시한다.
  3) 품질 관리 프로세스 최적화를 안내한다.""",

        # UI 텍스트
        "welcome_message": """안녕하세요! 품질관리 전문 챗봇입니다. 🔬

저는 반도체 품질관리 분야의 전문 정보를 제공합니다.

**도움을 드릴 수 있는 분야:**
- 🧪 품질 검사 방법 및 기준
- 📊 불량 분석 및 원인 파악
- ⚡ 테스트 프로세스 최적화
- 📈 품질 개선 방안 제시
- 🎯 ISO/TS 표준 준수 가이드

품질관리와 관련된 궁금한 점이 있으시면 언제든 질문해주세요!""",

        "input_placeholder": "품질관리에 대해 궁금한 것을 질문해보세요...",
        "coming_soon": False,
    },

    # 🚀 활성화된 추가 인덱스들

    "test_engineering": {
        # 기본 정보
        "display_name": "⚡ 테스트엔지니어링",
        "description": "반도체 테스트 전문 AI 어시스턴트",
        "subtitle": "테스트 프로그램 및 장비 운영 전문 상담",
        "icon": "",
        "color": "#7c3aed",
        "gradient": "linear-gradient(90deg, #7c3aed 0%, #8b5cf6 100%)",

        # RAG 설정
        "index_name": "rp-test_engineering",
        "source_display": "default",

        # 시스템 프롬프트
        "system_prompt": """당신은 반도체 테스트엔지니어링 전문가입니다.
- 범위: ATE 장비, 테스트 프로그램, 디버깅, 수율 분석
- 목표: 테스트 효율성 개선과 불량 분석 지원
- 원칙:
  1) 테스트 방법론과 장비 활용법을 상세히 안내한다.
  2) 불량 패턴 분석과 원인 파악을 지원한다.
  3) 테스트 시간 단축과 정확도 향상 방안을 제시한다.""",

        # UI 텍스트
        "welcome_message": """안녕하세요! 테스트엔지니어링 전문 챗봇입니다. ⚡

저는 반도체 테스트 분야의 전문 지식을 제공합니다.

**Coming Soon! 🚀**
- 🔧 ATE 장비 운영 및 최적화 (준비중)
- 📊 테스트 프로그램 개발 가이드 (준비중)
- 🔍 불량 분석 및 디버깅 방법 (준비중)
- ⚡ 수율 개선 전략 (준비중)
- 🎯 신제품 테스트 검증 (준비중)

곧 더 나은 서비스로 찾아뵙겠습니다!""",

        "input_placeholder": "테스트엔지니어링 서비스 준비중입니다...",
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