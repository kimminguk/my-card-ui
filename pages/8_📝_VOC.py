"""
AE WIKI - VOC (고객의 소리) 페이지
사용자들의 개선 제안과 의견을 수집하는 페이지
"""

import streamlit as st
import json
import os
import time
from datetime import datetime

from utils import (
    load_css_styles, require_login, get_current_user, initialize_session_state
)

# ====================================
# 🎨 페이지 설정 및 스타일
# ====================================

st.set_page_config(
    page_title="📝 VOC",
    page_icon="📝",
    layout="centered"
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
    
    show_voc_page()

def show_voc_page():
    """VOC 메인 페이지"""
    
    # 페이지 헤더
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>📝 VOC (Voice of Customer)</h1>
        <p style="color: #888; font-size: 1.2rem;">여러분의 소중한 의견을 들려주세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 안내 메시지
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
               padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;">
        <h3 style="margin-bottom: 1rem; text-align: center;">🎯 여러분의 목소리가 AE PLUS를 더 좋게 만듭니다</h3>
        <p style="margin-bottom: 0.5rem; text-align: center;">불편했던 점이나 개선했으면 하는 기능</p>
        <p style="margin-bottom: 0.5rem; text-align: center;">새로 추가되었으면 하는 기능</p>
        <p style="margin-bottom: 0; text-align: center;">사용 중 발견한 오류나 버그</p>
    </div>
    """, unsafe_allow_html=True)
    
    # VOC 제출 폼
    st.markdown("## ✍️ 의견 제출")
    
    # 폼 컨테이너 (세션 상태로 관리)
    if 'voc_category' not in st.session_state:
        st.session_state.voc_category = "🐛 버그 신고"
    if 'voc_title' not in st.session_state:
        st.session_state.voc_title = ""
    if 'voc_content' not in st.session_state:
        st.session_state.voc_content = ""
    if 'voc_contact' not in st.session_state:
        st.session_state.voc_contact = ""
    if 'voc_anonymous' not in st.session_state:
        st.session_state.voc_anonymous = False
    # 카테고리 선택
    category = st.selectbox(
        "📂 카테고리 *",
        [
            "🐛 버그 신고",
            "💡 기능 개선 제안", 
            "🆕 신규 기능 요청",
            "🎨 UI/UX 개선",
            "📚 컨텐츠 개선",
            "🔧 기타 의견"
        ],
        key="voc_category_input",
        help="가장 적절한 카테고리를 선택해주세요"
    )
    
    # 제목
    title = st.text_input(
        "📌 제목 *",
        placeholder="예: 챗봇 응답 속도 개선 요청",
        key="voc_title_input",
        help="의견을 간단히 요약해주세요"
    )
    
    # 내용
    content = st.text_area(
        "📄 상세 내용 *",
        placeholder="""예시:
- 현재 상황: 챗봇 응답이 너무 느려서 답답합니다
- 개선 요청: 응답 속도를 더 빠르게 해주세요  
- 기대 효과: 사용자 경험이 크게 개선될 것 같습니다""",
        height=200,
        key="voc_content_input",
        help="구체적으로 설명해주시면 더욱 도움이 됩니다"
    )
    
    # 연락처 (선택)
    contact = st.text_input(
        "📧 이메일 (선택)",
        placeholder="답변이 필요한 경우 이메일을 입력해주세요",
        key="voc_contact_input",
        help="피드백이 필요한 경우에만 입력해주세요"
    )
    
    # 익명 제출 여부
    anonymous = st.checkbox("🕶️ 익명으로 제출", key="voc_anonymous_input", help="체크하면 이름 없이 제출됩니다")
    
    st.divider()
    
    # 등록 버튼 (폼 외부)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        submitted = st.button(
            "📝 등록",
            type="primary",
            use_container_width=True
        )
    
    # 폼 검증 및 제출
    if submitted:
            if not title.strip():
                st.error("❌ 제목을 입력해주세요.")
            elif not content.strip():
                st.error("❌ 상세 내용을 입력해주세요.")
            else:
                # VOC 데이터 저장
                success = save_voc_data(category, title, content, contact, anonymous)
                if success:
                    st.success("✅ 소중한 의견 감사합니다! 검토 후 반영하겠습니다.")
                    st.balloons()
                    # 폼 초기화
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 제출 중 오류가 발생했습니다. 다시 시도해주세요.")
    
    st.divider()
    
    # FAQ
    show_voc_faq()

def save_voc_data(category, title, content, contact, anonymous):
    """VOC 데이터 저장"""
    try:
        user = get_current_user()
        voc_data = {
            "id": f"voc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": "" if anonymous else user.get("user_id", ""),
            "nickname": "" if anonymous else user.get("nickname", "익명"),
            "category": category,
            "title": title,
            "content": content,
            "contact": contact,
            "status": "접수",
            "anonymous": anonymous
        }
        
        # VOC 파일에 저장
        from config import DATA_CONFIG
        voc_file = DATA_CONFIG["voc_file"]
        
        # 기존 데이터 로드
        if os.path.exists(voc_file):
            with open(voc_file, 'r', encoding='utf-8') as f:
                all_voc = json.load(f)
        else:
            all_voc = []
        
        # 새 데이터 추가
        all_voc.append(voc_data)

        # 파일에 저장
        with open(voc_file, 'w', encoding='utf-8') as f:
            json.dump(all_voc, f, ensure_ascii=False, indent=2)

        # VOC 제출 시 포인트 적립 (익명이 아닌 경우만)
        if not anonymous and user:
            from utils import add_user_points, initialize_data, save_data
            data = initialize_data()
            username = user.get("knox_id") or user.get("username", "")
            if username:
                add_user_points(data, username, 50, "VOC 제출")
                save_data(data)

        return True
        
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False


def show_voc_faq():
    """VOC 관련 FAQ"""
    with st.expander("❓ VOC 관련 자주 묻는 질문", expanded=False):
        st.markdown("""
        **Q1. 제출한 의견은 언제 검토되나요?**  
        A. 모든 의견은 2-3 영업일 내에 검토됩니다. 긴급한 사안의 경우 더 빨리 처리됩니다.
        
        **Q2. 제출한 VOC의 처리 현황을 확인할 수 있나요?**  
        A. 현재는 이 페이지에서 전체 현황만 확인 가능합니다. 개별 추적 기능은 추후 업데이트 예정입니다.
        
        **Q3. 버그 신고 시 어떤 정보를 포함해야 하나요?**  
        A. 발생 상황, 기대했던 결과, 실제 결과, 재현 단계를 상세히 적어주세요.
        
        **Q4. 익명으로 제출해도 답변을 받을 수 있나요?**  
        A. 익명 제출 시 개별 답변은 어렵지만, 일반적인 개선사항은 공지를 통해 안내됩니다.
        
        **Q5. 제출한 의견이 실제로 반영되나요?**  
        A. 모든 의견을 검토하여 실현 가능한 개선사항은 우선순위에 따라 단계적으로 반영합니다.
        """)

# ====================================
# 🚀 앱 실행
# ====================================

if __name__ == "__main__":
    main()