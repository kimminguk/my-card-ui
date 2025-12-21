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
import logging
from datetime import datetime

from config import APP_CONFIG, CHATBOT_INDICES, get_available_indices, get_index_config
from utils import (
    initialize_data, get_chatbot_response, save_chat_history,
    require_login, initialize_session_state, get_user_id,
    get_username, get_current_user, get_user_chat_history
)

# 로거 설정
logger = logging.getLogger(__name__)

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
# 🔧 헬퍼 함수
# ====================================

def save_chat_history_with_session(data, user_message, bot_response, chatbot_type="ae_wiki",
                                   user_id=None, session_id=None, conversation_title=None):
    """세션 정보를 포함하여 채팅 기록 저장"""
    from data_manager import save_data

    try:
        # 기본 채팅 기록 저장
        if "chat_history" not in data:
            data["chat_history"] = []

        chat_entry = {
            "id": f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id or "anonymous",
            "username": get_username() or "anonymous",
            "chatbot_type": chatbot_type,
            "user_message": user_message,
            "bot_response": bot_response,
            "session_id": session_id,
            "conversation_title": conversation_title,
            "message_length": len(user_message),
            "response_length": len(bot_response)
        }

        data["chat_history"].append(chat_entry)

        # 슬라이딩 윈도우 적용 (최대 1000개 대화 유지)
        if len(data["chat_history"]) > 1000:
            data["chat_history"] = data["chat_history"][-1000:]

        save_data(data)
    except Exception as e:
        st.error(f"채팅 기록 저장 실패: {e}")

def get_user_conversation_sessions(data, user_id=None, limit=10):
    """사용자의 대화 세션 목록 조회 (개선된 사용자 식별)"""
    try:
        # 사용자 ID 확인 (다양한 방법으로 시도)
        if not user_id:
            try:
                user_id = get_user_id()
            except:
                pass

            if not user_id:
                try:
                    current_user = get_current_user()
                    if current_user:
                        user_id = current_user.get("knox_id") or current_user.get("user_id") or current_user.get("username")
                except:
                    pass

            if not user_id:
                user_id = st.session_state.get("auth_knox_id") or st.session_state.get("auth_user")

            if not user_id:
                try:
                    user_id = get_username()
                except:
                    user_id = "anonymous"

        logger.info(f"대화 기록 조회: user_id={user_id}")

        if "chat_history" not in data:
            return []

        # 세션별로 그룹화 (더 유연한 사용자 매칭)
        sessions = {}
        for chat in data["chat_history"]:
            # 사용자 매칭: user_id, username, knox_id 모두 확인
            chat_user_id = chat.get("user_id", "")
            chat_username = chat.get("username", "")

            if (chat_user_id == user_id or
                chat_username == user_id or
                chat_user_id in [user_id] or
                chat_username in [user_id]):

                session_id = chat.get("session_id", "unknown")
                if session_id not in sessions:
                    sessions[session_id] = {
                        "session_id": session_id,
                        "conversation_title": chat.get("conversation_title", "제목 없음"),
                        "chatbot_type": chat.get("chatbot_type", "unknown"),
                        "first_message_time": chat.get("timestamp", ""),
                        "message_count": 0,
                        "messages": []
                    }
                sessions[session_id]["message_count"] += 1
                sessions[session_id]["messages"].append(chat)

        # 최신순 정렬
        sorted_sessions = sorted(
            sessions.values(),
            key=lambda x: x["first_message_time"],
            reverse=True
        )

        return sorted_sessions[:limit]
    except Exception as e:
        st.error(f"세션 조회 실패: {e}")
        return []

def show_conversation_history_sidebar(data):
    """사이드바에 대화 기록 표시 (날짜별 그룹화)"""
    st.markdown("### 📚 대화 기록")

    user_id = get_user_id() or get_username() or "anonymous"
    sessions = get_user_conversation_sessions(data, user_id, limit=20)

    if not sessions:
        st.info("저장된 대화 기록이 없습니다.")
        return

    # 날짜별로 그룹화
    sessions_by_date = {}
    for session in sessions:
        # timestamp에서 날짜만 추출 (YYYY-MM-DD 형식)
        timestamp = session.get('first_message_time', '')
        if timestamp:
            date = timestamp.split()[0]  # "2025-12-21 14:30:00" -> "2025-12-21"
        else:
            date = "날짜 없음"

        if date not in sessions_by_date:
            sessions_by_date[date] = []

        sessions_by_date[date].append(session)

    # 날짜별로 표시 (최신 날짜가 위로)
    sorted_dates = sorted(sessions_by_date.keys(), reverse=True)

    for date in sorted_dates:
        # 날짜 헤더
        date_display = date if date != "날짜 없음" else "날짜 없음"
        st.markdown(f"**📅 {date_display}**")

        # 해당 날짜의 대화들
        for session in sessions_by_date[date]:
            # 시간만 추출
            timestamp = session.get('first_message_time', '')
            time_only = timestamp.split()[1][:5] if len(timestamp.split()) > 1 else ""  # "14:30"

            # 대화 제목만 표시 (시간 포함)
            title = session.get('conversation_title', '제목 없음')
            display_title = f"{time_only} - {title[:25]}..." if len(title) > 25 else f"{time_only} - {title}"

            if st.button(
                display_title,
                key=f"load_session_{session['session_id']}",
                use_container_width=True,
                help=f"클릭하여 이 대화를 불러옵니다"
            ):
                load_conversation(session)
                st.rerun()

        st.markdown("")  # 날짜 그룹 사이 여백

def load_conversation(session):
    """이전 대화를 불러오기"""
    try:
        # 세션 ID 및 제목 설정
        st.session_state.conversation_session_id = session["session_id"]
        st.session_state.conversation_title = session["conversation_title"]
        st.session_state.selected_index = session["chatbot_type"]

        # 인덱스 설정 로드
        config = get_index_config(session["chatbot_type"])
        st.session_state.current_index_config = config

        # 메시지 복원
        st.session_state.unified_chat_messages = []

        # 환영 메시지 추가
        welcome_msg = config.get("welcome_message", "챗봇입니다.")
        st.session_state.unified_chat_messages.append({
            "role": "assistant",
            "content": welcome_msg,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "index_id": session["chatbot_type"]
        })

        # 대화 내역 복원
        for msg in session["messages"]:
            # 사용자 메시지
            st.session_state.unified_chat_messages.append({
                "role": "user",
                "content": msg["user_message"],
                "timestamp": msg["timestamp"].split()[1] if " " in msg["timestamp"] else msg["timestamp"],
                "index_id": session["chatbot_type"]
            })

            # 봇 응답
            st.session_state.unified_chat_messages.append({
                "role": "assistant",
                "content": msg["bot_response"],
                "timestamp": msg["timestamp"].split()[1] if " " in msg["timestamp"] else msg["timestamp"],
                "index_id": session["chatbot_type"]
            })

        st.success(f"'{session['conversation_title']}' 대화를 불러왔습니다!")
    except Exception as e:
        st.error(f"대화 불러오기 실패: {e}")

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
    if "conversation_session_id" not in st.session_state:
        st.session_state.conversation_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if "conversation_title" not in st.session_state:
        st.session_state.conversation_title = None

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

    # 현재 선택된 인덱스 표시
    gradient = config.get("gradient", "linear-gradient(90deg, #667eea 0%, #764ba2 100%)")
    display_name = config.get("display_name", index_id)
    subtitle = config.get("subtitle", "AI 어시스턴트")

    st.markdown(f"""
    <div style="background: {gradient};
               padding: 1rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
        <h3 style="color: white; margin: 0; text-align: center;">
            {config.get('icon', '🤖')} {display_name}
        </h3>
        <p style="color: #f0f0f0; text-align: center; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 채팅 기록 표시
    for idx, message in enumerate(st.session_state.unified_chat_messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            st.caption(f"⏰ {message['timestamp']}")

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
        # 올바른 사용자 식별자 확인 (knox_id 우선)
        knox_id = None

        # 방법 1: get_user_id() 사용 (auth_manager에서 제공)
        try:
            knox_id = get_user_id()
        except Exception as e:
            logger.warning(f"get_user_id() 실패: {e}")
            knox_id = None

        # 방법 2: get_current_user()에서 knox_id 추출
        if not knox_id:
            try:
                current_user = get_current_user()
                if current_user:
                    knox_id = current_user.get("knox_id") or current_user.get("user_id") or current_user.get("username")
            except Exception as e:
                logger.warning(f"get_current_user() 실패: {e}")
                knox_id = None

        # 방법 3: 세션 상태에서 직접 가져오기
        if not knox_id:
            knox_id = st.session_state.get("auth_knox_id") or st.session_state.get("auth_user")

        # 방법 4: get_username() fallback
        if not knox_id:
            try:
                knox_id = get_username()
            except Exception:
                knox_id = None

        # 최종 fallback
        if not knox_id or knox_id.strip() == "":
            knox_id = "anonymous"
            logger.warning("사용자 식별자를 찾을 수 없어 'anonymous'로 저장합니다.")
        else:
            logger.info(f"대화 기록 저장: user_id={knox_id}")

        # 자동 대화 제목 생성 (첫 메시지인 경우)
        if not st.session_state.conversation_title:
            # 첫 질문을 기반으로 제목 생성 (최대 50자)
            st.session_state.conversation_title = prompt[:50] + ("..." if len(prompt) > 50 else "")

        # 저장 (신버전 우선, 구버전 fallback)
        try:
            save_chat_history_with_session(
                data,
                prompt,
                bot_response,
                chatbot_type=index_id,
                user_id=knox_id,
                session_id=st.session_state.conversation_session_id,
                conversation_title=st.session_state.conversation_title
            )
        except:
            # Fallback to original function
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

        if st.button("🆕 새 대화 시작", use_container_width=True, type="primary"):
            # 새 세션 ID 생성
            st.session_state.conversation_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.conversation_title = None
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
            st.success("새 대화를 시작합니다!")
            time.sleep(0.5)
            st.rerun()

        st.markdown("---")

        # 대화 기록 표시
        show_conversation_history_sidebar(data)


# ====================================
# 🚀 앱 실행
# ====================================

if __name__ == "__main__":
    main()