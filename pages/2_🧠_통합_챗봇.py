"""
=================================================================
🤖 AE WIKI - 통합 챗봇 페이지 (pages/2_🤖_통합_챗봇.py)
=================================================================

📋 파일 역할:
- 단일 통합 챗봇 인터페이스로 모든 RAG 인덱스를 지원
- 사용자가 인덱스를 선택하면 해당 인덱스의 데이터로 답변 제공
- 확장 가능한 구조로 새로운 인덱스 추가가 용이

🔗 주요 컴포넌트:
- 동적 인덱스 선택 버튼들 (config.py의 CHATBOT_INDICES 기반)
- 선택된 인덱스에 따른 프롬프트 자동 적용
- 각 인덱스별 전용 UI 테마 및 메시지

📊 입출력 데이터:
- 입력: 사용자 질문 + 선택된 인덱스
- 출력: 선택된 인덱스의 RAG 데이터 기반 답변
- 저장: 통합 채팅 히스토리 (인덱스별 구분)

🔄 연동 관계:
- config.py: CHATBOT_INDICES에서 모든 인덱스 설정 로드
- utils.py: get_chatbot_response_with_index() 호출
- 기존 모든 기능 유지 (로그인, 테마, 저장 등)

⚡ 처리 흐름:
인덱스 선택 -> 해당 인덱스 설정 로드 -> 질문 입력 -> RAG 검색 -> LLM 답변 생성 -> 출처 표시

🎯 확장성:
- config.py에 새 인덱스 추가 시 UI에 자동 반영
- 5개 이상의 인덱스도 동적으로 지원
- 최소한의 코드 수정으로 확장 가능
"""

import streamlit as st
import time
from datetime import datetime

from config import APP_CONFIG, CHATBOT_INDICES, get_available_indices, get_index_config
from utils import (
    initialize_data, get_chatbot_response, save_chat_history,
    require_login, initialize_session_state, get_user_id,
    get_username, get_current_user
)

# ====================================
# 🎨 페이지 설정 및 스타일
# ====================================

st.set_page_config(
    page_title=f"CHAT AEPLUS - {APP_CONFIG['page_title']}",
    page_icon="🧠",
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["initial_sidebar_state"]
)

# 다크 테마 적용
from theme import apply_dark_theme
apply_dark_theme()

# ====================================
# 🎯 메인 함수
# ====================================

def main():
    # 세션 상태 초기화 및 로그인 상태 복원
    initialize_session_state()

    # 로그인 확인
    if not require_login():
        return

    # 데이터 초기화
    data = initialize_data()

    # 통합 챗봇 페이지 표시
    show_unified_chatbot_page(data)

def show_unified_chatbot_page(data):
    """통합 챗봇 메인 페이지"""

    # 페이지 헤더
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem;
               box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
        <h3 style="color: white; margin-bottom: 1rem; font-weight: bold;">🎯 대화를 시작하려면 AI 챗봇를 선택해주세요</h3>
        <p style="color: rgba(255, 255, 255, 0.9); font-size: 1.1rem; margin-bottom: 0;">
            👇 AI 챗봇 선택하기
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 세션 상태 초기화
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None
    if "unified_chat_messages" not in st.session_state:
        st.session_state.unified_chat_messages = []
    if "current_index_config" not in st.session_state:
        st.session_state.current_index_config = {}

    # 동적 인덱스 선택 UI
    show_index_selection_ui()

    # 선택된 인덱스가 있으면 채팅 인터페이스 표시
    if st.session_state.selected_index:
        show_chat_interface(data)
    else:
        show_index_selection_guide()

def show_index_selection_ui():
    """동적 인덱스 선택 UI"""
    st.markdown("### 🎯 AI 챗봇 선택")

    # 사용 가능한 모든 인덱스 가져오기
    available_indices = get_available_indices()

    # 동적으로 버튼 생성 (3열 그리드, 6개까지 지원)
    cols = st.columns(3)

    for i, index_id in enumerate(available_indices):
        config = get_index_config(index_id)
        col_index = i % 3

        with cols[col_index]:
            # 각 인덱스별 고유한 색상과 스타일 적용
            gradient = config.get("gradient", "linear-gradient(90deg, #667eea 0%, #764ba2 100%)")
            icon = config.get("icon", "🤖")
            display_name = config.get("display_name", index_id)
            description = config.get("description", "AI 어시스턴트")

            # 선택 상태 표시
            is_selected = st.session_state.selected_index == index_id
            border_style = "border: 3px solid #28a745;" if is_selected else "border: 2px solid transparent;"

            # 호버 효과 추가
            hover_style = "transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.15);" if not is_selected else ""

            # Coming Soon 상태 확인
            is_coming_soon = config.get("coming_soon", False)

            # 카드 자체를 클릭 가능한 버튼으로 생성
            button_text = f"{icon}\n\n{display_name}\n\n{description}"
            if is_coming_soon:
                button_text += "\n\n🚀 Coming Soon!"

            button_disabled = is_coming_soon
            help_text = "곧 출시될 예정입니다!" if is_coming_soon else f"{display_name} 챗봇을 선택합니다"

            if st.button(
                button_text,
                key=f"select_{index_id}",
                use_container_width=True,
                help=help_text,
                disabled=button_disabled
            ):
                # 인덱스 변경 시 채팅 기록 초기화
                if st.session_state.selected_index != index_id:
                    st.session_state.unified_chat_messages = []

                st.session_state.selected_index = index_id
                st.session_state.current_index_config = config

                # 환영 메시지 추가
                welcome_msg = config.get("welcome_message", f"{display_name} 챗봇입니다.")
                st.session_state.unified_chat_messages = [{
                    "role": "assistant",
                    "content": welcome_msg,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "index_id": index_id
                }]

                st.rerun()

            # 선택된 상태는 버튼의 시각적 스타일로만 표시 (별도 텍스트 제거)

def show_index_selection_guide():
    """인덱스 선택 안내"""
    # 빈 함수로 변경 - 중복 표시 제거
    pass

def show_chat_interface(data):
    """선택된 인덱스의 채팅 인터페이스"""
    config = st.session_state.current_index_config
    index_id = st.session_state.selected_index

    # 🔥 대화 이력 로드 (페이지 새로고침 시에도 유지)
    # 세션 상태에 chat_history_loaded 플래그가 없거나 인덱스가 변경된 경우에만 로드
    if ("chat_history_loaded" not in st.session_state or 
        st.session_state.get("last_loaded_index") != index_id):
        
        # 저장된 대화 이력을 불러오기
        try:
            current_user = get_current_user()
            if current_user:
                user_id = current_user.get("user_id") or current_user.get("knox_id")
                
                # chat_history에서 현재 사용자 & 현재 챗봇의 최근 대화 가져오기
                all_chats = data.get("chat_history", [])
                user_chats_for_this_bot = [
                    chat for chat in all_chats
                    if (chat.get("user_id") == user_id and 
                        chat.get("chatbot_type") == index_id)
                ]
                
                # 최신 20개만 (너무 많으면 UI가 느려질 수 있음)
                user_chats_for_this_bot.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                recent_chats = user_chats_for_this_bot[:20]
                recent_chats.reverse()  # 오래된 것부터 표시하도록 다시 정렬
                
                # 세션 상태에 복원
                if recent_chats:
                    # 기존 환영 메시지는 유지하고 실제 대화만 추가
                    welcome_messages = [
                        msg for msg in st.session_state.unified_chat_messages
                        if msg.get("role") == "assistant" and "환영" in msg.get("content", "")
                    ]
                    
                    restored_messages = []
                    for chat in recent_chats:
                        # 사용자 메시지
                        restored_messages.append({
                            "role": "user",
                            "content": chat.get("user_message", ""),
                            "timestamp": chat.get("timestamp", "").split()[-1] if chat.get("timestamp") else "",
                            "index_id": index_id
                        })
                        # 봇 응답
                        restored_messages.append({
                            "role": "assistant",
                            "content": chat.get("bot_response", ""),
                            "timestamp": chat.get("timestamp", "").split()[-1] if chat.get("timestamp") else "",
                            "index_id": index_id
                        })
                    
                    # 환영 메시지 + 복원된 대화
                    st.session_state.unified_chat_messages = welcome_messages + restored_messages
        
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
        # 로드 완료 표시
        st.session_state.chat_history_loaded = True
        st.session_state.last_loaded_index = index_id

    # 현재 선택된 인덱스 표시
    gradient = config.get("gradient", "linear-gradient(90deg, #667eea 0%, #764ba2 100%)")
    display_name = config.get("display_name", index_id)
    subtitle = config.get("subtitle", "AI 어시스턴트")

    st.markdown(f"""
    <div style="background: {gradient};
               padding: 1rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
        <h3 style="color: white; margin: 0; text-align: center;">
            {config.get('icon', '🤖')} {display_name} 활성화
        </h3>
        <p style="color: #f0f0f0; text-align: center; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 채팅 기록 표시
    for message in st.session_state.unified_chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            st.caption(f"⏰ {message['timestamp']} | 📊 {message.get('index_id', 'unknown')}")

    # 채팅 입력 처리
    input_placeholder = config.get("input_placeholder", "질문을 입력하세요...")

    if prompt := st.chat_input(input_placeholder):
        # 사용자 메시지 추가
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.unified_chat_messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": timestamp,
            "index_id": index_id
        })

        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(f"⏰ {timestamp} | 📊 {index_id}")

        # AI 응답 생성 및 표시
        with st.chat_message("assistant"):
            # 대화 기록을 LLM API 형식으로 변환 (role, content)
            chat_history_for_llm = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.unified_chat_messages
                if msg["role"] in ["user", "assistant"]
            ]

            # 선택된 인덱스를 기반으로 응답 생성
            bot_response = get_chatbot_response(
                prompt,
                chat_history=chat_history_for_llm,
                chatbot_type=index_id,  # 인덱스 ID를 챗봇 타입으로 사용
                user_id=get_user_id()
            )

            # AI 응답 표시
            st.markdown(bot_response,
                        unsafe_allow_html=True)
            response_timestamp = datetime.now().strftime("%H:%M:%S")
            st.caption(f"⏰ {response_timestamp} | 📊 {index_id}")

        # AI 응답을 세션 상태에 저장
        st.session_state.unified_chat_messages.append({
            "role": "assistant",
            "content": bot_response,
            "timestamp": response_timestamp,
            "index_id": index_id
        })

        # 채팅 히스토리를 저장 (인덱스 정보 포함)
        knox_id = None
        try:
            knox_id = get_username()
        except Exception:
            knox_id = None

        if not knox_id:
            try:
                from utils import get_current_user
                knox_id = (get_current_user() or {}).get("knox_id")
            except Exception:
                knox_id = None

        if not knox_id:
            knox_id = "anonymous"

        # 저장 (신버전 우선, 구버전 fallback)
        try:
            save_chat_history(data, prompt, bot_response,
                              chatbot_type=index_id, user_id=knox_id)
        except TypeError:
            # utils.save_chat_history가 구시그니처인 경우
            save_chat_history(data, prompt, bot_response,
                              chatbot_type=index_id)

    # 사이드바: 채팅 관리 및 정보
    with st.sidebar:
        st.markdown("### 🔧 채팅 관리")

        if st.button("🗑️ 대화 기록 초기화", use_container_width=True):
            st.session_state.unified_chat_messages = []
            # 🔥 대화 이력 로드 플래그 초기화
            st.session_state.chat_history_loaded = False
            # 환영 메시지 다시 추가
            if st.session_state.selected_index:
                config = st.session_state.current_index_config
                welcome_msg = config.get("welcome_message", "챗봇입니다.")
                st.session_state.unified_chat_messages = [{
                    "role": "assistant",
                    "content": welcome_msg,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "index_id": st.session_state.selected_index
                }]
            st.success("대화 기록이 초기화되었습니다!")
            time.sleep(0.5)
            st.rerun()

        if st.button("🔄 인덱스 다시 선택", use_container_width=True):
            st.session_state.selected_index = None
            st.session_state.unified_chat_messages = []
            st.session_state.current_index_config = {}
            # 🔥 대화 이력 로드 플래그 초기화
            st.session_state.chat_history_loaded = False
            st.rerun()

        st.markdown("---")

        # 현재 활성 인덱스 정보
        if st.session_state.selected_index:
            config = st.session_state.current_index_config
            st.markdown("### 📊 현재 활성 인덱스")
            st.markdown(f"""
            **이름**: {config.get('display_name', 'Unknown')}
            **인덱스**: `{config.get('index_name', 'unknown')}`
            **ID**: `{st.session_state.selected_index}`
            """)


# ====================================
# 🚀 앱 실행
# ====================================

if __name__ == "__main__":
    main()