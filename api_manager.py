"""
=================================================================
📡 AE WIKI - API 관리자 모듈 (api_manager.py)
=================================================================

📋 파일 역할:
- AI API 통신 관리 (RAG API, LLM API)
- 모의 응답 시스템 및 실제 API 호출 처리
- 챗봇별 API 설정 및 응답 포맷팅

🔗 주요 컴포넌트:
- RAG API 호출 및 문서 검색
- LLM API 호출 및 응답 생성
- Mock 데이터 시스템 (개발/테스트용)
- 출처 정보 포맷팅
"""

import requests
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from config import API_CONFIG, TEST_CONFIG, get_index_system_prompt, get_index_config, get_index_rag_name

logger = logging.getLogger(__name__)

def call_llm_api(user_message: str, retrieve_data: List[str], chat_history: list = None, source_data: List[dict] = None, user_id: str = None, custom_system_prompt: str = None, chatbot_type: str = "ae_wiki") -> str:
    """
    🎯 목적: LLM API를 호출하여 RAG 검색 결과를 기반으로 답변 생성

    📊 입력:
    - user_message (str): 사용자 질문
    - retrieve_data (List[str]): RAG에서 검색된 문서 내용 리스트
    - chat_history (list): 이전 대화 기록 (최대 10턴)
    - source_data (List[dict]): 출처 정보 (URL, 제목 등)
    - user_id (str): 사용자 식별자
    - custom_system_prompt (str): 커스텀 시스템 프롬프트
    - chatbot_type (str): 챗봇 타입 ("ae_wiki", "glossary", "jedec")

    📤 출력:
    - str: LLM이 생성한 답변 텍스트

    🔄 처리 흐름:
    1. 시스템 프롬프트 설정 (챗봇 타입별)
    2. 검색된 문서들을 컨텍스트로 결합
    3. 대화 기록을 프롬프트에 포함 (최대 10턴)
    4. LLM API 호출 및 응답 파싱
    5. 에러 처리 및 폴백 응답
    """

    # STEP 1: Mock 모드 확인
    if TEST_CONFIG.get("enable_mock_mode", True):
        combined_text = "\n\n".join(retrieve_data) if retrieve_data else ""
        source_citations = format_source_citations(source_data or [], chatbot_type)
        system_prompt = custom_system_prompt or get_index_system_prompt(chatbot_type)
        return get_mock_llm_response(user_message, combined_text, source_citations, chatbot_type, system_prompt)

    try:
        # STEP 2: 시스템 프롬프트 설정
        system_prompt = custom_system_prompt or get_index_system_prompt(chatbot_type)

        # STEP 3: 검색된 문서들을 하나의 컨텍스트로 결합
        if retrieve_data:
            combined_context = "\n\n".join([f"문서 {i+1}:\n{doc}" for i, doc in enumerate(retrieve_data)])
        else:
            combined_context = "관련 문서를 찾을 수 없습니다."

        # STEP 4: 대화 기록을 프롬프트에 포함 (슬라이딩 윈도우 - 최대 10턴)
        conversation_context = ""
        if chat_history:
            # 최근 10턴(20개 메시지)만 유지하여 토큰 제한 관리
            recent_history = chat_history[-20:] if len(chat_history) > 20 else chat_history

            for msg in recent_history:
                if msg.get("role") == "user":
                    conversation_context += f"사용자: {msg.get('content', '')}\n"
                elif msg.get("role") == "assistant":
                    conversation_context += f"어시스턴트: {msg.get('content', '')}\n"

        # STEP 5: 통합된 프롬프트 구성
        full_prompt = f"""
{system_prompt}

[이전 대화 기록]
{conversation_context}

[검색된 관련 문서]
{combined_context}

[현재 질문]
사용자: {user_message}

위의 검색된 문서와 이전 대화를 참고하여 질문에 답변해주세요.
"""

        # STEP 6: API 호출 설정
        api_config = API_CONFIG["llm_api"]
        headers = api_config["headers"].copy()
        if user_id:
            headers["User-Id"] = user_id

        payload = {
            "model": api_config["model"],
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }

        # STEP 7: API 호출 실행
        response = requests.post(
            f"{api_config['base_url']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                logger.warning(f"LLM API 응답 형식 오류: {result}")
                return "죄송합니다. 응답 처리 중 오류가 발생했습니다."
        else:
            logger.error(f"LLM API 호출 실패: {response.status_code} - {response.text}")
            return "죄송합니다. 서비스에 일시적인 문제가 있습니다. 잠시 후 다시 시도해주세요."

    except Exception as e:
        logger.error(f"LLM API 호출 중 예외 발생: {e}")
        return "죄송합니다. 시스템 오류가 발생했습니다. 관리자에게 문의해주세요."

def get_mock_rag_response(user_message: str, chatbot_type: str) -> dict:
    """개발/테스트용 모의 RAG 응답 생성"""

    # 시뮬레이션 지연
    if TEST_CONFIG.get("mock_response_delay", 0) > 0:
        time.sleep(TEST_CONFIG["mock_response_delay"])

    # 오늘 날짜 기준으로 최신순 정렬 시뮬레이션
    today = datetime.now()
    from datetime import timedelta

    dates = [
        (today - timedelta(days=1)).strftime("%Y-%m-%d"),   # 어제 (최신)
        (today - timedelta(days=7)).strftime("%Y-%m-%d"),   # 1주일 전
        (today - timedelta(days=30)).strftime("%Y-%m-%d"),  # 1달 전
    ]

    # 챗봇별 모의 응답 데이터
    mock_responses = {
        "ae_wiki": {
            "documents": [
                f"AE팀 업무 프로세스 관련 문서입니다. 질문: '{user_message}'에 대한 상세 답변을 제공합니다. 최신 가이드라인에 따르면...",
                f"반도체 제품 사양 관련 내용입니다. '{user_message}' 관련하여 기술적 세부사항과 적용 방법을 설명합니다.",
                f"고객 지원 절차 문서에서 발췌한 내용입니다. '{user_message}'와 관련된 업무 프로세스를 안내합니다."
            ],
            "source_info": [
                {"source": "AE팀 업무 가이드 v2.1", "last_modified": dates[0], "date_score": 1.0, "relevance_score": 0.95, "confluence_url": "https://confluence.company.com/display/AE/Process-Guide"},
                {"source": "반도체 제품 사양서 v2.0", "last_modified": dates[1], "date_score": 0.8, "relevance_score": 0.88, "confluence_url": "https://confluence.company.com/display/AE/Product-Spec"},
                {"source": "고객 지원 매뉴얼 v1.0", "last_modified": dates[2], "date_score": 0.3, "relevance_score": 0.82, "confluence_url": "https://confluence.company.com/display/AE/Customer-Support"}
            ]
        },
        "glossary": {
            "documents": [
                f"AE 용어집: '{user_message}' 관련 전문 용어 정의 및 설명입니다. 반도체 기술 분야에서 사용되는 핵심 개념을 다룹니다.",
                f"기술 용어 해설: '{user_message}'의 상세한 기술적 정의와 실무 활용 방법을 제공합니다.",
                f"연관 키워드 및 참고 자료: '{user_message}'와 관련된 추가 용어와 참고할 만한 기술 문서를 안내합니다."
            ],
            "source_info": [
                {"source": "AE 용어집 DB v3.2", "last_modified": dates[0], "date_score": 1.0, "relevance_score": 0.92},
                {"source": "반도체 기술 용어집 v2.8", "last_modified": dates[1], "date_score": 0.8, "relevance_score": 0.85},
                {"source": "기술 용어 참고 자료집", "last_modified": dates[2], "date_score": 0.3, "relevance_score": 0.78}
            ]
        },
        "jedec": {
            "documents": [
                f"JEDEC 표준 문서: '{user_message}' 관련 규격 및 테스트 방법을 상세히 설명합니다. 최신 표준에 따른 기술 요구사항을 제시합니다.",
                f"메모리 표준 규격: '{user_message}'에 해당하는 JEDEC 메모리 표준의 세부 사양과 준수 사항을 안내합니다.",
                f"테스트 검증 방법: '{user_message}' 관련 JEDEC 표준 준수를 위한 테스트 절차와 검증 방법을 제공합니다."
            ],
            "source_info": [
                {"source": "JEDEC JESD79-5B Standard", "last_modified": dates[0], "date_score": 1.0, "relevance_score": 0.94, "page": "Section 4.2"},
                {"source": "JEDEC JEP106BJ Reference", "last_modified": dates[1], "date_score": 0.8, "relevance_score": 0.87, "page": "Table 3.1"},
                {"source": "JEDEC Test Methods Guide", "last_modified": dates[2], "date_score": 0.3, "relevance_score": 0.83, "page": "Chapter 2"}
            ]
        },
        "quality": {
            "documents": [
                f"품질관리 가이드: '{user_message}' 관련 품질 검사 기준과 절차를 상세히 설명합니다.",
                f"불량 분석 매뉴얼: '{user_message}'와 관련된 불량 유형 분석 및 개선 방안을 제시합니다.",
                f"품질 표준 문서: '{user_message}' 관련 ISO/TS 표준 준수 방법을 안내합니다."
            ],
            "source_info": [
                {"source": "품질관리 표준 매뉴얼 v4.1", "last_modified": dates[0], "date_score": 1.0, "relevance_score": 0.93},
                {"source": "불량 분석 가이드 v3.0", "last_modified": dates[1], "date_score": 0.8, "relevance_score": 0.86},
                {"source": "ISO/TS 16949 준수 가이드", "last_modified": dates[2], "date_score": 0.3, "relevance_score": 0.81}
            ]
        },
        "test_engineering": {
            "documents": [
                f"테스트엔지니어링 가이드: '{user_message}' 관련 ATE 장비 운영 및 테스트 프로그램 개발 방법을 설명합니다.",
                f"장비 운영 매뉴얼: '{user_message}'와 관련된 테스트 장비 설정 및 최적화 방법을 제시합니다.",
                f"수율 개선 방법론: '{user_message}' 관련 테스트 효율성 향상 및 불량 분석 기법을 안내합니다."
            ],
            "source_info": [
                {"source": "ATE 장비 운영 가이드 v2.3", "last_modified": dates[0], "date_score": 1.0, "relevance_score": 0.91},
                {"source": "테스트 프로그램 개발 매뉴얼", "last_modified": dates[1], "date_score": 0.8, "relevance_score": 0.84},
                {"source": "수율 개선 방법론 v1.8", "last_modified": dates[2], "date_score": 0.3, "relevance_score": 0.79}
            ]
        }
    }

    # 기본값 설정
    if chatbot_type not in mock_responses:
        chatbot_type = "ae_wiki"

    response_data = mock_responses[chatbot_type]

    return {
        "documents": response_data["documents"],
        "source_info": response_data["source_info"]
    }

def get_mock_llm_response(user_message: str, retrieve_text: str, source_citations: str, chatbot_type: str, system_prompt: str) -> str:
    """개발/테스트용 모의 LLM 응답 생성"""

    # 시뮬레이션 지연
    if TEST_CONFIG.get("mock_response_delay", 0) > 0:
        time.sleep(TEST_CONFIG["mock_response_delay"])

    # 챗봇별 맞춤형 응답 템플릿
    response_templates = {
        "ae_wiki": f"""안녕하세요! AE WIKI 전문 챗봇입니다. 🧠

**질문 분석**: "{user_message}"

**답변**:
검색된 AE팀 업무 문서를 바탕으로 답변드리겠습니다.

"{user_message}"에 대한 상세한 답변을 제공합니다. AE팀의 최신 업무 프로세스와 가이드라인에 따르면, 다음과 같은 절차를 따르시면 됩니다:

1. **주요 단계 및 절차**
   - 관련 문서 및 규정 확인
   - 팀 내부 승인 프로세스 진행
   - 고객사 및 관련 부서와의 협의

2. **주의사항**
   - 최신 업데이트된 정보 반영 필요
   - 보안 및 품질 기준 준수 필수
   - 정확한 문서화 및 이력 관리

더 자세한 내용은 검색된 문서나 팀 내 담당자에게 문의해주세요.

{source_citations}""",

        "glossary": f"""안녕하세요! AE 용어집 전문 챗봇입니다. 🔍

**검색 용어**: "{user_message}"

**용어 정의 및 설명**:
검색된 용어집 데이터베이스를 바탕으로 정확한 정의를 제공합니다.

"{user_message}"는 반도체 AE(Application Engineering) 분야에서 중요한 전문 용어입니다.

**정의**: [검색된 문서 기반 정의]
**활용 분야**: 반도체 설계, 제조 공정, 품질 관리 등
**관련 키워드**: [연관 용어들]

**실무 활용 방법**:
- 기술 문서 작성 시 정확한 용어 사용
- 고객사 기술 지원 시 전문 용어 설명
- 팀 내 기술 교육 및 지식 공유

궁금한 점이 더 있으시면 언제든 검색해보세요!

{source_citations}""",

        "jedec": f"""안녕하세요! JEDEC SPEC 전문 챗봇입니다. 🤖

**질의 사항**: "{user_message}"

**JEDEC 표준 답변**:
검색된 JEDEC 표준 문서를 기반으로 정확한 규격 정보를 제공합니다.

"{user_message}"와 관련된 JEDEC 표준 요구사항은 다음과 같습니다:

**표준 규격**:
- 해당 JEDEC 표준 번호 및 버전
- 주요 기술 사양 및 파라미터
- 테스트 방법 및 검증 절차

**준수 사항**:
- 필수 준수 요구사항
- 권장 구현 방법
- 호환성 고려사항

**실무 적용**:
- 제품 설계 시 고려사항
- 테스트 및 검증 방법
- 고객사 표준 대응 방안

더 상세한 표준 문서는 공식 JEDEC 웹사이트를 참고하시기 바랍니다.

{source_citations}""",

        "quality": f"""안녕하세요! 품질관리 전문 챗봇입니다. 🔬

**품질 관련 질의**: "{user_message}"

**품질관리 답변**:
검색된 품질관리 문서를 바탕으로 전문적인 답변을 제공합니다.

"{user_message}"에 대한 품질관리 관점의 분석 결과입니다:

**품질 기준**:
- 해당 품질 파라미터 및 허용 범위
- 측정 방법 및 검사 절차
- 품질 기준 근거 및 표준

**불량 분석**:
- 주요 불량 유형 및 원인
- 통계적 분석 방법
- 개선 방안 및 예방 대책

**프로세스 개선**:
- 품질 향상을 위한 권장사항
- 지속적 개선 방법론
- 모니터링 및 관리 체계

ISO/TS 표준 준수를 위한 추가 가이드가 필요하시면 말씀해주세요.

{source_citations}""",

        "test_engineering": f"""안녕하세요! 테스트엔지니어링 전문 챗봇입니다. ⚡

**테스트 관련 질의**: "{user_message}"

**테스트엔지니어링 답변**:
검색된 테스트 관련 문서를 기반으로 전문적인 답변을 제공합니다.

"{user_message}"에 대한 테스트엔지니어링 관점의 분석입니다:

**테스트 방법론**:
- 적절한 테스트 프로그램 및 패턴
- ATE 장비 설정 및 최적화
- 테스트 시간 단축 방안

**장비 운영**:
- 장비별 특성 및 활용 방법
- 유지보수 및 캘리브레이션
- 효율성 향상 기법

**불량 분석**:
- 테스트 불량 패턴 분석
- 근본 원인 파악 방법
- 수율 개선 전략

더 상세한 기술 지원이나 장비 관련 문의사항이 있으시면 언제든 말씀해주세요.

{source_citations}"""
    }

    # 기본 응답 (알 수 없는 챗봇 타입인 경우)
    if chatbot_type not in response_templates:
        return f"""죄송합니다. "{user_message}"에 대한 정보를 찾을 수 없습니다.

**검색된 내용**:
{retrieve_text[:500]}{"..." if len(retrieve_text) > 500 else ""}

{source_citations}

더 구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다."""

    return response_templates[chatbot_type]

def call_rag_api_with_chatbot_type(user_message: str, chatbot_type: str) -> dict:
    """
    🎯 목적: 챗봇 타입별 RAG API 호출하여 관련 문서 검색

    📊 입력:
    - user_message (str): 사용자 질문
    - chatbot_type (str): 챗봇 타입 (ae_wiki, glossary, jedec, quality, test_engineering)

    📤 출력:
    - dict: {"documents": [문서들], "source_info": [출처정보들]}

    🔄 처리 흐름:
    1. Mock 모드 확인 및 처리
    2. 챗봇별 인덱스명 매핑
    3. RAG API 호출 (날짜 정렬 포함)
    4. 응답 파싱 및 정규화
    """

    # STEP 1: Mock 모드 확인
    if TEST_CONFIG.get("enable_mock_mode", True):
        return get_mock_rag_response(user_message, chatbot_type)

    try:
        # STEP 2: 챗봇별 인덱스명 매핑
        index_name = get_index_rag_name(chatbot_type)
        if not index_name:
            logger.warning(f"Unknown chatbot type: {chatbot_type}")
            return {"documents": [], "source_info": []}

        # STEP 3: RAG API 호출 설정
        api_config = API_CONFIG["rag_api_common"]

        # 날짜 기반 정렬을 포함한 페이로드 구성
        payload = {
            "query": user_message,
            "index_name": index_name,
            "num_candidates": api_config.get("num_candidates", 1000),
            "num_result_doc": api_config.get("num_result_doc", 3),
            "fields_exclude": api_config.get("fields_exclude", []),
            "sort_config": {
                "enable_date_sort": api_config.get("sort_by_date", True),
                "date_field": api_config.get("date_field", "last_modified"),
                "sort_order": api_config.get("sort_order", "desc"),
                "date_weight": api_config.get("date_weight", 0.3),
                "relevance_weight": api_config.get("relevance_weight", 0.7),
                "current_date": datetime.now().isoformat()
            }
        }

        # STEP 4: API 호출 실행
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_config.get('credential_key', '')}"
        }

        response = requests.post(
            f"{api_config['base_url']}/search",
            headers=headers,
            json=payload,
            timeout=api_config.get("timeout", 30)
        )

        if response.status_code == 200:
            result = response.json()

            # 응답 파싱
            documents = []
            source_info = []

            if "results" in result:
                for item in result["results"]:
                    # 문서 내용 추출
                    content = item.get("content", item.get("text", ""))
                    if content:
                        documents.append(content)

                    # 출처 정보 추출
                    source_item = {
                        "source": item.get("title", item.get("source", "Unknown Source")),
                        "relevance_score": item.get("score", 0.0),
                        "last_modified": item.get("last_modified", ""),
                        "date_score": item.get("date_score", 0.0)
                    }

                    # 챗봇별 추가 정보
                    if chatbot_type == "ae_wiki" and "url" in item:
                        source_item["confluence_url"] = item["url"]
                    elif chatbot_type == "jedec" and "page" in item:
                        source_item["page"] = item["page"]

                    source_info.append(source_item)

            return {
                "documents": documents,
                "source_info": source_info
            }
        else:
            logger.error(f"RAG API 호출 실패: {response.status_code} - {response.text}")
            return {"documents": [], "source_info": []}

    except Exception as e:
        logger.error(f"RAG API 호출 중 예외 발생: {e}")
        return {"documents": [], "source_info": []}

def format_source_citations(source_data: List[dict], chatbot_type: str = "ae_wiki") -> str:
    """
    🎯 목적: 챗봇별 출처 정보를 적절한 형식으로 포맷팅

    📊 입력:
    - source_data: 출처 정보 리스트
    - chatbot_type: 챗봇 타입

    📤 출력:
    - 포맷팅된 출처 인용 문자열
    """
    if not source_data:
        return ""

    citations = []

    for i, source in enumerate(source_data, 1):
        source_name = source.get("source", f"문서 {i}")

        if chatbot_type == "ae_wiki":
            # Confluence URL 포함
            if "confluence_url" in source:
                citations.append(f"📄 **{source_name}** - [Confluence 링크]({source['confluence_url']})")
            else:
                citations.append(f"📄 **{source_name}**")

        elif chatbot_type == "jedec":
            # 페이지 정보 포함
            page_info = source.get("page", "")
            if page_info:
                citations.append(f"📄 **{source_name}** ({page_info})")
            else:
                citations.append(f"📄 **{source_name}**")

        else:
            # 기본 형식
            citations.append(f"📄 **{source_name}**")

        # 날짜 정보 추가 (있는 경우)
        if source.get("last_modified"):
            citations[-1] += f" (수정일: {source['last_modified']})"

    if citations:
        return f"\n\n**📚 참고 자료:**\n" + "\n".join(citations)
    else:
        return ""