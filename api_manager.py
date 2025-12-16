"""
=================================================================
📡 AE WIKI - API 관리자 모듈 (api_manager.py)
=================================================================

📋 파일 역할:
- AI API 통신 관리 (RAG API, LLM API)
- 실제 API 호출 처리
- 챗봇별 API 설정 및 응답 포맷팅

🔗 주요 컴포넌트:
- RAG API 호출 및 문서 검색
- LLM API 호출 및 응답 생성
- 출처 정보 포맷팅

🛠️ 개선사항 (2025-10-13):
1. 방어적 API 응답 파싱 - 키 존재 여부 확인 및 다중 경로 지원
2. Accept 헤더 수정 - 스트리밍 비활성화 시 application/json 사용
3. source_data를 LLM 프롬프트에 포함 - 신뢰성 향상
4. RAG 응답 파싱 fallback 추가 - 다양한 필드명 지원
5. 실제 에러 메시지 노출 - 디버깅 용이성 향상
6. 상세한 디버깅 로그 - 터미널 출력으로 흐름 추적
"""

import requests
import time
import logging
import uuid
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from config import API_CONFIG, TEST_CONFIG, get_index_system_prompt, get_index_config, get_index_rag_name

logger = logging.getLogger(__name__)

# ========================================
# 디버깅 설정
# ========================================
DEBUG_MODE = True  # False로 설정하면 상세 로그 비활성화

def debug_print(message: str, data: Any = None, level: str = "INFO"):
    """
    디버깅용 출력 함수 - 터미널에 상세 정보 출력

    Args:
        message: 출력할 메시지
        data: 출력할 데이터 (dict, list 등)
        level: 로그 레벨 (INFO, WARNING, ERROR)
    """
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level_emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "📝")

        print(f"\n{'='*80}")
        print(f"{level_emoji} [{level} {timestamp}] {message}")

        if data is not None:
            if isinstance(data, (dict, list)):
                try:
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except Exception as e:
                    print(f"[JSON 직렬화 실패: {e}]")
                    print(str(data))
            else:
                print(str(data))
        print(f"{'='*80}\n")


def safe_get_nested(data, *path, default=None):
    """
    dict/list 모두 지원하는 안전한 중첩 데이터 추출 함수

    Args:
        data: 딕셔너리 또는 리스트
        *path: 접근할 경로 (str: 딕셔너리 키, int: 리스트 인덱스)
        default: 기본값

    Returns:
        추출된 값 또는 기본값

    Examples:
        safe_get_nested(obj, "choices", 0, "message", "content")
        safe_get_nested(obj, "hits", "hits", 0, "_source", "title")
    """
    cur = data
    for key in path:
        if isinstance(cur, dict) and isinstance(key, str):
            if key not in cur:
                return default
            cur = cur[key]
        elif isinstance(cur, list) and isinstance(key, int):
            if key < 0 or key >= len(cur):
                return default
            cur = cur[key]
        else:
            return default
    return cur if cur is not None else default


# ========================================
# Confluence 기본 URL
# ========================================
CONFLUENCE_BASE = "https://confluence.samsungds.net/spaces/AppEngineeringTeam/pages/"

def sanitize_llm_markdown(text: str) -> str:
    """LLM 응답 내 HTML 줄바꿈/경량 태그를 Markdown 친화적으로 정리"""
    if not isinstance(text, str):
        return text

    # 1) br 변형 전부 개행으로
    text = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")

    # 2) p 태그 → 빈 줄
    text = text.replace("</p>", "\n\n").replace("<p>", "")

    # 3) li 태그 → 불릿
    text = text.replace("</li>", "").replace("<li>", "• ")

    # 4) ul/ol 제거
    text = text.replace("<ul>", "").replace("</ul>", "").replace("<ol>", "").replace("</ol>", "")

    # 5) 연속 개행 정리(선택)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    return text.strip()


# ========================================
# RAG 응답 범용 파서
# ========================================
def _extract_hits_from_rag_response(response, *, debug=False):
    """
    서버 응답 포맷 변화에 대응하는 유연한 hits 추출기.
    반환: List[dict] (ES hit 객체 리스트)
    """
    try:
        data = response.json()
    except Exception:
        try:
            data = json.loads(response.text)
        except Exception:
            if debug:
                print("[RAG] 응답 JSON 파싱 실패:", response.text[:1000])
            raise ValueError("RAG 응답이 JSON이 아닙니다.")

    if debug:
        try:
            print("[RAG] top-level keys:", list(data.keys()))
        except Exception:
            pass

    # 과거 포맷: {"message": "{\"hits\": {...}}"}
    if isinstance(data, dict) and "message" in data:
        msg = data["message"]
        try:
            inner = json.loads(msg) if isinstance(msg, str) else msg
        except Exception:
            if debug:
                print("[RAG] message 재파싱 실패:", type(msg), str(msg)[:300])
            raise ValueError("RAG 응답의 message 필드 JSON 파싱 실패")
        if "hits" in inner and "hits" in inner["hits"]:
            return inner["hits"]["hits"]

    # 일반 포맷: {"hits": {"hits": [...]}}
    if isinstance(data, dict) and "hits" in data and isinstance(data["hits"], dict) and "hits" in data["hits"]:
        return data["hits"]["hits"]

    # 래핑 포맷: {"data": {"hits": {"hits": [...]}}}
    cur = data
    for key in ("data", "result", "payload"):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
    if isinstance(cur, dict) and "hits" in cur and isinstance(cur["hits"], dict) and "hits" in cur["hits"]:
        return cur["hits"]["hits"]

    if debug:
        print("[RAG] 인식 불가 응답 샘플:", json.dumps(data, ensure_ascii=False)[:1000])
    raise KeyError("RAG 응답에서 hits 리스트를 찾을 수 없습니다.")


# ========================================
# LLM 응답 범용 파서
# ========================================
def _extract_llm_text(result, *, debug=False) -> str:
    """
    다양한 LLM 응답 포맷에서 본문 텍스트를 찾아서 문자열로 반환.
    지원: choices[0].message.content(str|list), choices[0].text,
         tool_calls/function_call(요약), refusal, Responses API 스타일 등
    """
    if not isinstance(result, dict):
        return ""

    if debug:
        try:
            print("[LLM] top-level keys:", list(result.keys()))
        except Exception:
            pass

    # 1) Chat Completions 표준 계열
    try:
        choices = result.get("choices")
        if isinstance(choices, list) and choices:
            c0 = choices[0]
            if debug:
                try:
                    print("[LLM] choices[0] keys:", list(c0.keys()))
                    if isinstance(c0.get("message"), dict):
                        print("[LLM] choices[0].message keys:", list(c0["message"].keys()))
                except Exception:
                    pass

            # 1-1) message.content (string)
            msg = c0.get("message") or {}
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                return content

            # 1-2) message.content (list of parts)
            if isinstance(content, list):
                parts = []
                for p in content:
                    if isinstance(p, dict) and isinstance(p.get("text"), str) and p["text"].strip():
                        parts.append(p["text"])
                    elif isinstance(p, str) and p.strip():
                        parts.append(p)
                if parts:
                    return "\n".join(parts)

            # 1-3) tool_calls / function_call만 있고 content가 비어있는 경우
            tool_calls = msg.get("tool_calls") or []
            function_call = msg.get("function_call")
            if tool_calls or function_call:
                try:
                    if tool_calls:
                        tc = tool_calls[0]
                        fn_name = tc.get("function", {}).get("name", "tool")
                        fn_args = tc.get("function", {}).get("arguments", "")
                        if isinstance(fn_args, dict):
                            fn_args = json.dumps(fn_args, ensure_ascii=False)
                        return f"(도구 호출: {fn_name} args={fn_args})"
                    if function_call:
                        fn_name = function_call.get("name", "function")
                        fn_args = function_call.get("arguments", "")
                        if isinstance(fn_args, dict):
                            fn_args = json.dumps(fn_args, ensure_ascii=False)
                        return f"(함수 호출: {fn_name} args={fn_args})"
                except Exception:
                    pass

            # 1-4) refusal이 별도 필드로 온 경우
            refusal = msg.get("refusal")
            if isinstance(refusal, str) and refusal.strip():
                return f"(거부 사유)\n{refusal}"

            # 1-5) 구형/호환: choices[0].text
            if isinstance(c0.get("text"), str) and c0["text"].strip():
                return c0["text"]

            # 1-6) finish_reason이 content_filter 등으로 content가 비는 경우
            finish_reason = c0.get("finish_reason")
            if finish_reason and str(finish_reason) != "stop":
                return f"(finish_reason={finish_reason})"
    except Exception as e:
        if debug:
            print("[LLM] ChatCompletions parse error:", repr(e))

    # 2) Responses API 계열
    try:
        output = result.get("output")
        if isinstance(output, list) and output:
            o0 = output[0]
            cnt = o0.get("content")
            if isinstance(cnt, list) and cnt:
                parts = []
                for p in cnt:
                    if isinstance(p, dict) and isinstance(p.get("text"), str) and p["text"].strip():
                        parts.append(p["text"])
                if parts:
                    return "\n".join(parts)
    except Exception as e:
        if debug:
            print("[LLM] Responses parse error:", repr(e))

    return ""


# ========================================
# 출처 포맷팅 함수
# ========================================
def format_source_citations(source_data: List[dict], chatbot_type: str = "ae_wiki") -> str:
    """출처 정보를 마크다운 형식으로 포맷팅"""
    if not source_data:
        return ""
    lines = []
    for i, s in enumerate(source_data, 1):
        t = s.get("title", f"문서_{i}")
        u = s.get("source_url", "")
        if not u and s.get("doc_id"):
            u = f"{CONFLUENCE_BASE}{s['doc_id']}"
        if u:
            lines.append(f"{i}. [{t}]({u})")
        else:
            lines.append(f"{i}. {t}")
    return "\n".join(lines)


# ========================================
# LLM API 호출 함수 (개선 버전)
# ========================================
def call_llm_api(
    user_message: str,
    retrieve_data: List[str],
    chat_history: list = None,
    source_data: List[dict] = None,
    user_id: str = None,
    custom_system_prompt: str = None,
    chatbot_type: str = "ae_wiki"
) -> str:
    """
    🎯 목적: LLM API를 호출하여 RAG 검색 결과를 기반으로 답변 생성

    📊 입력:
    - user_message (str): 사용자 질문
    - retrieve_data (List[str]): RAG에서 검색된 문서 내용 리스트
    - chat_history (list): 이전 대화 기록 (최대 10턴)
    - source_data (List[dict]): 출처 정보 (URL, 제목 등) - LLM 프롬프트에 포함됨
    - user_id (str): 사용자 식별자
    - custom_system_prompt (str): 커스텀 시스템 프롬프트
    - chatbot_type (str): 챗봇 타입 ("ae_wiki", "glossary", "jedec")

    📤 출력:
    - str: LLM이 생성한 답변 텍스트

    🛡️ 개선사항:
    - 방어적 응답 파싱 (문제 1 해결)
    - Accept 헤더 수정 (문제 2 해결)
    - source_data 포함 (문제 3 해결)
    - 실제 에러 노출 (문제 5 해결)
    - 상세 디버깅 로그 (문제 7 해결)
    """

    debug_print("🚀 LLM API 호출 시작", {
        "user_message": user_message[:100] + "..." if len(user_message) > 100 else user_message,
        "chatbot_type": chatbot_type,
        "user_id": user_id,
        "retrieve_data_count": len(retrieve_data) if retrieve_data else 0,
        "source_data_count": len(source_data) if source_data else 0,
        "chat_history_count": len(chat_history) if chat_history else 0
    })

    try:
        # STEP 1: 시스템 프롬프트 설정
        system_prompt = custom_system_prompt or get_index_system_prompt(chatbot_type)
        debug_print("📝 시스템 프롬프트 로드", {
            "prompt_length": len(system_prompt),
            "prompt_preview": system_prompt[:150] + "..."
        })

        # STEP 2: 검색된 문서들을 하나의 컨텍스트로 결합
        if retrieve_data:
            combined_context = "\n\n".join([f"문서 {i+1}:\n{doc}" for i, doc in enumerate(retrieve_data)])
            debug_print("📚 검색 문서 결합 완료", {
                "document_count": len(retrieve_data),
                "total_length": len(combined_context)
            })
        else:
            combined_context = "관련 문서를 찾을 수 없습니다."
            debug_print("⚠️ 검색된 문서 없음", level="WARNING")

        # STEP 3: 출처 정보를 포맷팅 (문제 3 해결 - source_data를 LLM에 반영)
        source_citations = ""
        if source_data:
            source_citations = format_source_citations(source_data, chatbot_type)
            debug_print("🔗 출처 정보 포맷팅 완료", {
                "source_count": len(source_data),
                "citations_length": len(source_citations)
            })

        # STEP 4: messages 배열 구성
        messages = []

        # 시스템 프롬프트 추가
        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # 이전 대화 기록 추가
        if chat_history:
            recent_history = chat_history[-20:] if len(chat_history) > 20 else chat_history
            messages.extend(recent_history)
            debug_print("💬 대화 기록 추가", {"history_messages": len(recent_history)})

        # 현재 질문 구성 (RAG 문서 + 출처 정보 포함)
        current_user_message = f"""[검색된 관련 문서]
{combined_context}

[현재 질문]
{user_message}

위의 검색된 문서를 참고하여 질문에 답변해주세요."""

        # 출처 정보가 있으면 프롬프트에 추가 (문제 3 해결)
        if source_citations:
            current_user_message += f"\n\n{source_citations}"

        messages.append({
            "role": "user",
            "content": current_user_message
        })

        debug_print("📨 Messages 배열 구성 완료", {
            "total_messages": len(messages),
            "user_message_length": len(current_user_message)
        })

        # STEP 5: API 호출 설정
        api_config = API_CONFIG.get("llm_api", {})
        if not api_config:
            raise ValueError("API_CONFIG에 'llm_api' 설정이 없습니다.")

        base_url = api_config.get("base_url")
        if not base_url:
            raise ValueError("LLM API base_url이 설정되지 않았습니다.")

        # 헤더 구성
        headers_config = api_config.get("headers", {})

        # 문제 2 해결: 스트리밍 비활성화 시 Accept를 application/json으로 변경
        accept_header = "application/json"  # stream=False이므로 JSON으로 변경

        headers = {
            "x-dep-ticket": api_config.get("credential_key", ""),
            "Send-System-Name": headers_config.get("Send-System-Name", ""),
            "User-Id": user_id or headers_config.get("User-Id", ""),
            "User-Type": headers_config.get("User-Type", "AD_ID"),
            "Prompt-Msg-Id": str(uuid.uuid4()),
            "Completion-Msg-Id": str(uuid.uuid4()),
            "Accept": accept_header,  # 문제 2 해결
            "Content-Type": "application/json"
        }

        payload = {
            "model": api_config.get("model", "openai/gpt-oss-120b"),
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 6000,
            "stream": False
        }

        debug_print("📤 LLM API 요청 준비", {
            "url": base_url,
            "model": payload["model"],
            "temperature": payload["temperature"],
            "max_tokens": payload["max_tokens"],
            "stream": payload["stream"],
            "headers": {k: v[:50] + "..." if len(str(v)) > 50 else v for k, v in headers.items()}
        })

        # STEP 6: API 호출 실행
        debug_print("🌐 LLM API 호출 중...")

        response = requests.post(
            base_url,
            headers=headers,
            json=payload,
            timeout=30
        )

        debug_print("📥 LLM API 응답 수신", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response_length": len(response.text) if response.text else 0
        })

        # STEP 7: 응답 처리 (범용 파서 사용)
        if response.status_code == 200:
            try:
                result = response.json()

                # 관찰용: choices[0] 구조
                try:
                    if isinstance(result.get("choices"), list) and result["choices"]:
                        c0 = result["choices"][0]
                        print("[LLM] choices[0] keys:", list(c0.keys()))
                        if isinstance(c0.get("message"), dict):
                            print("[LLM] choices[0].message keys:", list(c0["message"].keys()))
                except Exception:
                    pass

                content = _extract_llm_text(result, debug=True)
                if content and isinstance(content, str):
                    debug_print("✅ LLM 답변 생성 성공", {
                        "content_length": len(content),
                        "content_preview": content[:200] + "..." if len(content) > 200 else content
                    })

                    # 출처 데이터 추가
                    citations_source = source_data or []

                    # 하단 출처 섹션 생성 및 붙이기
                    try:
                        citations_md = format_source_citations(citations_source, chatbot_type)
                    except Exception:
                        citations_md = ""

                    final_answer = content + ("\n\n---\n**출처**\n" + citations_md if citations_md else "")
                    return final_answer

                # content 못 찾은 경우: 폴백 처리
                try:
                    # 텍스트 본문이 없을 때, 최소 힌트라도 만들어서 반환
                    choices = result.get("choices") or []
                    c0 = choices[0] if choices else {}
                    msg = c0.get("message") or {}
                    finish_reason = c0.get("finish_reason")
                    tool_calls = msg.get("tool_calls") or []
                    function_call = msg.get("function_call")

                    hint_lines = []
                    if finish_reason:
                        hint_lines.append(f"finish_reason={finish_reason}")
                    if tool_calls:
                        try:
                            fn_name = tool_calls[0].get("function", {}).get("name", "tool")
                            hint_lines.append(f"tool_calls={fn_name}")
                        except Exception:
                            pass
                    if function_call:
                        try:
                            fn_name = function_call.get("name", "function")
                            hint_lines.append(f"function_call={fn_name}")
                        except Exception:
                            pass

                    hint = (", ".join(hint_lines)) if hint_lines else "본문 텍스트가 비어 있음"
                    content = f"(LLM 응답 요약: {hint})"

                    # 출처 붙이기
                    citations_source = source_data or []
                    try:
                        citations_md = format_source_citations(citations_source, chatbot_type)
                    except Exception:
                        citations_md = ""

                    final_answer = content + ("\n\n---\n**출처**\n" + citations_md if citations_md else "")
                    return final_answer

                except Exception:
                    # 마지막 방어선: 그래도 실패하면 기존 오류를 유지
                    top_keys = list(result.keys())
                    raise ValueError(f"LLM API 응답 형식 오류 - content를 찾을 수 없습니다. 응답 키: {top_keys}")

            except json.JSONDecodeError as e:
                error_msg = f"❌ JSON 파싱 실패: {str(e)}\n\n원본 응답 텍스트:\n{response.text[:1000]}"
                debug_print(error_msg, level="ERROR")
                logger.error(error_msg)
                raise ValueError(f"LLM API 응답 JSON 파싱 실패: {str(e)}")
        else:
            # 문제 5 해결: 실제 HTTP 에러와 응답 본문을 노출
            error_msg = f"❌ LLM API 호출 실패\n\nHTTP Status: {response.status_code}\nReason: {response.reason}\n\n응답 본문:\n{response.text[:1000]}"
            debug_print(error_msg, level="ERROR")
            logger.error(error_msg)
            raise requests.HTTPError(f"LLM API 호출 실패 - Status: {response.status_code}, Reason: {response.reason}, Body: {response.text[:500]}")

    except requests.Timeout as e:
        error_msg = f"❌ LLM API 타임아웃 (30초 초과)\n\n예외: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        debug_print(error_msg, level="ERROR")
        logger.error(error_msg)
        raise TimeoutError(f"LLM API 타임아웃: {str(e)}")

    except requests.RequestException as e:
        error_msg = f"❌ LLM API 요청 예외\n\n예외: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        debug_print(error_msg, level="ERROR")
        logger.error(error_msg)
        raise requests.RequestException(f"LLM API 요청 예외: {str(e)}")

    except Exception as e:
        error_msg = f"❌ LLM API 예상치 못한 예외\n\n예외 타입: {type(e).__name__}\n예외 내용: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        debug_print(error_msg, level="ERROR")
        logger.error(error_msg)
        raise Exception(f"LLM API 예상치 못한 예외 [{type(e).__name__}]: {str(e)}")


# ========================================
# RAG API 호출 함수 (개선 버전)
# ========================================
def call_rag_api_with_chatbot_type(user_message: str, chatbot_type: str) -> dict:
    """
    🎯 목적: 챗봇 타입별 RAG API 호출하여 관련 문서 검색

    📊 입력:
    - user_message (str): 사용자 질문
    - chatbot_type (str): 챗봇 타입 (ae_wiki, glossary, jedec, quality, test_engineering)

    📤 출력:
    - dict: {"documents": [문서들], "source_info": [출처정보들]}

    🛡️ 개선사항:
    - fallback 파싱 로직 추가 (문제 4 해결)
    - 실제 에러 노출 (문제 5 해결)
    - 상세 디버깅 로그 (문제 7 해결)
    """

    debug_print("🔍 RAG API 호출 시작", {
        "user_message": user_message[:100] + "..." if len(user_message) > 100 else user_message,
        "chatbot_type": chatbot_type
    })

    try:
        # STEP 1: 챗봇별 인덱스명 매핑
        index_name = get_index_rag_name(chatbot_type)
        if not index_name:
            error_msg = f"⚠️ 알 수 없는 챗봇 타입: {chatbot_type}"
            debug_print(error_msg, level="WARNING")
            logger.warning(error_msg)
            return {"documents": [], "source_info": []}

        debug_print("📇 인덱스 매핑 완료", {
            "chatbot_type": chatbot_type,
            "index_name": index_name
        })

        # STEP 2: RAG API 설정
        api_config = API_CONFIG.get("rag_api_common", {})
        if not api_config:
            raise ValueError("API_CONFIG에 'rag_api_common' 설정이 없습니다.")

        base_url = api_config.get("base_url")
        if not base_url:
            raise ValueError("RAG API base_url이 설정되지 않았습니다.")

        # 페이로드 구성 (스펙 준수)
        index_name = (index_name or "").strip()

        # URL/ID 키는 절대 제외하지 않도록 필터링
        _raw_exclude = api_config.get("fields_exclude", ["v_merge_title_content"])
        fields_exclude = [k for k in _raw_exclude if k not in {"source_url", "url", "doc_url", "link", "doc_id", "_id"}]

        payload = {
            "index_name": index_name,
            "permission_groups": api_config.get("auth_list", ["ds"]),
            "query_text": user_message,
            "num_result_doc": api_config.get("num_result_doc", 5),
            "fields_exclude": fields_exclude,
        }

        print(f"[RAG] base_url={api_config.get('base_url','')}")
        print(f"[RAG] index_name='{index_name}'")
        print(f"[RAG] permission_groups={api_config.get('auth_list', [])}")
        print(f"[RAG] fields_exclude={fields_exclude}")

        # 헤더 구성
        headers = {
            "Content-Type": "application/json",
            "x-dep-ticket": api_config.get("credential_key", ""),
            "api-key": api_config.get("api-key", "")
        }

        debug_print("📤 RAG API 요청 준비", {
            "url": base_url,
            "index_name": index_name,
            "num_result_doc": payload["num_result_doc"],
            "query_length": len(user_message),
            "headers": {k: v[:50] + "..." if len(str(v)) > 50 else v for k, v in headers.items()}
        })

        # STEP 3: API 호출 실행
        debug_print("🌐 RAG API 호출 중...")

        response = requests.post(
            base_url,
            headers=headers,
            json=payload,
            timeout=api_config.get("timeout", 30)
        )

        debug_print("📥 RAG API 응답 수신", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response_length": len(response.text) if response.text else 0
        })

        # STEP 4: 응답 처리 (범용 파서 사용)
        if response.status_code == 200:
            try:
                # 포맷 변화에 안전한 파서
                hits = _extract_hits_from_rag_response(response, debug=True)
                debug_print("📄 검색 결과 파싱", {"hit_count": len(hits)})

                documents: List[str] = []
                source_info: List[dict] = []

                # 콘텐츠/제목/URL 후보 키
                CONTENT_KEYS = ["content", "merge_title_content", "v_merge_title_content", "body", "text"]
                TITLE_KEYS   = ["title", "doc_title", "name"]
                URL_KEYS     = ["source_url", "url", "doc_url", "link"]

                for i, hit in enumerate(hits):
                    src = hit.get("_source", {}) if isinstance(hit, dict) else {}

                    # content 선택 (첫 매치)
                    content = next((src.get(k) for k in CONTENT_KEYS if src.get(k)), "")
                    title   = next((src.get(k) for k in TITLE_KEYS   if src.get(k)), f"문서_{i+1}")
                    url     = next((src.get(k) for k in URL_KEYS     if src.get(k)), "")

                    doc_id  = src.get("doc_id", "") or hit.get("_id", "")

                    # URL이 없으면 doc_id로 강제 생성
                    if not url and doc_id:
                        url = f"{CONFLUENCE_BASE}{doc_id}"

                    # 필수 보정
                    if not isinstance(content, str):
                        content = str(content) if content is not None else ""
                    if not isinstance(title, str):
                        title = str(title) if title is not None else f"문서_{i+1}"
                    if not isinstance(url, str):
                        url = str(url) if url is not None else ""

                    documents.append(content)

                    si = {
                        "title": title,
                        "doc_id": doc_id,
                        "score": hit.get("_score", 0),
                        "index": index_name,
                        "source_url": url
                    }
                    source_info.append(si)

                    # 디버그 로그
                    try:
                        print(f"[RAG][{i}] source_info =", json.dumps(si, ensure_ascii=False))
                    except Exception as _e:
                        print(f"[RAG][{i}] source_info(print 실패):", repr(_e))

                debug_print("✅ RAG 검색 완료", {
                    "documents_count": len(documents),
                    "sources_count": len(source_info)
                })

                return {
                    "documents": documents if documents else ["관련 문서를 찾을 수 없습니다."],
                    "source_info": source_info
                }

            except json.JSONDecodeError as e:
                error_msg = f"❌ JSON 파싱 실패: {str(e)}\n\n원본 응답 텍스트:\n{response.text[:1000]}"
                debug_print(error_msg, level="ERROR")
                logger.error(error_msg)
                raise ValueError(f"RAG API 응답 JSON 파싱 실패: {str(e)}")
        else:
            # 문제 5 해결: 실제 HTTP 에러와 응답 본문을 노출
            error_msg = f"❌ RAG API 호출 실패\n\nHTTP Status: {response.status_code}\nReason: {response.reason}\n\n응답 본문:\n{response.text[:1000]}"
            debug_print(error_msg, level="ERROR")
            logger.error(error_msg)
            raise requests.HTTPError(f"RAG API 호출 실패 - Status: {response.status_code}, Reason: {response.reason}, Body: {response.text[:500]}")

    except requests.Timeout as e:
        error_msg = f"❌ RAG API 타임아웃\n\n예외: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        debug_print(error_msg, level="ERROR")
        logger.error(error_msg)
        raise TimeoutError(f"RAG API 타임아웃: {str(e)}")

    except requests.RequestException as e:
        error_msg = f"❌ RAG API 요청 예외\n\n예외: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        debug_print(error_msg, level="ERROR")
        logger.error(error_msg)
        raise requests.RequestException(f"RAG API 요청 예외: {str(e)}")

    except Exception as e:
        error_msg = f"❌ RAG API 예상치 못한 예외\n\n예외 타입: {type(e).__name__}\n예외 내용: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        debug_print(error_msg, level="ERROR")
        logger.error(error_msg)
        raise Exception(f"RAG API 예상치 못한 예외 [{type(e).__name__}]: {str(e)}")


# ========================================
# 출처 정보 포맷팅 함수
# ========================================
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
