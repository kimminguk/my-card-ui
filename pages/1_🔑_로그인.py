"""
=================================================================
🔑 AE WIKI - 로그인 페이지 (pages/1_🔑_로그인.py)
=================================================================

📋 파일 역할:
- 사용자 인증 시스템의 진입점 (로그인 + 회원가입)
- 간소화된 인증: 아이디/비밀번호 방식으로 빠른 접근
- 세션 관리: 로그인 성공 시 24시간 세션 유지
- 사용자 등록: 신규 사용자 회원가입 기능 제공

🔗 주요 컴포넌트:
- 로그인 탭: 기존 사용자 인증 (아이디/비밀번호)
- 회원가입 탭: 신규 사용자 등록 (녹스ID/닉네임/부서)
- 엔터키 지원: 로그인 탭에서 엔터키로 빠른 로그인
- 입력 검증: 실시간 유효성 검사 및 오류 메시지 표시

📊 입출력 데이터:
- 입력: 사용자 크리덴셜 (ID/PW), 프로필 정보 (녹스ID/닉네임/부서)
- 출력: 로그인 성공/실패, 회원가입 처리 결과
- 세션: st.session_state에 인증 정보 저장

🔄 연동 관계:
- utils.py: simple_login(), setup_session_after_login(), submit_registration_request()
- config.py: AUTH_CONFIG에서 검증 규칙 및 부서 목록 참조
- users_data.json: 사용자 계정 정보 영구 저장
- 홈페이지: 로그인 성공 시 🏠_Home.py로 자동 리다이렉트

⚡ 처리 흐름:
페이지 접속 -> 로그인 상태 확인 -> 인증 폼 표시 -> 인증 처리 
-> 성공 시 세션 설정 + 홈페이지 이동 | 실패 시 오류 메시지 표시

🔐 보안 기능:
- 비밀번호 마스킹 처리
- 로그인 시도 제한 (향후 구현 예정)
- 세션 타임아웃 관리 (24시간)
"""

import streamlit as st
import time

from config import APP_CONFIG
from utils import (
    is_logged_in, setup_session_after_login, simple_login, 
    check_session_validity, submit_registration_request
)

# ====================================
# 🎨 페이지 설정 및 스타일
# ====================================

st.set_page_config(
    page_title=f"🔑 로그인 - {APP_CONFIG['page_title']}",
    page_icon="🔑",
    layout="centered"
)

# 다크 테마 적용
from theme import apply_dark_theme
apply_dark_theme()

# 엔터키 지원 JavaScript
st.markdown("""

<script>
document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        // 현재 활성화된 탭이 로그인 탭인지 확인
        const activeTab = document.querySelector('[role="tab"][aria-selected="true"]');
        const isLoginTab = activeTab && activeTab.textContent.includes('로그인');
        
        // 로그인 탭에서만 엔터키 동작 허용
        if (isLoginTab) {
            const loginBtn = document.querySelector('[data-testid="stButton"] button[aria-label*="로그인"]');
            if (loginBtn) {
                loginBtn.click();
            }
        }
        // 회원가입 탭에서는 엔터키 동작 차단
        else {
            // 회원가입 폼 내의 input 요소에서 엔터키를 눌렀을 때만 차단
            const registrationForm = event.target.closest('form');
            if (registrationForm) {
                event.preventDefault();
                event.stopPropagation();
            }
        }
    }
});

// 🎨 동적 스타일 향상
document.addEventListener('DOMContentLoaded', function() {
    // 페이지 로드 애니메이션
    const container = document.querySelector('.main .block-container');
    if (container) {
        container.style.opacity = '0';
        container.style.transform = 'translateY(20px)';
        setTimeout(() => {
            container.style.transition = 'all 0.6s ease';
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
        }, 100);
    }
});
</script>
""", unsafe_allow_html=True)

# ====================================
# 🎯 메인 함수
# ====================================

def main():
    # 세션 유효성 검사 및 자동 연장
    check_session_validity()
    
    # 이미 로그인한 사용자는 홈으로 리디렉션
    if is_logged_in():
        st.success("✅ 이미 로그인된 상태입니다.")
        if st.button("🏠 홈으로 이동"):
            st.switch_page("🏠_Home.py")
        st.stop()
    
    show_auth_page()

def show_auth_page():
    """로그인 및 회원가입 페이지"""
    
    # 페이지 헤더
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>🔑 AE WIKI 인증</h1>
        <p style="color: #888; font-size: 1.1rem;">로그인 또는 회원가입을 선택하세요</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 탭으로 로그인/회원가입 구분
    tab1, tab2 = st.tabs(["🔓 로그인", "📝 회원가입"])
    
    with tab1:
        show_simple_login()
    
    with tab2:
        show_registration_form()

def show_simple_login():
    """간단한 로그인 폼"""
    st.markdown("### 🔑 로그인")
    st.info('🔑 Knox ID와 비밀번호를 입력해주세요. (회원가입 후 이용 가능합니다)')
    
    with st.form(key="login_form", clear_on_submit=False):
        username = st.text_input(
            "녹스아이디", 
            placeholder="예: knox.kim",
            help="등록된 사용자명을 입력하세요"
        )
        
        password = st.text_input(
            "비밀번호", 
            type="password",
            placeholder="비밀번호",
            help="회원가입 시 설정한 비밀번호를 입력해주세요."
        )
        
        # 로그인 버튼
        login_submitted = st.form_submit_button(
            "🚪 로그인", 
            type="primary", 
            use_container_width=True
        )
        
    # 로그인 처리
    if login_submitted:
        if not username or not password:
            st.error("❌ knox ID와 비밀번호를 입력해주세요.")
            return
            
        success, message, user_info = simple_login(username.strip(), password.strip())
        
        if success:
            # 로그인 성공
            setup_session_after_login(user_info['username'], user_info['name'])
            st.success(f'🎉 환영합니다, **{user_info["name"]}**님!')
            st.balloons()
            
            # 홈으로 자동 이동
            st.info('🏠 홈페이지로 자동 이동합니다...')
            time.sleep(1)
            st.switch_page('🏠_Home.py')
        else:
            st.error(f"❌ {message}")
            show_login_help()




def show_login_help():
    """streamlit-authenticator 로그인 도움말"""
    with st.expander("ℹ️ 로그인 안내", expanded=False):
        st.markdown("""
        **🔐로그인**
        
        - **Knox ID**: 예) minguk.kim
        - **비밀번호**: 회원가입 시 입력한 비밀번호
        - **문제가 계속되면 관리자에게 문의해주세요.**
        
        **💡관리자: minguk.kim@samsung.com**

        """)

def show_registration_form():
    """회원가입 신청 폼 (관리자 승인 방식)"""
    st.markdown("### 📝 회원가입 신청")
    st.info('📋 회원가입 신청 후 관리자 승인을 받아야 로그인 가능합니다 ( 9시/ 14시 일괄 승인)')
    
    # 회원가입 폼
    with st.form(key="registration_form", clear_on_submit=False):
        # 입력 필드들
        col1, col2 = st.columns(2)
        
        with col1:
            reg_username = st.text_input(
                "Knox ID*", 
                placeholder="예: Knox.kim",
                help="로그인 시 사용할 Knox ID*를 입력하세요"
            )
            
            reg_name = st.text_input(
                "닉네임*",
                placeholder="예: 홍길동",
                help="닉네임을 입력하세요"
            )
        
        with col2:
            reg_department = st.selectbox(
                "소속부서*",
                options=["AE팀", "DARM AE그룹", "NAND AE그룹", "기타"],
                help="소속 부서를 선택하세요"
            )
            
            reg_password = st.text_input(
                " 비밀번호*", 
                type="password",
                placeholder="8자 이상 입력",
                help=" 비밀번호는 승인 후 로그인 시 사용됩니다"
            )
        
        # 필수 입력 안내
        st.markdown("**필수 입력 사항*** - 모든 필드를 정확히 입력해주세요")
        
        # 구분선과 버튼 섹션
        st.markdown("---")
        st.info("💡 모든 정보를 입력했다면 아래 버튼을 클릭하여 회원가입을 완료하세요!")
        
        # 제출 버튼 (반드시 form 안에 있어야 함)
        register_submitted = st.form_submit_button(
            "📋 회원가입 신청하기", 
            type="primary", 
            use_container_width=True
        )
    
        
    # 회원가입 처리
    if register_submitted:
        if not all([reg_username, reg_name, reg_department, reg_password]):
            st.error("❌ 모든 필수 입력 사항을 채워주세요.")
            return
            
        if len(reg_password) < 8:
            st.error("❌ 비밀번호는 8자 이상이어야 합니다.")
            return
            
        # 회원가입 신청 제출
        success, message = submit_registration_request(
            reg_username.strip(), 
            reg_name.strip(), 
            reg_department, 
            reg_password
        )
        
        if success:
            st.success(f'🎉 {message}')
            st.balloons()
            
            # 신청 완료 안내
            st.info("""
            **📋 회원가입 신청이 완료되었습니다!**
            
            1. **관리자 검토**: 신청 내용을 관리자가 검토합니다
            2. **승인 알림**: 관리자가 승인 완료 시 사용 가능합니다.  
            3. **로그인 가능**: 승인 후 Knox ID와 비밀번호로 로그인하세요
            
            승인 과정은 보통 1-2 영업일 소요됩니다.
            """)
        else:
            st.error(f"❌ {message}")
            
            # 오류별 추가 도움말
            if "이미 등록된" in message:
                st.warning("💡 이미 등록된 Knox ID입니다. 다른 아이디를 사용하거나 관리자에게 문의하세요.")
            elif "승인 대기" in message:
                st.warning("💡 해당 Knox ID로 이미 신청이 접수되어 승인을 기다리고 있습니다.")

    # 회원가입 안내사항
    with st.expander("ℹ️ 회원가입 안내", expanded=False):
        st.markdown("""
        **📋 회원가입 절차:**
        
        1. **신청 제출**: 위 폼을 통해 회원가입을 신청합니다
        2. **관리자 검토**: 제출된 정보를 관리자가 검토합니다
        3. **승인/거절**: 검토 결과에 따라 승인 또는 거절됩니다
        4. **로그인**: 승인 완료 시 로그인 가능합니다
        
        **🔐 보안 정책:**
        
        - 모든 신규 계정은 관리자 승인이 필요합니다
        - 임시 비밀번호는 안전하게 해시화되어 저장됩니다
        - 승인 완료 후 비밀번호 변경을 권장합니다
        
        **📞 문의사항:**
        
        회원가입 관련 문의는 관리자에게 연락하시기 바랍니다.
        관리자 : minguk.kim@samsung.com
        """)


# ====================================
# 🚀 앱 실행
# ====================================

if __name__ == "__main__":
    main()