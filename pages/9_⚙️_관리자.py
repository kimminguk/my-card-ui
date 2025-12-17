"""
AE WIKI - 관리자 페이지
시스템 관리, 로그 조회, 데이터 관리 기능을 제공하는 관리자 전용 페이지
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import io

from config import APP_CONFIG, DATA_CONFIG, AUTH_CONFIG
from utils import (
    initialize_data, is_logged_in, require_login,
    get_username, load_css_styles, get_all_users, search_users,
    toggle_user_status, delete_user, update_user_info,
    get_all_user_points, adjust_user_points, set_user_points, get_point_change_history,
    cleanup_duplicate_points_data,
    get_pending_registration_requests,
    approve_registration_request,
    reject_registration_request, resolve_user_label,
    resolve_to_knox_id
)
# 새 통합 사용자 관리 시스템 import
from user_manager import get_pending_requests, approve_registration_request as approve_new, reject_registration_request as reject_new

# ====================================
# 🎨 페이지 설정 및 스타일
# ====================================

st.set_page_config(
    page_title="⚙️",
    page_icon="⚙️",
    layout=APP_CONFIG["layout"]
)

# 다크 테마 적용
from theme import apply_dark_theme
apply_dark_theme()

# ====================================
# 🛡️ 관리자 인증 함수
# ====================================

def require_admin():
    """관리자 권한 확인 - 로그인 없이도 관리자 비밀번호로 접근 가능"""
    # 세션에 관리자 인증 상태가 있는지 확인
    if st.session_state.get('admin_authenticated', False):
        return True
    
    # 일반 로그인된 사용자가 관리자 계정인지 확인
    if is_logged_in():
        current_user = get_username()
        admin_users = ["admin", "관리자"]
        if current_user in admin_users:
            st.session_state.admin_authenticated = True
            return True
    
    # 관리자 비밀번호 인증 폼 표시
    st.error("🚫 **관리자 권한이 필요합니다**")
    st.markdown("---")
    
    st.markdown("### 🛡️ 관리자 인증")
    st.info("💡 로그인 없이 관리자 비밀번호만으로 접근할 수 있습니다.")
    
    with st.form("admin_login_form"):
        admin_password = st.text_input(
            "관리자 비밀번호", 
            type="password", 
            placeholder="관리자 비밀번호를 입력하세요"
        )
        login_button = st.form_submit_button("🚪 관리자로 로그인", type="primary")
        
        if login_button:
            if admin_password == "admin123":  # config.py의 admin_password와 일치
                st.session_state.admin_authenticated = True
                st.success("✅ 관리자로 인증되었습니다!")
                st.rerun()
            else:
                st.error("❌ 관리자 비밀번호가 틀렸습니다.")
    
    return False

# ====================================
# 🎯 메인 함수
# ====================================

def main():
    # 관리자 권한 확인 (로그인 없이도 관리자 비밀번호로 접근 가능)
    if not require_admin():
        return
    
    # 데이터 초기화
    data = initialize_data()
    
    # 메인 콘텐츠
    show_admin_page(data)

def show_admin_page(data):
    """관리자 페이지 메인"""
    
    # 페이지 헤더
    col1, col2 = st.columns([8, 2])
    
    with col1:
        st.title("⚙️ 관리자 대시보드")
        st.markdown("📊 시스템 관리 및 데이터 분석 도구")
        
        # 회원가입 신청 알림 표시
        try:
            from user_manager import get_pending_requests
            pending_requests = get_pending_requests()
            if pending_requests:
                st.warning(f"🔔 **회원가입 승인 대기: {len(pending_requests)}건** - '회원 승인' 탭에서 확인하세요!")
        except:
            pass
    
    with col2:
        st.caption(f"👤 {get_username()}님 (관리자)")
        if st.button("🚪 로그아웃", type="secondary"):
            # 관리자 인증 상태 클리어
            if 'admin_authenticated' in st.session_state:
                del st.session_state.admin_authenticated
            
            # 일반 로그인 상태도 클리어 (필요한 경우)
            from utils import logout_user
            logout_user()
            
            # 홈페이지로 리다이렉트
            st.success("✅ 로그아웃되었습니다.")
            st.switch_page("🏠_Home.py")
    
    # 대시보드 탭
    tabs = st.tabs([
        "📊 전체 현황",
        "👥 회원 관리",
        "✅ 회원 승인",
        "🎁 포인트 관리",
        "📝 VOC 관리",
        "📚 WIKI 학습 관리",
        "🚀 인덱스 관리",
        "📋 로그 관리",
        "💬 대화 기록",
        "🧠 대화 메모리",
        "📈 통계 분석",
        "⚙️ 시스템 설정"
    ])
    
    with tabs[0]:
        show_dashboard_overview(data)

    with tabs[1]:
        show_user_management()

    with tabs[2]:
        show_registration_approval(data)

    with tabs[3]:
        show_points_management(data)

    with tabs[4]:
        show_voc_management()

    with tabs[5]:
        show_wiki_learning_management()

    with tabs[6]:
        show_index_management()

    with tabs[7]:
        show_log_management(data)

    with tabs[8]:
        show_chat_history(data)

    with tabs[9]:
        show_conversation_memory_manager()

    with tabs[10]:
        show_statistics(data)

    with tabs[11]:
        show_system_settings(data)

def show_dashboard_overview(data):
    """전체 현황 대시보드"""
    st.markdown("### 📊 전체 현황")
    
    # 주요 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📝 전체 질문 수", 
            len(data["questions"]),
            delta=get_today_count(data["questions"])
        )
    
    with col2:
        st.metric(
            "💬 전체 답변 수", 
            len(data["answers"]),
            delta=get_today_count(data["answers"])
        )
    
    with col3:
        chat_count = len(data.get("chat_history", []))
        st.metric(
            "🤖 챗봇 대화 수", 
            chat_count,
            delta=get_today_chat_count(data)
        )
    
    with col4:
        search_count = len(data.get("search_logs", []))
        st.metric(
            "🔍 검색 수행 수", 
            search_count,
            delta=get_today_search_count(data)
        )
    
    st.markdown("---")
    
    # 최근 활동
    st.markdown("### 📋 최근 활동")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🆕 최근 질문 (5개)**")
        recent_questions = sorted(data["questions"], 
                                key=lambda x: x["timestamp"], reverse=True)[:5]
        
        if recent_questions:
            for q in recent_questions:
                st.markdown(f"• **{q['title']}** `[{q['category']}]`")
                st.markdown(f"  _{q['author']} - {q['timestamp']}_")
        else:
            st.info("등록된 질문이 없습니다.")
    
    with col2:
        st.markdown("**💬 최근 답변 (5개)**")
        recent_answers = sorted(data["answers"], 
                              key=lambda x: x["timestamp"], reverse=True)[:5]
        
        if recent_answers:
            for a in recent_answers:
                question = next((q for q in data["questions"] if q["id"] == a["question_id"]), None)
                q_title = question["title"] if question else "삭제된 질문"
                st.markdown(f"• **{q_title}**에 답변")
                st.markdown(f"  _{a['author']} - {a['timestamp']}_")
        else:
            st.info("등록된 답변이 없습니다.")

def show_user_management():
    """회원 관리"""
    st.markdown("### 👥 회원 관리")
    
    # 검색 및 필터
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        search_keyword = st.text_input("🔍 회원 검색", placeholder="녹스아이디, 닉네임, 부서로 검색")
    
    with col2:
        department_filter = st.selectbox("부서 필터", ["전체"] + AUTH_CONFIG["departments"])
    
    with col3:
        if st.button("📥 회원 목록 다운로드"):
            download_user_list()
    
    # 회원 목록 조회
    users = search_users(search_keyword)
    
    # 부서 필터 적용
    if department_filter != "전체":
        users = [user for user in users if user.get("department") == department_filter]
    
    # 회원 통계
    all_users = get_all_users()
    total_users = len(all_users)
    active_users = len([u for u in all_users if u.get("is_active", True)])
    inactive_users = len([u for u in all_users if not u.get("is_active", True)])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("전체 회원", total_users)
    
    with col2:
        st.metric("활성 회원", active_users)
    
    with col3:
        st.metric("비활성 회원", inactive_users)
    
    with col4:
        st.metric("검색 결과", len(users))
    
    st.markdown("---")
    
    # 회원 목록 표시
    if users:
        st.markdown(f"#### 📋 회원 목록 ({len(users)}명)")
        
        # 정렬 옵션
        sort_options = ["등록일순", "이름순", "부서순", "최근 로그인순"]
        sort_by = st.selectbox("정렬 기준", sort_options)
        
        # 정렬 적용
        if sort_by == "등록일순":
            users = sorted(users, key=lambda x: x["created_at"], reverse=True)
        elif sort_by == "이름순":
            users = sorted(users, key=lambda x: x["nickname"])
        elif sort_by == "부서순":
            users = sorted(users, key=lambda x: x["department"])
        elif sort_by == "최근 로그인순":
            users = sorted(users, key=lambda x: x.get("last_login", ""), reverse=True)
        
        # 페이지네이션 (간단 버전)
        if len(users) > 20:
            st.info(f"💡 총 {len(users)}명의 회원이 있습니다. 상위 20명만 표시됩니다.")
            users = users[:20]
        
        # 회원 카드 표시
        for i, user in enumerate(users, 1):
            show_user_card(user, i)
    
    else:
        st.info("검색 조건에 맞는 회원이 없습니다.")

def show_user_card(user, index):
    """회원 카드 표시"""
    
    with st.container():
        # 회원 상태에 따른 색상
        status_color = "🟢" if user.get("is_active", True) else "🔴"
        status_text = "활성" if user.get("is_active", True) else "비활성"
        
        # 헤더
        col1, col2, col3 = st.columns([6, 2, 2])
        
        with col1:
            st.markdown(f"**{index}. {status_color} {user['nickname']}** `({user['knox_id']})`")
        
        with col2:
            st.markdown(f"**{user['department']}**")
        
        with col3:
            st.markdown(f"_{status_text}_")
        
        # 상세 정보
        col1, col2, col3 = st.columns(3)
        
        with col1:
            created_at = user.get('created_at', '정보 없음')
            if created_at and created_at != '정보 없음':
                created_at = created_at.split()[0]  # 날짜만 표시
            st.markdown(f"📅 **등록일**: {created_at}")
        
        with col2:
            last_login = user.get('last_login')
            if last_login and last_login != '접속 기록 없음':
                last_login = last_login.split()[0]  # 날짜만 표시
            else:
                last_login = '접속 기록 없음'
            st.markdown(f"🕐 **마지막 로그인**: {last_login}")
        
        with col3:
            # 관리 버튼들
            col_edit, col_toggle, col_delete = st.columns(3)
            
            with col_edit:
                if st.button("✏️", key=f"edit_{user['user_id']}", help="정보 수정"):
                    st.session_state[f"editing_{user['user_id']}"] = True
                    st.rerun()
            
            with col_toggle:
                action_text = "비활성화" if user.get("is_active", True) else "활성화"
                if st.button("⚡", key=f"toggle_{user['user_id']}", help=action_text):
                    if toggle_user_status(user['user_id']):
                        st.success(f"✅ {user['nickname']}님이 {action_text}되었습니다.")
                        st.rerun()
            
            with col_delete:
                if st.button("🗑️", key=f"delete_{user['user_id']}", help="회원 삭제"):
                    st.session_state[f"confirm_delete_{user['user_id']}"] = True
                    st.rerun()
        
        # 정보 수정 폼
        if st.session_state.get(f"editing_{user['user_id']}", False):
            show_edit_user_form(user)
        
        # 삭제 확인
        if st.session_state.get(f"confirm_delete_{user['user_id']}", False):
            show_delete_confirmation(user)
        
        st.markdown("---")

def show_edit_user_form(user):
    """회원 정보 수정 폼"""
    
    with st.expander(f"✏️ {user['nickname']} 정보 수정", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            new_nickname = st.text_input(
                "닉네임", 
                value=user['nickname'],
                key=f"new_nickname_{user['user_id']}"
            )
        
        with col2:
            new_department = st.selectbox(
                "소속부서",
                AUTH_CONFIG["departments"],
                index=AUTH_CONFIG["departments"].index(user['department']) if user['department'] in AUTH_CONFIG["departments"] else 0,
                key=f"new_department_{user['user_id']}"
            )
        
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            if st.button("💾 저장", key=f"save_{user['user_id']}", type="primary"):
                success, message = update_user_info(user['user_id'], new_nickname, new_department)
                if success:
                    st.success(f"✅ {message}")
                    del st.session_state[f"editing_{user['user_id']}"]
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        with col_cancel:
            if st.button("❌ 취소", key=f"cancel_{user['user_id']}"):
                del st.session_state[f"editing_{user['user_id']}"]
                st.rerun()

def show_delete_confirmation(user):
    """회원 삭제 확인"""
    
    with st.expander(f"🗑️ {user['nickname']} 삭제 확인", expanded=True):
        st.warning(f"⚠️ **{user['nickname']}**님의 계정을 삭제하시겠습니까?")
        st.markdown("- 모든 질문, 답변 기록이 그대로 유지됩니다")
        st.markdown("- 삭제된 계정은 복구할 수 없습니다")
        st.markdown("- 해당 녹스아이디로 다시 등록할 수 있습니다")
        
        col_delete, col_cancel = st.columns(2)
        
        with col_delete:
            if st.button("🗑️ 삭제", key=f"confirm_delete_yes_{user['user_id']}", type="primary"):
                if delete_user(user['user_id']):
                    st.success(f"✅ {user['nickname']}님의 계정이 삭제되었습니다.")
                    del st.session_state[f"confirm_delete_{user['user_id']}"]
                    st.rerun()
                else:
                    st.error("❌ 삭제에 실패했습니다.")
        
        with col_cancel:
            if st.button("❌ 취소", key=f"confirm_delete_no_{user['user_id']}"):
                del st.session_state[f"confirm_delete_{user['user_id']}"]
                st.rerun()

def download_user_list():
    """회원 목록 Excel 다운로드"""
    users = get_all_users()
    
    if not users:
        st.warning("다운로드할 회원 정보가 없습니다.")
        return
    
    # DataFrame 생성
    df_data = []
    for user in users:
        df_data.append({
            "녹스아이디": user["knox_id"],
            "닉네임": user["nickname"], 
            "소속부서": user["department"],
            "등록일": user["created_at"].split()[0],
            "마지막 로그인": user.get("last_login", "접속 기록 없음").split()[0] if user.get("last_login") else "접속 기록 없음",
            "활성 상태": "활성" if user.get("is_active", True) else "비활성"
        })
    
    df = pd.DataFrame(df_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ae_wiki_users_{timestamp}.xlsx"
    
    df.to_excel(filename, index=False)
    st.success(f"📥 {filename} 파일이 다운로드되었습니다.")

def show_log_management(data):
    """로그 관리"""
    st.markdown("### 📋 로그 관리")
    
    # 로그 타입 선택
    log_type = st.selectbox(
        "로그 타입 선택",
        ["검색 로그", "챗봇 대화 로그", "사용자 활동 로그"]
    )
    
    if log_type == "검색 로그":
        show_search_logs(data)
    elif log_type == "챗봇 대화 로그":
        show_chatbot_logs(data)
    elif log_type == "사용자 활동 로그":
        show_user_activity_logs(data)

def show_search_logs(data):
    """검색 로그 표시"""
    st.markdown("#### 🔍 검색 로그")
    
    search_logs = data.get("search_logs", [])
    
    if not search_logs:
        st.info("검색 로그가 없습니다.")
        return
    
    # 검색 로그 필터
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_filter = st.date_input("날짜 필터", value=datetime.now().date())
    
    with col2:
        keyword_filter = st.text_input("키워드 필터", placeholder="검색어 입력")
    
    with col3:
        if st.button("📥 Excel 다운로드"):
            download_search_logs_excel(search_logs)
    
    # 필터링된 로그 표시
    filtered_logs = filter_search_logs(search_logs, date_filter, keyword_filter)
    
    if filtered_logs:
        df = pd.DataFrame(filtered_logs)
        st.dataframe(df, use_container_width=True)
        
        st.markdown(f"**총 {len(filtered_logs)}개의 검색 로그**")
    else:
        st.warning("필터 조건에 맞는 로그가 없습니다.")

def show_chatbot_logs(data):
    """챗봇 대화 로그 표시"""
    st.markdown("#### 🤖 챗봇 대화 로그")
    
    chat_history = data.get("chat_history", [])
    
    if not chat_history:
        st.info("챗봇 대화 기록이 없습니다.")
        return
    
    # 챗봇별 대화 분류 (새로운 3-챗봇 시스템)
    ae_wiki_chats = [chat for chat in chat_history if chat.get("chatbot_type") == "ae_wiki"]
    glossary_chats = data.get("glossary_chat_history", [])
    jedec_chats = data.get("jedec_chat_history", [])
    
    # 레거시 데이터 호환성: chatbot_type이 없는 구 데이터는 AE WIKI로 추정
    legacy_chats = [chat for chat in chat_history if not chat.get("chatbot_type") and not chat.get("is_admin_bot", False)]
    all_chats = ae_wiki_chats + legacy_chats + glossary_chats + jedec_chats
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**총 {len(all_chats)}개의 챗봇 대화**")
        st.caption(f"AE WIKI: {len(ae_wiki_chats + legacy_chats)}개 | 용어집: {len(glossary_chats)}개 | JEDEC: {len(jedec_chats)}개")
    
    with col2:
        if st.button("📥 대화 로그 다운로드"):
            download_chat_logs_excel(all_chats, "전체_챗봇")
    
    # 최근 대화 표시
    recent_chats = sorted(all_chats, key=lambda x: x["timestamp"], reverse=True)[:20]
    
    for i, chat in enumerate(recent_chats, 1):
        chatbot_type = chat.get('chatbot_type', 'AE WIKI (레거시)')
        chatbot_emoji = {'ae_wiki': '🧠', 'glossary': '🔍', 'jedec': '🤖'}.get(chatbot_type, '🧠')
        with st.expander(f"{i}. {chat['timestamp']} - {chat.get('user_id', 'Unknown')} [{chatbot_emoji} {chatbot_type.upper()}]"):
            st.markdown(f"**👤 사용자:** {chat['user_message']}")
            st.markdown(f"**{chatbot_emoji} AI:** {chat['bot_response']}")

# REMOVED: show_admin_chatbot_logs - 행정 챗봇 완전 제거

def show_user_activity_logs(data):
    """사용자 활동 로그 표시"""
    st.markdown("#### 👥 사용자 활동 로그")
    
    # 질문/답변 활동 통합
    activities = []
    
    # 질문 활동
    for q in data["questions"]:
        activities.append({
            "timestamp": q["timestamp"],
            "user": q["author"],
            "activity": "질문 등록",
            "content": q["title"],
            "category": q["category"]
        })
    
    # 답변 활동  
    for a in data["answers"]:
        question = next((q for q in data["questions"] if q["id"] == a["question_id"]), None)
        q_title = question["title"] if question else "삭제된 질문"
        activities.append({
            "timestamp": a["timestamp"],
            "user": a["author"],
            "activity": "답변 등록",
            "content": f"{q_title}에 답변",
            "category": question["category"] if question else "Unknown"
        })
    
    # 시간순 정렬
    activities = sorted(activities, key=lambda x: x["timestamp"], reverse=True)
    
    if activities:
        # 최근 50개 활동만 표시
        recent_activities = activities[:50]
        df = pd.DataFrame(recent_activities)
        st.dataframe(df, use_container_width=True)
        
        st.markdown(f"**총 {len(activities)}개의 사용자 활동 (최근 50개 표시)**")
        
        if st.button("📥 전체 활동 로그 다운로드"):
            download_activity_logs_excel(activities)
    else:
        st.info("사용자 활동 기록이 없습니다.")

def show_chat_history(data):
    """대화 기록 관리"""
    st.markdown("### 💬 대화 기록 관리")
    
    chat_history = data.get("chat_history", [])
    
    if not chat_history:
        st.info("대화 기록이 없습니다.")
        return
    
    # 새로운 3-챗봇 시스템 대화 타입별 분류
    ae_wiki_chats = [chat for chat in chat_history if chat.get("chatbot_type") == "ae_wiki"]
    glossary_chats = data.get("glossary_chat_history", [])
    jedec_chats = data.get("jedec_chat_history", [])
    legacy_chats = [chat for chat in chat_history if not chat.get("chatbot_type") and not chat.get("is_admin_bot", False)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🧠 AE WIKI", len(ae_wiki_chats + legacy_chats))
        st.metric("🔍 용어집", len(glossary_chats))
    
    with col2:
        st.metric("🤖 JEDEC", len(jedec_chats))
        st.metric("📊 전체", len(chat_history) + len(glossary_chats) + len(jedec_chats))
    
    # 대화 기록 정리 옵션
    st.markdown("---")
    st.markdown("#### 🧹 데이터 정리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days_old = st.number_input("며칠 이전 대화 삭제", min_value=1, value=30)
        if st.button("🗑️ 오래된 대화 삭제", type="secondary"):
            deleted_count = cleanup_old_chats(data, days_old)
            if deleted_count > 0:
                st.success(f"✅ {deleted_count}개의 오래된 대화를 삭제했습니다.")
                st.rerun()
            else:
                st.info("삭제할 오래된 대화가 없습니다.")
    
    with col2:
        st.markdown("**⚠️ 주의사항**")
        st.markdown("- 삭제된 대화는 복구할 수 없습니다")
        st.markdown("- 정기적인 백업을 권장합니다")

def show_statistics(data):
    """통계 분석"""
    st.markdown("### 📈 통계 분석")
    
    # 카테고리별 질문 분포
    st.markdown("#### 📊 카테고리별 질문 분포")
    
    if data["questions"]:
        category_counts = {}
        for q in data["questions"]:
            category = q["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
        
        df_categories = pd.DataFrame(list(category_counts.items()), 
                                   columns=["카테고리", "질문 수"])
        st.bar_chart(df_categories.set_index("카테고리"))
        
        # 상위 카테고리
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        st.markdown("**상위 5개 카테고리:**")
        for category, count in top_categories:
            st.markdown(f"- **{category}**: {count}개")
    
    st.markdown("---")
    
    # 일별 활동 통계
    st.markdown("#### 📅 일별 활동 통계")
    
    daily_stats = calculate_daily_stats(data)
    
    if daily_stats:
        df_daily = pd.DataFrame(daily_stats)
        st.line_chart(df_daily.set_index("날짜"))

def show_system_settings(data):
    """시스템 설정"""
    st.markdown("### ⚙️ 시스템 설정")
    
    # 데이터 백업
    st.markdown("#### 💾 데이터 백업")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 데이터 백업 다운로드", type="primary"):
            backup_data(data)
    
    with col2:
        st.markdown("**백업 정보**")
        st.markdown(f"- 질문: {len(data['questions'])}개")
        st.markdown(f"- 답변: {len(data['answers'])}개")
        st.markdown(f"- 대화: {len(data.get('chat_history', []))}개")
    
    st.markdown("---")
    
    # 시스템 정보
    st.markdown("#### 💻 시스템 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**애플리케이션 정보**")
        st.markdown(f"- 버전: AE WIKI v1.0")
        st.markdown(f"- 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d')}")
        st.markdown(f"- 관리자: {get_username()}")
    
    with col2:
        st.markdown("**데이터 현황**")
        data_size = estimate_data_size(data)
        st.markdown(f"- 데이터 크기: ~{data_size} KB")
        st.markdown(f"- 총 사용자: {count_unique_users(data)}명")

# ====================================
# 🛠️ 유틸리티 함수들
# ====================================

def get_today_count(items):
    """오늘 등록된 항목 수"""
    today = datetime.now().date()
    count = 0
    for item in items:
        try:
            item_date = datetime.strptime(item["timestamp"].split()[0], "%Y-%m-%d").date()
            if item_date == today:
                count += 1
        except:
            continue
    return count

def get_today_chat_count(data):
    """오늘의 챗봇 대화 수"""
    today = datetime.now().date()
    count = 0
    for chat in data.get("chat_history", []):
        try:
            chat_date = datetime.strptime(chat["timestamp"].split()[0], "%Y-%m-%d").date()
            if chat_date == today:
                count += 1
        except:
            continue
    return count

def get_today_search_count(data):
    """오늘의 검색 수"""
    today = datetime.now().date()
    count = 0
    for search in data.get("search_logs", []):
        try:
            search_date = datetime.strptime(search["timestamp"].split()[0], "%Y-%m-%d").date()
            if search_date == today:
                count += 1
        except:
            continue
    return count

def filter_search_logs(logs, date_filter, keyword_filter):
    """검색 로그 필터링"""
    filtered = []
    for log in logs:
        # 날짜 필터
        try:
            log_date = datetime.strptime(log["timestamp"].split()[0], "%Y-%m-%d").date()
            if log_date != date_filter:
                continue
        except:
            continue
        
        # 키워드 필터
        if keyword_filter and keyword_filter.lower() not in log.get("query", "").lower():
            continue
            
        filtered.append(log)
    
    return filtered

def download_search_logs_excel(logs):
    """검색 로그 Excel 다운로드 (브라우저에서 바로)"""
    df = pd.DataFrame(logs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_logs_{timestamp}.xlsx"
    
    # 엑셀을 메모리에 쓰기
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="SearchLogs")
        buffer.seek(0)
    
    # 브라우저 다운로드
    st.download_button(
        label="📥 검색 로그 다운로드",
        data=buffer,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def download_chat_logs_excel(chats, chat_type):
    """챗봇 로그 Excel 다운로드 (브라우저에서 바로)"""
    df = pd.DataFrame(chats)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{chat_type}_logs_{timestamp}.xlsx"
    
    # 엑셀을 메모리에 쓰기
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="ChatLogs")
        buffer.seek(0)
    
    # 브라우저 다운로드
    st.download_button(
        label="📥 대화 로그 다운로드",
        data=buffer,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def download_activity_logs_excel(activities):
    """활동 로그 Excel 다운로드 (브라우저에서 바로)"""
    df = pd.DataFrame(activities)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"activity_logs_{timestamp}.xlsx"
    
    # 엑셀을 메모리에 쓰기
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="ActivityLogs")
        buffer.seek(0)
    
    # 브라우저 다운로드
    st.download_button(
        label="📥 활동 로그 다운로드",
        data=buffer,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def cleanup_old_chats(data, days_old):
    """오래된 대화 삭제"""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    original_count = len(data.get("chat_history", []))
    
    # 필터링: 최근 대화만 유지
    recent_chats = []
    for chat in data.get("chat_history", []):
        try:
            chat_date = datetime.strptime(chat["timestamp"], "%Y-%m-%d %H:%M:%S")
            if chat_date >= cutoff_date:
                recent_chats.append(chat)
        except:
            # 날짜 파싱 실패시 유지
            recent_chats.append(chat)
    
    data["chat_history"] = recent_chats
    
    # 데이터 저장
    save_data(data)
    
    return original_count - len(recent_chats)

def show_conversation_memory_manager():
    """대화 메모리 관리 위젯"""
    try:
        from conversation_manager import show_conversation_manager_widget
        show_conversation_manager_widget()
    except ImportError:
        st.error("🚨 대화 메모리 관리자가 설치되지 않았습니다.")
        st.info("conversation_manager.py 파일이 필요합니다.")
    except Exception as e:
        st.error(f"🚨 대화 메모리 관리자 오류: {str(e)}")
        st.info("관리자에게 문의하세요.")

def calculate_daily_stats(data):
    """일별 활동 통계 계산"""
    daily_stats = {}
    
    # 질문 통계
    for q in data["questions"]:
        try:
            date = datetime.strptime(q["timestamp"].split()[0], "%Y-%m-%d").date()
            if date not in daily_stats:
                daily_stats[date] = {"날짜": date, "질문": 0, "답변": 0}
            daily_stats[date]["질문"] += 1
        except:
            continue
    
    # 답변 통계
    for a in data["answers"]:
        try:
            date = datetime.strptime(a["timestamp"].split()[0], "%Y-%m-%d").date()
            if date not in daily_stats:
                daily_stats[date] = {"날짜": date, "질문": 0, "답변": 0}
            daily_stats[date]["답변"] += 1
        except:
            continue
    
    # 최근 30일만
    recent_dates = sorted(daily_stats.keys(), reverse=True)[:30]
    return [daily_stats[date] for date in reversed(recent_dates)]

def backup_data(data):
    """데이터 백업"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ae_wiki_backup_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    st.success(f"📥 {filename} 백업 파일이 생성되었습니다.")

def estimate_data_size(data):
    """데이터 크기 추정"""
    data_str = json.dumps(data, ensure_ascii=False)
    return round(len(data_str.encode('utf-8')) / 1024, 2)

def count_unique_users(data):
    """고유 사용자 수 계산"""
    users = set()
    
    for q in data["questions"]:
        users.add(q["author"])
    
    for a in data["answers"]:
        users.add(a["author"])
    
    return len(users)

def save_data(data):
    """데이터 저장"""
    try:
        with open(DATA_CONFIG["data_file"], 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"데이터 저장 실패: {str(e)}")
        return False

def show_voc_management():
    """VOC 관리 탭"""
    st.markdown("### 📝 VOC (고객의 소리) 관리")
    
    try:
        from config import DATA_CONFIG
        voc_file = DATA_CONFIG["voc_file"]
        if os.path.exists(voc_file):
            with open(voc_file, 'r', encoding='utf-8') as f:
                all_voc = json.load(f)
        else:
            all_voc = []
        
        if all_voc:
            # 통계 정보
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("전체 VOC", f"{len(all_voc)}건")
            
            with col2:
                recent_count = len([v for v in all_voc if 
                                 (datetime.now() - datetime.strptime(v['timestamp'], '%Y-%m-%d %H:%M:%S')).days <= 7])
                st.metric("최근 7일", f"{recent_count}건")
            
            with col3:
                completed_count = len([v for v in all_voc if v.get('status') == '완료'])
                st.metric("처리 완료", f"{completed_count}건")
            
            with col4:
                if len(all_voc) > 0:
                    completion_rate = round((completed_count / len(all_voc)) * 100, 1)
                    st.metric("처리율", f"{completion_rate}%")
            
            st.markdown("---")
            
            # VOC 목록 표시
            st.markdown("#### 📋 VOC 목록")
            
            # 정렬 및 필터링 옵션
            col1, col2 = st.columns(2)
            with col1:
                sort_option = st.selectbox("정렬 기준", ["최신순", "오래된순"])
            with col2:
                status_filter = st.selectbox("상태 필터", ["전체", "접수", "검토중", "진행중", "완료"])
            
            # VOC 필터링 및 정렬
            filtered_voc = all_voc
            if status_filter != "전체":
                filtered_voc = [v for v in filtered_voc if v.get('status', '접수') == status_filter]
            
            if sort_option == "최신순":
                filtered_voc = sorted(filtered_voc, key=lambda x: x['timestamp'], reverse=True)
            elif sort_option == "오래된순":
                filtered_voc = sorted(filtered_voc, key=lambda x: x['timestamp'])
            
            # VOC 목록 표시
            for i, voc in enumerate(filtered_voc):
                with st.expander(f"[{voc['category']}] {voc['title']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**제출일**: {voc['timestamp']}")
                        st.markdown(f"**제출자**: {'익명' if voc.get('anonymous', False) else voc.get('nickname', '알 수 없음')}")
                        st.markdown(f"**연락처**: {voc.get('contact', '없음')}")
                        st.markdown(f"**내용**:")
                        st.text_area("", value=voc['content'], height=100, disabled=True, key=f"voc_content_{i}")
                    
                    with col2:
                        current_status = voc.get('status', '접수')
                        new_status = st.selectbox(
                            "상태 변경",
                            ["접수", "검토중", "진행중", "완료"],
                            index=["접수", "검토중", "진행중", "완료"].index(current_status),
                            key=f"voc_status_{i}"
                        )
                        
                        if st.button("상태 업데이트", key=f"voc_update_{i}"):
                            voc['status'] = new_status
                            voc['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # 파일에 저장
                            with open(voc_file, 'w', encoding='utf-8') as f:
                                json.dump(all_voc, f, ensure_ascii=False, indent=2)
                            
                            st.success(f"상태가 '{new_status}'로 업데이트되었습니다!")
                            st.rerun()
        else:
            st.info("📝 아직 제출된 VOC가 없습니다.")
            
    except Exception as e:
        st.error(f"VOC 데이터 로드 중 오류: {e}")

def show_wiki_learning_management():
    """WIKI 학습 관리 탭"""
    st.markdown("### 📚 WIKI 학습 요청 관리")
    
    try:
        from config import DATA_CONFIG
        learning_file = DATA_CONFIG["learning_requests_file"]
        if os.path.exists(learning_file):
            with open(learning_file, 'r', encoding='utf-8') as f:
                all_requests = json.load(f)
        else:
            all_requests = []
        
        if all_requests:
            # 통계 정보
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("전체 요청", f"{len(all_requests)}건")
            
            with col2:
                pending_count = len([r for r in all_requests if r.get('status', '대기중') == '대기중'])
                st.metric("대기중", f"{pending_count}건")
            
            with col3:
                processing_count = len([r for r in all_requests if r.get('status', '대기중') == '처리중'])
                st.metric("처리중", f"{processing_count}건")
            
            with col4:
                completed_count = len([r for r in all_requests if r.get('status', '대기중') == '완료'])
                st.metric("완료", f"{completed_count}건")
            
            st.markdown("---")
            
            # 학습 요청 목록 표시
            st.markdown("#### 📋 학습 요청 목록")
            
            # 정렬 및 필터링 옵션
            col1, col2 = st.columns(2)
            with col1:
                sort_option = st.selectbox("정렬 기준", ["최신순", "오래된순"], key="learning_sort")
            with col2:
                status_filter = st.selectbox("상태 필터", ["전체", "대기중", "검토중", "처리중", "완료", "거부"], key="learning_status")
            
            # 요청 필터링 및 정렬
            filtered_requests = all_requests
            if status_filter != "전체":
                filtered_requests = [r for r in filtered_requests if r.get('status', '대기중') == status_filter]
            
            if sort_option == "최신순":
                filtered_requests = sorted(filtered_requests, key=lambda x: x['timestamp'], reverse=True)
            elif sort_option == "오래된순":
                filtered_requests = sorted(filtered_requests, key=lambda x: x['timestamp'])
            
            # 요청 목록 표시
            for i, req in enumerate(filtered_requests):
                # 요청 타입 표시 (자료링크 vs 용어학습)
                request_type = req.get('request_type', '자료링크')
                type_emoji = "🔗" if request_type == "자료링크" else "📝"
                
                title_display = req.get('title', req.get('term_name', '제목 없음'))
                with st.expander(f"{type_emoji} [{req['category']}] {title_display}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**요청 유형**: {request_type}")
                        st.markdown(f"**제출일**: {req['timestamp']}")
                        st.markdown(f"**제출자**: {req.get('nickname', '알 수 없음')}")
                        
                        if request_type == "자료링크":
                            # 자료 링크 학습 요청
                            st.markdown(f"**URL 링크**: {req.get('url_link', req.get('edm_link', ''))}")
                            st.markdown(f"**적용 대상**: {', '.join(req.get('target_bots', []))}")
                            st.markdown(f"**설명**:")
                            st.text_area("", value=req.get('description', ''), height=80, disabled=True, key=f"req_desc_{i}")
                        else:
                            # 용어 학습 요청
                            st.markdown(f"**용어명**: {req.get('term_name', '')}")
                            st.markdown(f"**용어 정의**:")
                            st.text_area("", value=req.get('term_definition', ''), height=120, disabled=True, key=f"req_term_def_{i}")
                            if req.get('related_keywords'):
                                st.markdown(f"**관련 키워드**: {req['related_keywords']}")
                            if req.get('reference_source'):
                                st.markdown(f"**참고 자료**: {req['reference_source']}")
                        
                        if req.get('additional_notes'):
                            st.markdown(f"**추가 요청사항**: {req['additional_notes']}")
                    
                    with col2:
                        current_status = req.get('status', '대기중')
                        new_status = st.selectbox(
                            "상태 변경",
                            ["대기중", "검토중", "처리중", "완료", "거부"],
                            index=["대기중", "검토중", "처리중", "완료", "거부"].index(current_status),
                            key=f"req_status_{i}"
                        )
                        
                        # 관리자 메모 추가
                        admin_memo = st.text_area(
                            "관리자 메모",
                            value=req.get('admin_memo', ''),
                            height=60,
                            key=f"req_memo_{i}"
                        )
                        
                        if st.button("상태 업데이트", key=f"req_update_{i}"):
                            req['status'] = new_status
                            req['admin_memo'] = admin_memo
                            req['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # 파일에 저장
                            with open(learning_file, 'w', encoding='utf-8') as f:
                                json.dump(all_requests, f, ensure_ascii=False, indent=2)
                            
                            st.success(f"상태가 '{new_status}'로 업데이트되었습니다!")
                            st.rerun()
        else:
            st.info("📚 아직 제출된 학습 요청이 없습니다.")
            
    except Exception as e:
        st.error(f"학습 요청 데이터 로드 중 오류: {e}")

def show_registration_approval(data):
    """회원가입 승인 관리"""
    st.markdown("### ✅ 회원가입 승인 관리")
    
    try:
        # 새 통합 시스템에서 승인 대기 중인 신청 목록 가져오기
        from user_manager import get_pending_requests
        pending_requests = get_pending_requests()
        
        if pending_requests:
            st.info(f"📋 승인 대기 중인 회원가입 신청: **{len(pending_requests)}**건")
            
            for req in pending_requests:
                with st.expander(f"🆕 {req['name']} ({req['knox_id']}) - {req['department']}", expanded=True):
                    # 신청자 정보 표시
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📋 신청자 정보**")
                        st.markdown(f"**녹스아이디**: {req['knox_id']}")
                        st.markdown(f"**실명**: {req['name']}")
                        st.markdown(f"**소속부서**: {req['department']}")
                        st.markdown(f"**신청일시**: {req['requested_at'][:19].replace('T', ' ')}")
                    
                    with col2:
                        st.markdown("**⚙️ 관리자 액션**")
                        
                        # 승인 버튼
                        if st.button(
                            f"✅ {req['knox_id']} 승인", 
                            key=f"approve_{req['id']}", 
                            type="primary",
                            use_container_width=True
                        ):
                            admin_username = get_username() or "admin"  # 현재 관리자 ID
                            success, message = approve_new(req['id'], admin_username)
                            
                            if success:
                                st.success(f"🎉 {message}")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        
                        # 거절 버튼과 사유 입력
                        with st.form(f"reject_form_{req['id']}"):
                            rejection_reason = st.text_area(
                                "거절 사유 (선택사항)", 
                                placeholder="거절 사유를 입력하세요...",
                                key=f"reason_{req['id']}"
                            )
                            
                            if st.form_submit_button(
                                f"❌ {req['knox_id']} 거절", 
                                type="secondary",
                                use_container_width=True
                            ):
                                admin_username = get_username() or "admin"  # 현재 관리자 ID
                                success, message = reject_new(
                                    req['id'], admin_username, rejection_reason
                                )
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    if rejection_reason:
                                        st.info(f"거절 사유: {rejection_reason}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                    
                    st.divider()
        else:
            st.success("✅ 현재 승인 대기 중인 회원가입 신청이 없습니다.")
        
        # 처리된 신청 기록 (최근 10개)
        st.markdown("### 📜 최근 처리 기록")
        
        from user_manager import get_processed_requests
        processed_requests = get_processed_requests()
        
        if processed_requests:
            recent_processed = processed_requests[:10]  # 최근 10개만 표시
            
            # 테이블로 표시
            table_data = []
            for req in recent_processed:
                status_emoji = "✅" if req["status"] == "approved" else "❌"
                table_data.append({
                    "상태": f"{status_emoji} {req['status'].upper()}",
                    "녹스아이디": req["knox_id"],
                    "실명": req["name"],
                    "부서": req["department"],
                    "신청일": req["requested_at"][:10],
                    "처리일": req.get("processed_at", "")[:10] if req.get("processed_at") else "-",
                    "처리자": req.get("processed_by", "Unknown")
                })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("📝 아직 처리된 회원가입 신청이 없습니다.")
            
    except Exception as e:
        st.error(f"회원가입 승인 데이터 로드 중 오류: {e}")

# ====================================
# 🎁 포인트 관리 시스템
# ====================================

def show_points_management(data):
    """포인트 관리 대시보드"""
    st.markdown("### 🎁 사용자 포인트 관리")

    # 포인트 전체 현황
    all_points = get_all_user_points(data)

    if not all_points:
        st.info("📊 아직 포인트 데이터가 없습니다.")
        return

    # 통계 정보
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 사용자", f"{len(all_points)}명")

    with col2:
        total_points = sum(all_points.values())
        st.metric("총 포인트", f"{total_points:,}점")

    with col3:
        avg_points = total_points / len(all_points) if all_points else 0
        st.metric("평균 포인트", f"{avg_points:.1f}점")

    with col4:
        max_points = max(all_points.values()) if all_points else 0
        st.metric("최고 포인트", f"{max_points:,}점")

    st.markdown("---")

    # 포인트 관리 탭
    point_tabs = st.tabs(["📊 포인트 현황", "⚡ 포인트 조정", "📜 변경 기록", "🔧 데이터 정리"])

    with point_tabs[0]:
        show_points_overview(data, all_points)

    with point_tabs[1]:
        show_points_adjustment(data)

    with point_tabs[2]:
        show_points_history(data)

    with point_tabs[3]:
        show_points_data_cleanup(data)

def show_points_overview(data, all_points):
    """포인트 현황 탭"""
    st.markdown("#### 📊 사용자별 포인트 현황")

    # 포인트 순위표
    sorted_points = sorted(all_points.items(), key=lambda x: x[1], reverse=True)

    # 사용자 정보와 포인트 결합
    users_list = get_all_users()
    user_dict = {user.get("knox_id", user.get("user_id", "")): user for user in users_list}

    # 테이블 데이터 생성
    table_data = []
    for rank, (username, points) in enumerate(sorted_points, 1):
        user_info = user_dict.get(username, {})
        table_data.append({
            "순위": f"#{rank}",
            "사용자명": username,
            "닉네임": user_info.get("nickname", user_info.get("name", "-")),
            "부서": user_info.get("department", "-"),
            "포인트": f"{points:,}점",
            "포인트_값": points  # 정렬용
        })

    if table_data:
        # 포인트 차트
        st.markdown("##### 📈 포인트 분포")

        import pandas as pd
        df = pd.DataFrame(table_data)

        # 바 차트
        chart_data = df[["사용자명", "포인트_값"]].set_index("사용자명")
        st.bar_chart(chart_data["포인트_값"])

        # 데이터 테이블
        st.markdown("##### 📋 상세 현황")
        display_df = df.drop("포인트_값", axis=1)  # 정렬용 컬럼 제거
        st.dataframe(display_df, use_container_width=True)

        # 검색 기능
        st.markdown("##### 🔍 사용자 검색")
        search_user = st.selectbox(
            "조회할 사용자 선택:",
            ["전체"] + [user["사용자명"] for user in table_data],
            key="points_search_user"
        )

        if search_user != "전체":
            user_data = next((user for user in table_data if user["사용자명"] == search_user), None)
            if user_data:
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**{user_data['닉네임']}**님의 포인트: **{user_data['포인트']}**")
                with col2:
                    st.info(f"순위: **{user_data['순위']}** / 부서: **{user_data['부서']}**")

def show_points_adjustment(data):
    """포인트 조정 탭"""
    st.markdown("#### ⚡ 포인트 조정")

    # 사용자 선택
    users_list = get_all_users()
    if not users_list:
        st.warning("등록된 사용자가 없습니다.")
        return

    user_options = {
        f"{user.get('nickname', user.get('name', 'Unknown'))} ({user.get('knox_id', user.get('user_id', ''))})"
        : user.get('knox_id', user.get('user_id', ''))
        for user in users_list
    }

    selected_user_display = st.selectbox(
        "포인트를 조정할 사용자 선택:",
        list(user_options.keys()),
        key="points_adjust_user"
    )

    if selected_user_display:
        selected_username = user_options[selected_user_display]
        current_points = get_all_user_points(data).get(selected_username, 0)

        st.info(f"**{selected_user_display}**의 현재 포인트: **{current_points:,}점**")

        # 조정 방식 선택
        adjustment_type = st.radio(
            "조정 방식:",
            ["포인트 증감", "포인트 설정"],
            key="adjustment_type"
        )

        col1, col2 = st.columns(2)

        with col1:
            if adjustment_type == "포인트 증감":
                point_change = st.number_input(
                    "변경할 포인트 (음수는 차감):",
                    value=0,
                    step=10,
                    key="point_change"
                )
                new_points = max(0, current_points + point_change)
                st.write(f"변경 후 예상 포인트: **{new_points:,}점**")
            else:
                new_points = st.number_input(
                    "설정할 포인트:",
                    value=current_points,
                    min_value=0,
                    step=10,
                    key="new_points"
                )
                point_change = new_points - current_points

        with col2:
            reason = st.text_area(
                "조정 사유:",
                placeholder="포인트 조정 사유를 입력하세요...",
                key="adjustment_reason"
            )

        # 조정 실행
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("✅ 포인트 조정 실행", key="execute_adjustment"):
                if not reason.strip():
                    st.warning("조정 사유를 입력해주세요.")
                else:
                    admin_user = get_username()

                    if adjustment_type == "포인트 증감":
                        success = adjust_user_points(data, selected_username, point_change, reason, admin_user)
                    else:
                        success = set_user_points(data, selected_username, new_points, admin_user)

                    if success:
                        st.success(f"✅ 포인트 조정 완료! {current_points:,} → {new_points:,}점")
                        st.rerun()
                    else:
                        st.error("❌ 포인트 조정에 실패했습니다.")

        with col2:
            if st.button("🔄 페이지 새로고침", key="refresh_points"):
                st.rerun()

def show_points_history(data):
    """포인트 변경 기록 탭"""
    st.markdown("#### 📜 포인트 변경 기록")

    # 필터 옵션
    col1, col2 = st.columns(2)

    with col1:
        # 사용자 필터
        users_list = get_all_users()
        user_options = ["전체"] + [
            user.get('knox_id', user.get('user_id', ''))
            for user in users_list
        ]
        selected_user = st.selectbox("사용자 필터:", user_options, key="history_user_filter")

    with col2:
        # 표시 개수
        limit = st.selectbox("표시 개수:", [20, 50, 100], key="history_limit")

    # 기록 조회
    username_filter = None if selected_user == "전체" else selected_user
    history = get_point_change_history(data, username_filter, limit)

    if history:
        # 테이블 데이터 생성
        table_data = []
        for record in history:
            table_data.append({
                "시간": record.get("timestamp", "")[:19].replace("T", " "),
                "사용자": record.get("username", ""),
                "이전": f"{record.get('old_points', 0):,}점",
                "이후": f"{record.get('new_points', 0):,}점",
                "변경": f"{record.get('point_change', 0):+,}점" if 'point_change' in record else f"{record.get('new_points', 0) - record.get('old_points', 0):+,}점",
                "사유": record.get("reason", "수동 조정"),
                "관리자": record.get("admin_user", "시스템")
            })

        import pandas as pd
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

        # 통계 정보
        st.markdown("##### 📊 변경 통계")
        col1, col2, col3 = st.columns(3)

        with col1:
            total_changes = len(history)
            st.metric("총 변경 횟수", f"{total_changes}회")

        with col2:
            unique_users = len(set(record.get("username", "") for record in history))
            st.metric("관련 사용자", f"{unique_users}명")

        with col3:
            recent_changes = len([h for h in history if h.get("timestamp", "").startswith(datetime.now().strftime("%Y-%m-%d"))])
            st.metric("오늘 변경", f"{recent_changes}회")

    else:
        st.info("📜 포인트 변경 기록이 없습니다.")

def show_points_data_cleanup(data):
    """포인트 데이터 정리 탭"""
    st.markdown("#### 🔧 포인트 데이터 정리")

    # 중복 데이터 검사
    all_points = get_all_user_points(data)
    users_list = get_all_users()
    user_dict = {user.get("knox_id", user.get("user_id", "")): user for user in users_list}

    # 중복 가능성 분석
    duplicates_found = []
    checked_names = set()

    for username in all_points.keys():
        # nox_id가 아닌 경우 (레거시 이름 기반)
        if username not in [user.get("knox_id", "") for user in users_list]:
            # 실제 사용자 이름과 매칭되는지 확인
            matching_user = None
            for user in users_list:
                if user.get("name", "") == username or user.get("nickname", "") == username:
                    matching_user = user
                    break

            if matching_user and matching_user.get("knox_id") in all_points:
                legacy_points = all_points.get(username, 0)
                current_points = all_points.get(matching_user.get("knox_id"), 0)

                duplicates_found.append({
                    "legacy_key": username,
                    "legacy_points": legacy_points,
                    "current_key": matching_user.get("knox_id"),
                    "current_points": current_points,
                    "user_info": matching_user
                })

    if duplicates_found:
        st.warning(f"⚠️ {len(duplicates_found)}개의 중복 포인트 데이터가 발견되었습니다.")

        # 중복 데이터 상세 표시
        st.markdown("##### 📋 중복 데이터 목록")

        for i, dup in enumerate(duplicates_found):
            with st.expander(f"중복 #{i+1}: {dup['user_info'].get('name', 'Unknown')}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**🗂️ 레거시 데이터**")
                    st.write(f"키: `{dup['legacy_key']}`")
                    st.write(f"포인트: **{dup['legacy_points']:,}점**")

                with col2:
                    st.markdown("**🆕 현재 데이터**")
                    st.write(f"키: `{dup['current_key']}`")
                    st.write(f"포인트: **{dup['current_points']:,}점**")

                st.markdown("**👤 사용자 정보**")
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"이름: {dup['user_info'].get('name', '-')}")
                    st.write(f"ID: {dup['user_info'].get('knox_id', '-')}")
                with col_info2:
                    st.write(f"닉네임: {dup['user_info'].get('nickname', '-')}")
                    st.write(f"부서: {dup['user_info'].get('department', '-')}")

        st.markdown("---")

        # 정리 옵션
        st.markdown("##### 🛠️ 데이터 정리 옵션")

        cleanup_option = st.radio(
            "정리 방법을 선택하세요:",
            [
                "현재 데이터 유지 (레거시 데이터 삭제)",
                "더 높은 포인트 값 유지",
                "포인트 합산 후 현재 키로 통합"
            ],
            help="데이터 정리 방식을 선택하면 중복을 해결할 수 있습니다."
        )

        # 미리보기
        st.markdown("##### 👀 정리 결과 미리보기")
        preview_data = {}

        for dup in duplicates_found:
            if cleanup_option == "현재 데이터 유지 (레거시 데이터 삭제)":
                preview_data[dup['current_key']] = dup['current_points']
            elif cleanup_option == "더 높은 포인트 값 유지":
                max_points = max(dup['legacy_points'], dup['current_points'])
                preview_data[dup['current_key']] = max_points
            elif cleanup_option == "포인트 합산 후 현재 키로 통합":
                total_points = dup['legacy_points'] + dup['current_points']
                preview_data[dup['current_key']] = total_points

        preview_df = []
        for username, points in preview_data.items():
            user_info = user_dict.get(username, {})
            preview_df.append({
                "사용자명": username,
                "닉네임": user_info.get("nickname", user_info.get("name", "-")),
                "정리 후 포인트": f"{points:,}점"
            })

        if preview_df:
            import pandas as pd
            st.dataframe(pd.DataFrame(preview_df), use_container_width=True)

        # 정리 실행 버튼
        st.markdown("---")
        col1, col2 = st.columns([3, 1])

        with col1:
            st.warning("⚠️ **주의**: 데이터 정리는 되돌릴 수 없습니다. 신중하게 선택해주세요.")

        with col2:
            if st.button("🧹 데이터 정리 실행", type="primary"):
                try:
                    # 실제 정리 로직 실행
                    from utils import cleanup_duplicate_points_data

                    # 정리 방법에 따라 처리
                    if cleanup_option == "현재 데이터 유지 (레거시 데이터 삭제)":
                        method = "keep_current"
                    elif cleanup_option == "더 높은 포인트 값 유지":
                        method = "keep_higher"
                    elif cleanup_option == "포인트 합산 후 현재 키로 통합":
                        method = "sum_points"

                    success = cleanup_duplicate_points_data(data, method=method)

                    if success:
                        st.success("✅ 중복 데이터 정리가 완료되었습니다!")
                        st.info("🔄 페이지를 새로고침해주세요.")
                        st.balloons()
                    else:
                        st.error("❌ 데이터 정리 중 오류가 발생했습니다.")

                except Exception as e:
                    st.error(f"❌ 오류: {str(e)}")

    else:
        st.success("✅ 중복된 포인트 데이터가 없습니다.")
        st.info("모든 포인트 데이터가 올바르게 관리되고 있습니다.")

        # 현재 데이터 요약
        st.markdown("##### 📊 현재 포인트 데이터 현황")

        col1, col2, col3 = st.columns(3)

        with col1:
            total_users = len(all_points)
            st.metric("총 사용자 수", f"{total_users}명")

        with col2:
            total_points = sum(all_points.values())
            st.metric("총 포인트", f"{total_points:,}점")

        with col3:
            avg_points = total_points / total_users if total_users > 0 else 0
            st.metric("평균 포인트", f"{avg_points:.1f}점")

def show_index_management():
    """🚀 인덱스 관리 시스템"""
    st.markdown("### 🚀 인덱스 추가요청 관리")

    # 요청 데이터 로드
    try:
        from config import DATA_CONFIG
        learning_file = DATA_CONFIG["learning_requests_file"]

        if os.path.exists(learning_file):
            with open(learning_file, 'r', encoding='utf-8') as f:
                all_requests = json.load(f)
        else:
            all_requests = []

        # 인덱스 추가요청만 필터링
        index_requests = [req for req in all_requests if req.get("request_type") == "인덱스추가"]

    except Exception as e:
        st.error(f"요청 데이터 로드 실패: {e}")
        index_requests = []

    # 통계 정보
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_requests = len(index_requests)
        st.metric("총 요청 수", f"{total_requests}개")

    with col2:
        pending_requests = len([r for r in index_requests if r.get("status") == "대기중"])
        st.metric("대기중", f"{pending_requests}개")

    with col3:
        approved_requests = len([r for r in index_requests if r.get("status") == "승인"])
        st.metric("승인됨", f"{approved_requests}개")

    with col4:
        rejected_requests = len([r for r in index_requests if r.get("status") == "거부"])
        st.metric("거부됨", f"{rejected_requests}개")

    st.markdown("---")

    # 인덱스 관리 탭
    index_tabs = st.tabs(["📋 요청 목록", "✅ 요청 검토", "🎯 현재 인덱스", "⚙️ 인덱스 설정"])

    with index_tabs[0]:
        show_index_requests_list(index_requests)

    with index_tabs[1]:
        show_index_request_review(index_requests)

    with index_tabs[2]:
        show_current_indices()

    with index_tabs[3]:
        show_index_configuration()

def show_index_requests_list(index_requests):
    """인덱스 요청 목록"""
    st.markdown("#### 📋 인덱스 추가요청 목록")

    if not index_requests:
        st.info("📋 인덱스 추가요청이 없습니다.")
        return

    # 필터링 옵션
    col1, col2 = st.columns(2)

    with col1:
        status_filter = st.selectbox(
            "상태 필터",
            ["전체", "대기중", "승인", "거부"],
            key="index_status_filter"
        )

    with col2:
        category_filter = st.selectbox(
            "분야 필터",
            ["전체"] + list(set([req.get("category", "기타") for req in index_requests])),
            key="index_category_filter"
        )

    # 필터링 적용
    filtered_requests = index_requests
    if status_filter != "전체":
        filtered_requests = [r for r in filtered_requests if r.get("status") == status_filter]
    if category_filter != "전체":
        filtered_requests = [r for r in filtered_requests if r.get("category") == category_filter]

    # 요청 목록 표시
    for request in sorted(filtered_requests, key=lambda x: x.get("timestamp", ""), reverse=True):
        with st.expander(f"🚀 {request.get('display_name', 'Unknown')} ({request.get('status', 'Unknown')})"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📋 기본 정보**")
                st.write(f"**인덱스명**: {request.get('index_name', '-')}")
                st.write(f"**표시명**: {request.get('display_name', '-')}")
                st.write(f"**설명**: {request.get('description', '-')}")
                st.write(f"**분야**: {request.get('category', '-')}")
                st.write(f"**요청자**: {request.get('nickname', '-')}")
                st.write(f"**요청일**: {request.get('timestamp', '-')}")

            with col2:
                st.markdown("**🎨 UI 설정**")
                st.write(f"**아이콘**: {request.get('icon', '-')}")
                st.write(f"**색상**: {request.get('color', '-')}")
                st.write(f"**부제목**: {request.get('subtitle', '-')}")
                st.write(f"**RAG 인덱스**: {request.get('rag_index_name', '-')}")
                st.write(f"**출처 표시**: {request.get('source_display_type', '-')}")

            st.markdown("**🤖 시스템 프롬프트 요청**")
            st.write(request.get('system_prompt_description', '-'))

            st.markdown("**📚 데이터 소스**")
            st.write(request.get('data_sources', '-'))

            st.markdown("**🎯 사용 목적**")
            st.write(request.get('use_cases', '-'))

            if request.get('additional_notes'):
                st.markdown("**📝 추가 요청사항**")
                st.write(request.get('additional_notes', '-'))

def show_index_request_review(index_requests):
    """인덱스 요청 검토"""
    st.markdown("#### ✅ 인덱스 요청 검토 및 승인")

    pending_requests = [r for r in index_requests if r.get("status") == "대기중"]

    if not pending_requests:
        st.info("📋 검토 대기 중인 인덱스 요청이 없습니다.")
        return

    # 검토할 요청 선택
    request_options = [f"{req.get('display_name', 'Unknown')} ({req.get('timestamp', '')})"
                      for req in pending_requests]

    if request_options:
        selected_idx = st.selectbox(
            "검토할 요청 선택",
            range(len(request_options)),
            format_func=lambda x: request_options[x],
            key="review_request_select"
        )

        selected_request = pending_requests[selected_idx]

        # 요청 상세 정보 표시
        st.markdown("---")
        st.markdown("### 📋 요청 상세 정보")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**기본 정보**")
            st.write(f"인덱스명: `{selected_request.get('index_name')}`")
            st.write(f"표시명: {selected_request.get('display_name')}")
            st.write(f"설명: {selected_request.get('description')}")
            st.write(f"분야: {selected_request.get('category')}")

        with col2:
            st.markdown("**요청자 정보**")
            st.write(f"요청자: {selected_request.get('nickname')}")
            st.write(f"요청일: {selected_request.get('timestamp')}")
            st.write(f"아이콘: {selected_request.get('icon')}")
            st.write(f"색상: {selected_request.get('color')}")

        # 검토 액션
        st.markdown("---")
        st.markdown("### ⚙️ 검토 및 액션")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ 승인", type="primary", use_container_width=True):
                if update_index_request_status(selected_request["id"], "승인"):
                    st.success("✅ 요청이 승인되었습니다!")
                    # TODO: 실제 인덱스를 config.py에 추가하는 로직 구현
                    st.rerun()

        with col2:
            if st.button("❌ 거부", type="secondary", use_container_width=True):
                if update_index_request_status(selected_request["id"], "거부"):
                    st.success("❌ 요청이 거부되었습니다!")
                    st.rerun()

        with col3:
            if st.button("📝 메모 추가", use_container_width=True):
                st.session_state.show_admin_notes = True

        # 관리자 메모 입력
        if st.session_state.get("show_admin_notes", False):
            admin_notes = st.text_area(
                "관리자 메모",
                value=selected_request.get('admin_notes', ''),
                placeholder="검토 의견이나 추가 정보를 입력하세요..."
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("메모 저장"):
                    if update_index_request_notes(selected_request["id"], admin_notes):
                        st.success("메모가 저장되었습니다!")
                        st.session_state.show_admin_notes = False
                        st.rerun()

            with col2:
                if st.button("취소"):
                    st.session_state.show_admin_notes = False
                    st.rerun()

def show_current_indices():
    """현재 인덱스 현황"""
    st.markdown("#### 🎯 현재 활성 인덱스")

    from config import CHATBOT_INDICES, get_available_indices

    indices = get_available_indices()

    st.write(f"**총 {len(indices)}개의 인덱스가 활성화되어 있습니다.**")

    for index_id in indices:
        from config import get_index_config
        config = get_index_config(index_id)

        with st.expander(f"{config.get('display_name', index_id)} ({index_id})"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**설명**: {config.get('description', '-')}")
                st.write(f"**아이콘**: {config.get('icon', '-')}")
                st.write(f"**색상**: {config.get('color', '-')}")
                st.write(f"**RAG 인덱스**: {config.get('index_name', '-')}")

            with col2:
                st.write(f"**출처 표시**: {config.get('source_display', '-')}")
                st.write(f"**준비 상태**: {'준비중' if config.get('coming_soon', False) else '활성'}")
                gradient = config.get('gradient', '')
                if gradient:
                    st.markdown(f"**그라디언트**: `{gradient}`")

def show_index_configuration():
    """인덱스 설정 관리"""
    st.markdown("#### ⚙️ 인덱스 시스템 설정")

    st.info("🚧 고급 인덱스 설정 기능은 개발 중입니다.")

    # 향후 구현 예정 기능들
    st.markdown("""
    **📋 계획된 기능들:**
    - 인덱스 활성화/비활성화
    - 인덱스 순서 변경
    - 시스템 프롬프트 실시간 편집
    - RAG 인덱스 연결 관리
    - 인덱스 성능 모니터링
    """)

def update_index_request_status(request_id, new_status):
    """인덱스 요청 상태 업데이트"""
    try:
        from config import DATA_CONFIG
        learning_file = DATA_CONFIG["learning_requests_file"]

        # 데이터 로드
        with open(learning_file, 'r', encoding='utf-8') as f:
            all_requests = json.load(f)

        # 해당 요청 찾아서 상태 업데이트
        for request in all_requests:
            if request.get("id") == request_id:
                request["status"] = new_status
                request["admin_action_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break

        # 파일에 저장
        with open(learning_file, 'w', encoding='utf-8') as f:
            json.dump(all_requests, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        st.error(f"상태 업데이트 실패: {e}")
        return False

def update_index_request_notes(request_id, admin_notes):
    """인덱스 요청 관리자 메모 업데이트"""
    try:
        from config import DATA_CONFIG
        learning_file = DATA_CONFIG["learning_requests_file"]

        # 데이터 로드
        with open(learning_file, 'r', encoding='utf-8') as f:
            all_requests = json.load(f)

        # 해당 요청 찾아서 메모 업데이트
        for request in all_requests:
            if request.get("id") == request_id:
                request["admin_notes"] = admin_notes
                request["admin_notes_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break

        # 파일에 저장
        with open(learning_file, 'w', encoding='utf-8') as f:
            json.dump(all_requests, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        st.error(f"메모 업데이트 실패: {e}")
        return False

# ====================================
# 🚀 앱 실행
# ====================================

if __name__ == "__main__":
    main()