# 📋 AE WIKI 챗봇 처리 플로우 상세 리포트

**프로젝트**: AE WIKI 통합 챗봇 시스템
**작성일**: 2025년 10월 2일
**분석 대상**: "김민국" 입력 시 처리 과정
**시스템 모드**: Mock 응답 모드

---

## 🎯 개요

본 리포트는 AE WIKI 통합 챗봇에서 사용자가 "김민국"이라고 입력했을 때, 시스템 내부에서 어떤 함수들이 순차적으로 호출되고 어떤 프롬프트와 로직을 거쳐 최종 응답이 생성되는지를 상세히 분석한 기술 문서입니다.

---

## 1️⃣ 사용자 입력 단계

### 📍 위치
- **파일**: `pages/2_🤖_통합_챗봇.py`
- **라인**: 226

### 🔧 처리 과정
```python
if prompt := st.chat_input(input_placeholder):
    # 사용자가 "김민국" 입력
```

### 📊 세부 내용
1. **입력 위젯**: Streamlit의 `st.chat_input()` 컴포넌트
2. **플레이스홀더**: `"AE팀 업무에 대해 궁금한 것을 질문해보세요..."`
3. **입력값**: `"김민국"`
4. **변수 할당**: `prompt = "김민국"`
5. **타임스탬프 생성**: `datetime.now().strftime("%H:%M:%S")`

---

## 2️⃣ 세션 상태 업데이트

### 📍 위치
- **파일**: `pages/2_🤖_통합_챗봇.py`
- **라인**: 229-235

### 🔧 처리 과정
```python
st.session_state.unified_chat_messages.append({
    "role": "user",
    "content": prompt,        # "김민국"
    "timestamp": timestamp,  # "15:30:45"
    "index_id": index_id     # "ae_wiki"
})
```

### 📊 저장 데이터 구조
```json
{
    "role": "user",
    "content": "김민국",
    "timestamp": "15:30:45",
    "index_id": "ae_wiki"
}
```

---

## 3️⃣ 메인 챗봇 응답 함수 호출

### 📍 위치
- **파일**: `pages/2_🤖_통합_챗봇.py`
- **라인**: 230-235

### 🔧 함수 호출
```python
bot_response = get_chatbot_response(
    prompt,                 # "김민국"
    chat_history=None,
    chatbot_type=index_id,  # "ae_wiki"
    user_id=get_user_id()   # 현재 사용자 ID
)
```

### 🎯 호출 대상
- **함수**: `get_chatbot_response()`
- **파일**: `utils.py`
- **라인**: 224

---

## 4️⃣ RAG 검색 단계

### 📍 위치
- **파일**: `utils.py`
- **라인**: 228

### 🔧 RAG API 호출
```python
rag_result = call_rag_api_with_chatbot_type(user_message, chatbot_type)
# call_rag_api_with_chatbot_type("김민국", "ae_wiki")
```

### 4-1. Mock 모드 확인

#### 📍 위치
- **파일**: `api_manager.py`
- **라인**: 374

#### 🔧 조건 체크
```python
if TEST_CONFIG.get("enable_mock_mode", True):
    return get_mock_rag_response(user_message, chatbot_type)
```

#### 📊 설정값
- **파일**: `config.py`
- **라인**: 81
- **값**: `"enable_mock_mode": True`

### 4-2. Mock RAG 응답 생성

#### 📍 위치
- **파일**: `api_manager.py`
- **라인**: 144-200

#### 🔧 함수 실행
```python
def get_mock_rag_response(user_message: str, chatbot_type: str) -> dict:
    # user_message = "김민국"
    # chatbot_type = "ae_wiki"
```

#### 📊 생성되는 Mock 응답
```python
{
    "documents": [
        "AE팀 업무 프로세스 관련 문서입니다. 질문: '김민국'에 대한 상세 답변을 제공합니다. 최신 가이드라인에 따르면...",
        "반도체 제품 사양 관련 내용입니다. '김민국' 관련하여 기술적 세부사항과 적용 방법을 설명합니다.",
        "고객 지원 절차 문서에서 발췌한 내용입니다. '김민국'와 관련된 업무 프로세스를 안내합니다."
    ],
    "source_info": [
        {
            "source": "AE팀 업무 가이드 v2.1",
            "last_modified": "2025-10-01",
            "date_score": 1.0,
            "relevance_score": 0.95,
            "confluence_url": "https://confluence.company.com/display/AE/Process-Guide"
        },
        {
            "source": "반도체 제품 사양서 v2.0",
            "last_modified": "2025-09-25",
            "date_score": 0.8,
            "relevance_score": 0.88,
            "confluence_url": "https://confluence.company.com/display/AE/Product-Spec"
        },
        {
            "source": "고객 지원 매뉴얼 v1.0",
            "last_modified": "2025-09-02",
            "date_score": 0.3,
            "relevance_score": 0.82,
            "confluence_url": "https://confluence.company.com/display/AE/Customer-Support"
        }
    ]
}
```

---

## 5️⃣ LLM 응답 생성 단계

### 📍 위치
- **파일**: `utils.py`
- **라인**: 233-241

### 🔧 LLM API 호출
```python
response = call_llm_api(
    user_message="김민국",
    retrieve_data=["AE팀 업무 프로세스 관련 문서입니다...", "반도체 제품 사양 관련...", "고객 지원 절차..."],
    chat_history=None,
    source_data=[{"source": "AE팀 업무 가이드 v2.1", ...}, ...],
    user_id=user_id,
    custom_system_prompt=None,
    chatbot_type="ae_wiki"
)
```

### 5-1. LLM API 함수 호출

#### 📍 위치
- **파일**: `api_manager.py`
- **라인**: 39

#### 🔧 함수 정의
```python
def call_llm_api(user_message: str, retrieve_data: List[str],
                 chat_history: list = None, source_data: List[dict] = None,
                 user_id: str = None, custom_system_prompt: str = None,
                 chatbot_type: str = "ae_wiki") -> str:
```

### 5-2. Mock 모드 재확인

#### 📍 위치
- **파일**: `api_manager.py`
- **라인**: 74

#### 🔧 처리 로직
```python
if TEST_CONFIG.get("enable_mock_mode", True):
    combined_text = "\n\n".join(retrieve_data)
    source_citations = format_source_citations(source_data, chatbot_type)
    system_prompt = get_index_system_prompt(chatbot_type)
    return get_mock_llm_response(user_message, combined_text, source_citations, chatbot_type, system_prompt)
```

### 5-3. 시스템 프롬프트 로드

#### 📍 위치
- **호출**: `utils.py:208`
- **설정**: `config.py:127-133`

#### 🔧 로드되는 시스템 프롬프트
```
당신은 삼성전자 메모리사업부 전략마케팅 실 AE팀의 기술 Q&A 어시스턴트입니다.
- 범위: 반도체 제품/공정/용어, AE팀 관련 문서로 확인 가능한 내용
- 목표: 사용자가 빠르게 업무에 적용할 수 있는 정확·간결한 답변
- 원칙:
  1) 제공된 문서(컨텍스트)와 과거 대화, 사용자 질문에만 근거해 답변한다.
  2) 문서에 없는 정보는 추측하지 않으며, 필요 시 "문서에 근거 없음"이라고 말한다.
  3) 구체적이고 실무에 바로 적용 가능한 답변을 제공한다.
```

### 5-4. 출처 정보 포맷팅

#### 📍 위치
- **파일**: `api_manager.py`
- **함수**: `format_source_citations()`

#### 🔧 포맷팅 결과
```
**📚 참고 자료:**
📄 **AE팀 업무 가이드 v2.1** - [Confluence 링크](https://confluence.company.com/display/AE/Process-Guide) (수정일: 2025-10-01)
📄 **반도체 제품 사양서 v2.0** - [Confluence 링크](https://confluence.company.com/display/AE/Product-Spec) (수정일: 2025-09-25)
📄 **고객 지원 매뉴얼 v1.0** - [Confluence 링크](https://confluence.company.com/display/AE/Customer-Support) (수정일: 2025-09-02)
```

### 5-5. Mock LLM 응답 생성

#### 📍 위치
- **파일**: `api_manager.py`
- **라인**: 241-300

#### 🔧 함수 실행
```python
def get_mock_llm_response(user_message: str, retrieve_text: str,
                         source_citations: str, chatbot_type: str, system_prompt: str):
    # user_message = "김민국"
    # chatbot_type = "ae_wiki"
```

#### 📊 생성되는 최종 응답
```markdown
안녕하세요! AE WIKI 전문 챗봇입니다. 🧠

**질문 분석**: "김민국"

**답변**:
검색된 AE팀 업무 문서를 바탕으로 답변드리겠습니다.

"김민국"에 대한 상세한 답변을 제공합니다. AE팀의 최신 업무 프로세스와 가이드라인에 따르면, 다음과 같은 절차를 따르시면 됩니다:

1. **주요 단계 및 절차**
   - 관련 문서 및 규정 확인
   - 팀 내부 승인 프로세스 진행
   - 고객사 및 관련 부서와의 협의

2. **주의사항**
   - 최신 업데이트된 정보 반영 필요
   - 보안 및 품질 기준 준수 필수
   - 정확한 문서화 및 이력 관리

더 자세한 내용은 검색된 문서나 팀 내 담당자에게 문의해주세요.

**📚 참고 자료:**
📄 **AE팀 업무 가이드 v2.1** - [Confluence 링크](https://confluence.company.com/display/AE/Process-Guide) (수정일: 2025-10-01)
📄 **반도체 제품 사양서 v2.0** - [Confluence 링크](https://confluence.company.com/display/AE/Product-Spec) (수정일: 2025-09-25)
📄 **고객 지원 매뉴얼 v1.0** - [Confluence 링크](https://confluence.company.com/display/AE/Customer-Support) (수정일: 2025-09-02)
```

---

## 6️⃣ 응답 표시 및 저장

### 6-1. UI 표시

#### 📍 위치
- **파일**: `pages/2_🤖_통합_챗봇.py`
- **라인**: 237-240

#### 🔧 렌더링 코드
```python
with st.chat_message("assistant"):
    st.markdown(bot_response)  # 생성된 응답 표시
    response_timestamp = datetime.now().strftime("%H:%M:%S")
    st.caption(f"⏰ {response_timestamp} | 📊 ae_wiki")
```

### 6-2. 세션 상태 저장

#### 📍 위치
- **파일**: `pages/2_🤖_통합_챗봇.py`
- **라인**: 242-248

#### 🔧 저장 로직
```python
st.session_state.unified_chat_messages.append({
    "role": "assistant",
    "content": bot_response,
    "timestamp": response_timestamp,
    "index_id": "ae_wiki"
})
```

### 6-3. 채팅 기록 영구 저장

#### 📍 위치
- **호출**: `pages/2_🤖_통합_챗봇.py:251`
- **함수**: `chat_manager.py:32`

#### 🔧 저장 함수 호출
```python
save_chat_history(data, "김민국", bot_response, chatbot_type="ae_wiki")
```

#### 📊 저장되는 데이터 구조
```python
chat_entry = {
    "id": "chat_20251002_153045_123456",
    "timestamp": "2025-10-02 15:30:45",
    "user_id": "user_20251001_120000",
    "username": "hong.gildong",
    "chatbot_type": "ae_wiki",
    "user_message": "김민국",
    "bot_response": "안녕하세요! AE WIKI 전문 챗봇입니다...",
    "message_length": 3,
    "response_length": 1250
}
```

#### 🔧 저장 위치
- **파일**: `datalog/knowledge_data.json`
- **키**: `chat_history` 배열에 추가

---

## 📊 전체 함수 호출 체인

```
1. st.chat_input()
   └─ prompt = "김민국"

2. get_chatbot_response("김민국", chatbot_type="ae_wiki")
   └─ utils.py:224

3. call_rag_api_with_chatbot_type("김민국", "ae_wiki")
   ├─ api_manager.py:369
   └─ get_mock_rag_response("김민국", "ae_wiki")
       └─ api_manager.py:144

4. call_llm_api("김민국", retrieve_data, chatbot_type="ae_wiki")
   ├─ api_manager.py:39
   ├─ get_index_system_prompt("ae_wiki")
   │   └─ config.py:127 (시스템 프롬프트 로드)
   ├─ format_source_citations(source_data, "ae_wiki")
   │   └─ api_manager.py:405 (출처 포맷팅)
   └─ get_mock_llm_response("김민국", combined_text, citations, "ae_wiki", system_prompt)
       └─ api_manager.py:241

5. save_chat_history(data, "김민국", bot_response, "ae_wiki")
   └─ chat_manager.py:32

6. st.markdown(bot_response)
   └─ UI에 최종 응답 표시
```

---

## ⚙️ 핵심 설정 및 구성 파일

### 📁 설정 파일들

1. **`config.py`**
   - AE WIKI 시스템 프롬프트 정의
   - 챗봇 인덱스 설정 (display_name, description 등)
   - Mock 모드 설정

2. **`api_manager.py`**
   - Mock RAG/LLM 응답 생성 로직
   - 실제 API 호출 대비 폴백 시스템

3. **`chat_manager.py`**
   - 채팅 기록 저장 및 관리
   - 슬라이딩 윈도우 메모리 관리

4. **`utils.py`**
   - 모든 모듈 통합 관리
   - 하위 호환성 유지

### 📊 데이터 흐름

```
사용자 입력 → 세션 상태 → RAG 검색 → LLM 생성 → UI 표시 → 영구 저장
    ↓            ↓           ↓          ↓         ↓         ↓
  "김민국"    chat_messages  Mock 문서   Mock 응답  st.markdown  JSON 파일
```

---

## 🔄 Mock vs 실제 모드 비교

### Mock 모드 (현재 상태)
- **설정**: `TEST_CONFIG["enable_mock_mode"] = True`
- **RAG**: 미리 정의된 템플릿 문서 반환
- **LLM**: 패턴 기반 응답 생성
- **장점**: 빠른 응답, 개발/테스트 용이
- **단점**: 실제 검색 및 생성 불가

### 실제 모드 (프로덕션)
- **설정**: `TEST_CONFIG["enable_mock_mode"] = False`
- **RAG**: 실제 Confluence 문서 검색
- **LLM**: 실제 대화형 AI 모델 사용
- **장점**: 정확한 정보 검색 및 생성
- **단점**: API 의존성, 응답 시간

---

## 🚀 성능 및 최적화 고려사항

### 📈 처리 시간 분석
1. **사용자 입력**: ~10ms (UI 렌더링)
2. **RAG 검색**: ~500ms (Mock), ~2-3초 (실제)
3. **LLM 생성**: ~300ms (Mock), ~5-10초 (실제)
4. **UI 표시**: ~50ms
5. **데이터 저장**: ~100ms

### 🔧 최적화 포인트
1. **캐싱**: RAG 검색 결과 캐싱
2. **비동기 처리**: UI 업데이트와 저장 병렬 처리
3. **슬라이딩 윈도우**: 채팅 기록 메모리 관리
4. **에러 핸들링**: API 실패 시 폴백 메커니즘

---

## 📋 결론

AE WIKI 챗봇 시스템은 모듈화된 아키텍처를 통해 사용자 입력부터 최종 응답까지의 전체 플로우를 체계적으로 관리합니다. 현재 Mock 모드로 동작하여 개발 및 테스트가 용이하며, 실제 프로덕션 환경에서는 동일한 플로우를 통해 실제 RAG 검색과 LLM 생성이 이루어집니다.

**핵심 특징:**
- ✅ 모듈화된 구조로 유지보수 용이
- ✅ Mock/실제 모드 양방향 지원
- ✅ 완전한 채팅 기록 및 세션 관리
- ✅ 에러 핸들링 및 폴백 시스템
- ✅ 확장 가능한 인덱스 구조

---

**작성자**: Claude Code AI Assistant
**검토일**: 2025년 10월 2일
**문서 버전**: v1.0