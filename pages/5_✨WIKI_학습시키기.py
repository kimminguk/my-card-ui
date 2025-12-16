"""
=================================================================
📄 AE WIKI - 5_✨챗봇_학습시키기 페이지 (5_✨챗봇_학습시키기.py)
=================================================================

📋 파일 역할:
- 사용자가 새로운 지식을 AE WIKI 시스템에 기여할 수 있는 양방향 학습 페이지
- 2가지 학습 방식 제공: ①용어 학습 ②자료 링크 학습 (순서 변경됨 - CHANGED)
- 관리자 검토 후 실제 챗봇 시스템에 반영되는 워크플로우 지원

🔗 주요 컴포넌트:
- 탭 1: 용어 학습시키기 (용어명 + 정의 직접 입력)
- 탭 2: 자료 링크 학습 (URL 링크 제출, 관리자 검토 후 크롤링)
- 리다이렉트 처리: AE 용어집 챗봇에서 "수정/추가" 요청 시 자동 이동
- 포인트 시스템: 학습 기여 시 100포인트 자동 지급

📊 입출력 데이터:
- 입력: 사용자 로그인 세션, 용어/URL 입력 데이터, 리다이렉트 컨텍스트
- 출력: learning_requests.json 파일에 학습 요청 저장, 성공 알림, 포인트 지급
- 처리: JSON 파일 기반 큐 시스템 (관리자가 8_⚙️_관리자.py에서 검토)

🔄 연동 관계:
- utils.py: 사용자 인증, 포인트 시스템, 데이터 초기화
- pages/3_🔍_AE_용어집_챗봇.py: "수정하기/추가하기" 버튼으로 리다이렉트 연동
- pages/8_⚙️_관리자.py: 학습 요청 승인/거부 처리
- config.py: 앱 기본 설정값 사용

⚡ 처리 흐름:
사용자 접속/리다이렉트 -> 탭 선택 (용어/자료링크) -> 폼 작성 -> 유효성 검증 
-> learning_requests.json에 저장 -> 100포인트 지급 -> 성공 알림 -> 관리자 검토 대기

🔄 데이터 흐름 다이어그램:
사용자 입력 -> validate_url()/폼검증 -> save_learning_request()/save_term_learning_request()
-> learning_requests.json 저장 -> add_user_points() -> 성공 알림
"""

import streamlit as st
import json
import os
import re
import time
from datetime import datetime

from utils import (
    load_css_styles, require_login, get_current_user, initialize_session_state,
    initialize_data, add_user_points
)
from config import get_available_indices, get_index_config

# ====================================
# 🎨 페이지 설정 및 스타일
# ====================================

st.set_page_config(
    page_title="✨ AI 챗봇 학습시키기",
    page_icon="✨",
    layout="centered"
)

# 다크 테마 적용
from theme import apply_dark_theme
apply_dark_theme()

# ====================================
# 🎯 메인 진입점 함수
# ====================================

def main():
    """
    🎯 목적: 5_✨챗봇_학습시키기 페이지의 메인 실행 함수
    
    📊 입력: Streamlit 웹 요청
    📤 출력: 학습 기여 페이지 UI (탭 형태)
    
    🔄 부작용:
    - st.session_state에 사용자 인증 정보 저장
    - 로그인 페이지로 리다이렉트 가능 (미인증 시)
    
    📞 호출 관계:
    - 호출자: Streamlit 앱 (__name__ == "__main__") 또는 페이지 네비게이션
    - 호출 대상: initialize_session_state(), require_login(), show_wiki_learning_page()
    
    ⚡ 처리 흐름:
    세션 초기화 -> 로그인 검증 -> 학습 페이지 렌더링
    """
    
    # STEP 1: 세션 상태 초기화
    # Streamlit 세션에 앱 상태 설정 (로그인 정보, 페이지 설정 등)
    initialize_session_state()
    
    # STEP 2: 사용자 인증 확인
    # 미인증 사용자는 자동으로 로그인 페이지로 리다이렉트
    if not require_login():
        return  # 미인증 시 여기서 종료
    
    # STEP 3: 메인 학습 페이지 렌더링
    show_wiki_learning_page()

def show_wiki_learning_page():
    """
    🎯 목적: 5_✨챗봇_학습시키기 메인 페이지 UI 렌더링 및 탭 구성
    
    📊 입력:
    - st.session_state.redirect_to_wiki_term (AE 용어집 챗봇에서 리다이렉트 시)
    - st.session_state.edit_content / add_context (수정/추가 컨텍스트)
    
    📤 출력:
    - 2개 탭 UI: ①용어 학습시키기 ②자료 링크 학습 (순서 변경 - CHANGED)
    - 리다이렉트 안내 메시지 (해당 시)
    
    🔄 부작용:
    - st.session_state.redirect_to_wiki_term 플래그 제거
    - 탭 포커스 설정 (리다이렉트 시)
    
    📞 호출 관계:
    - 호출자: main() -> show_wiki_learning_page()
    - 호출 대상: show_term_learning_section(), show_link_learning_section()
    
    🎨 UI 이벤트:
    - 탭 전환: "📝 용어 학습시키기" ↔ "📂 자료 링크 학습"
    - 리다이렉트 처리: AE 용어집 챗봇 "수정/추가" -> 용어 학습 탭 자동 선택
    
    📊 데이터 흐름:
    리다이렉트 확인 -> 안내 메시지 표시 -> 탭 구성 -> 각 탭별 폼 렌더링
    """
    
    # 페이지 헤더
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>✨ AI 챗봇 학습시키기</h1>
        <p style="color: #888; font-size: 1.2rem;">새로운 지식을 AI 챗봇에 추가해보세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # STEP 1: 용어집 챗봇 리다이렉트 처리
    # AE 용어집 챗봇에서 "수정하기" 또는 "추가하기" 버튼 클릭 시 이 페이지로 자동 이동
    redirect_type = st.session_state.get('redirect_to_wiki_term', None)
    if redirect_type:
        # 리다이렉트 타입별 안내 메시지 표시
        if redirect_type == "edit":
            # 기존 용어의 정의를 수정하고자 할 때
            st.info("🔗 AE 용어집 챗봇에서 **수정하기** 요청으로 이동했습니다. 아래 📝 용어 학습시키기 탭에서 정보를 수정해주세요.")
        elif redirect_type == "add":
            # 새로운 용어를 추가하고자 할 때
            st.info("🔗 AE 용어집 챗봇에서 **추가하기** 요청으로 이동했습니다. 아래 📝 용어 학습시키기 탭에서 새로운 용어를 등록해주세요.")
        
        # 리다이렉트 플래그 즉시 제거 (한 번만 표시하기 위함)
        del st.session_state['redirect_to_wiki_term']
    
    # 학습 방식 선택
    st.markdown("## 🎯 학습 방식 선택")
    
    # 리다이렉트된 경우 용어 학습 탭을 기본으로 선택 (이제 용어 학습이 첫 번째 탭)
    # default_tab = 0  # 미사용 변수 제거
    
    # 학습 방식 탭
    learning_tab = st.tabs(["📝 용어 학습시키기", "📂 자료 링크 학습", "🚀 챗봇 추가 요청하기"])

    # 리다이렉트된 경우 용어 학습 탭으로 포커스
    if redirect_type and redirect_type.startswith("term"):
        st.session_state.setdefault('active_tab', 0)

    with learning_tab[0]:
        show_term_learning_section(redirect_type)

    with learning_tab[1]:
        show_link_learning_section()

    with learning_tab[2]:
        show_index_request_section()

def show_link_learning_section():
    """자료 링크 학습 섹션"""
    
    # 안내 메시지
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;">
        <h3 style="margin-bottom: 1rem;">📂 자료 링크 학습 시스템</h3>
        <p style="margin-bottom: 0.5rem;">• <strong>URL 링크</strong>를 제출하면 관리자가 검토 후 WIKI에 학습시킵니다</p>
        <p style="margin-bottom: 0.5rem;">• 승인된 자료는 <strong>AE WIKI 챗봇</strong>과 <strong>용어집 챗봇</strong>의 답변에 활용됩니다</p>
        <p style="margin-bottom: 0.5rem;">• 반도체 기술 자료와 업무 관련 문서 모두 환영합니다!</p>
        <p style="margin-bottom: 0; background: rgba(255,255,255,0.2); padding: 0.8rem; border-radius: 8px; font-weight: bold;">
    </div>
    """, unsafe_allow_html=True)
    
    # 학습 자료 제출 폼
    st.markdown("## 📖 자료 링크 제출")
    
    # 챗봇 인덱스 선택
    st.markdown("### 🤖 어떤 챗봇에 추가할까요?")

    # 사용 가능한 인덱스 가져오기
    available_indices = get_available_indices()
    index_options = []
    index_mapping = {}

    for index_id in available_indices:
        index_config = get_index_config(index_id)
        display_name = index_config.get("display_name", index_id)
        index_options.append(display_name)
        index_mapping[display_name] = index_id

    selected_chatbot = st.selectbox(
        "🎯 대상 챗봇 선택 *",
        index_options,
        key="link_learning_chatbot_input",
        help="자료를 학습시킬 챗봇을 선택해주세요"
    )
    
    # URL 링크
    url_link = st.text_input(
        "🔗 URL 링크 *",
        placeholder="https://confluence.company.com/documents/...",
        key="link_learning_url_input",
        help="학습시킬 자료의 URL 링크를 입력해주세요"
    )
    
    # 자료 제목/설명
    title = st.text_input(
        "📌 자료 제목 *",
        placeholder="예: CMOS 공정 최적화 가이드라인 v2.0",
        key="link_learning_title_input",
        help="자료의 제목이나 간단한 설명을 입력해주세요"
    )
    
    # 상세 설명
    description = st.text_area(
        "📄 상세 설명",
        placeholder="""예시:
- 내용: CMOS 공정 최적화 방법과 품질 기준
- 대상: 공정 엔지니어, QA 담당자  
- 활용 방안: 챗봇이 CMOS 관련 질문에 더 정확하게 답변할 수 있음""",
        height=120,
        key="link_learning_description_input",
        help="자료의 내용과 활용 방안을 설명해주세요"
    )
    
    # 추가 요청사항
    additional_notes = st.text_area(
        "📝 추가 요청사항",
        placeholder="특별히 주의할 점이나 요청사항이 있다면 입력해주세요",
        height=80,
        key="link_learning_notes_input"
    )
    
    st.divider()
    
    # 등록 버튼 (폼 외부)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        submitted = st.button(
            "📚 등록",
            type="primary",
            use_container_width=True,
            key="link_learning_submit"
        )
    
    # 폼 검증 및 제출
    if submitted:
        if not url_link.strip():
            st.error("❌ URL 링크를 입력해주세요.")
        elif not title.strip():
            st.error("❌ 자료 제목을 입력해주세요.")
        elif not is_valid_url(url_link):
            st.error("❌ 올바른 URL 형식을 입력해주세요.")
        else:
            # 선택된 챗봇을 인덱스 ID로 변환
            selected_index_id = index_mapping[selected_chatbot]

            # 학습 요청 데이터 저장 (자료 링크)
            success = save_learning_request(selected_chatbot, selected_index_id, url_link, title, description, additional_notes, "자료링크")
            if success:
                st.success("✅ 학습 요청이 제출되었습니다! 관리자 검토 후 순차적으로 처리하겠습니다.")
                st.balloons()
                # 폼 초기화
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ 제출 중 오류가 발생했습니다. 다시 시도해주세요.")
    
    st.divider()
    
    # 가이드라인
    show_learning_guidelines()

def show_term_learning_section(redirect_type=None):
    """용어 학습시키기 섹션"""
    
    # 안내 메시지
    st.markdown("""
    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
               padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;">
        <h3 style="margin-bottom: 1rem;">📝 용어 학습시키기 시스템</h3>
        <p style="margin-bottom: 0.5rem;">• <strong>특정 용어</strong>와 <strong>정의/설명</strong>을 직접 등록할 수 있습니다</p>
        <p style="margin-bottom: 0.5rem;">• 등록된 용어는 <strong>AE 용어집 챗봇</strong>에서 검색 가능해집니다</p>
        <p style="margin-bottom: 0.5rem;">• 반도체 전문 용어, 업무 관련 용어 모두 환영합니다!</p>
        <p style="margin-bottom: 0; background: rgba(255,255,255,0.2); padding: 0.8rem; border-radius: 8px; font-weight: bold;">💰 용어를 등록하면 <strong>100포인트</strong>를 획득할 수 있습니다!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 리다이렉트 컨텍스트 정보 표시
    if redirect_type:
        edit_content = st.session_state.get('edit_content', '')
        add_context = st.session_state.get('add_context', '')
        
        if edit_content:
            st.markdown("### 📄 수정 대상 내용")
            with st.expander("기존 답변 내용 확인", expanded=False):
                st.markdown(edit_content)
        elif add_context:
            st.markdown("### 📄 관련 컨텍스트")
            with st.expander("관련 정보 확인", expanded=False):
                st.markdown(add_context)
    
    # 용어 학습 제출 폼
    st.markdown("## 📝 용어 정보 등록")
    
    # 용어명
    term_name = st.text_input(
        "📌 용어명 *",
        placeholder="예: CMOS, DDR5, FinFET",
        key="term_learning_name_input",
        help="학습시킬 용어명을 입력해주세요"
    )
    
    # 용어 정의/설명
    term_definition = st.text_area(
        "📝 용어 정의/설명 *",
        placeholder="""예시:
CMOS (Complementary Metal-Oxide-Semiconductor)는 반도체 제조 기술의 한 종류로, 
P형과 N형 MOS 트랜지스터를 상호 보완적으로 사용하는 기술입니다.

주요 특징:
- 낮은 전력 소모
- 높은 집적도
- 우수한 노이즈 마진

활용 분야:
- 마이크로프로세서
- 메모리 소자
- 디지털 회로""",
        height=200,
        key="term_learning_definition_input",
        help="용어의 정의와 상세 설명을 입력해주세요"
    )
    
    
    # 추가 요청사항
    term_additional_notes = st.text_area(
        "📝 추가 요청사항 (선택)",
        placeholder="특별히 주의할 점이나 요청사항이 있다면 입력해주세요",
        height=80,
        key="term_learning_additional_notes_input"
    )
    
    st.divider()
    
    # 등록 버튼
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        term_submitted = st.button(
            "📝 등록",
            type="primary",
            use_container_width=True,
            key="term_learning_submit"
        )
    
    # 폼 검증 및 제출
    if term_submitted:
        if not term_name.strip():
            st.error("❌ 용어명을 입력해주세요.")
        elif not term_definition.strip():
            st.error("❌ 용어 정의/설명을 입력해주세요.")
        else:
            # 용어 학습 요청 데이터 저장
            success = save_term_learning_request(
                term_name, term_definition, term_additional_notes
            )
            if success:
                st.success("✅ 용어 학습 요청이 제출되었습니다! 관리자 검토 후 용어집에 추가하겠습니다.")
                st.balloons()
                
                # 리다이렉트 관련 세션 정리
                if 'edit_content' in st.session_state:
                    del st.session_state['edit_content']
                if 'add_context' in st.session_state:
                    del st.session_state['add_context']
                
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ 제출 중 오류가 발생했습니다. 다시 시도해주세요.")
    
    st.divider()
    
    # 용어 학습 가이드라인
    show_term_learning_guidelines()

def is_valid_url(url):
    """URL 유효성 검사"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def save_learning_request(chatbot_name, index_id, url_link, title, description, additional_notes, request_type="자료링크"):
    """
    🎯 목적: 자료 링크 학습 요청 데이터를 JSON 파일에 저장하고 포인트 지급
    
    📊 입력:
    - category (str): 자료 분류 (🔬 반도체 기술, ⚙️ 공정 기술 등)
    - url_link (str): 학습시킬 URL 링크 (CHANGED: EDM 링크 -> URL 링크)
    - title (str): 자료 제목/설명
    - description (str): 상세 설명 (선택)
    - target_bots (list): 적용할 챗봇 목록 (DEPRECATED: 현재 사용 안함)
    - additional_notes (str): 추가 요청사항 (선택)
    - request_type (str): 요청 타입 ("자료링크" 고정)
    
    📤 출력:
    - bool: 저장 성공 시 True, 실패 시 False
    
    🔄 부작용:
    - learning_requests.json 파일에 새 요청 추가
    - 사용자에게 100포인트 자동 지급
    - 실패 시 st.error() 메시지 표시
    
    📞 호출 관계:
    - 호출자: show_link_learning_section() -> "📚 등록" 버튼 클릭 시
    - 호출 대상: get_current_user(), initialize_data(), add_user_points(), get_username()
    
    🔄 데이터 흐름:
    사용자 입력 -> 요청 데이터 구조화 -> JSON 파일 읽기 -> 새 데이터 추가 
    -> JSON 파일 저장 -> 포인트 지급 -> 성공/실패 반환
    
    ⚠️ 예외 처리:
    - JSON 파일 읽기/쓰기 오류: 사용자에게 "저장 오류" 메시지 표시
    - 파일이 없는 경우: 빈 배열로 초기화 후 진행
    """
    try:
        # STEP 1: 사용자 정보 조회
        user = get_current_user()  # 현재 로그인된 사용자 정보 (utils.py)
        
        # STEP 2: 학습 요청 데이터 구조화
        # JSON 파일에 저장될 표준화된 데이터 구조 생성
        learning_data = {
            "id": f"learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # 고유 ID (timestamp 기반)
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),     # 요청 시간
            "user_id": user.get("user_id", ""),                           # 요청자 내부 ID
            "nickname": user.get("nickname", ""),                         # 요청자 닉네임 (관리자용)
            "chatbot_name": chatbot_name,                                  # 선택된 챗봇명
            "index_id": index_id,                                          # 대상 인덱스 ID
            "url_link": url_link,                                          # 학습할 URL 링크
            "title": title,                                                # 자료 제목
            "description": description,                                    # 상세 설명
            "additional_notes": additional_notes,                          # 추가 요청사항
            "request_type": request_type,  # 요청 타입 구분자 ("자료링크" or "용어학습")
            "status": "대기중",            # 관리자 처리 상태 (대기중 -> 승인/거부)
            "admin_notes": ""              # 관리자 메모 (처리 시 추가)
        }
        
        # STEP 3: JSON 파일에 저장 (큐 시스템)
        from config import DATA_CONFIG
        learning_file = DATA_CONFIG["learning_requests_file"]  # 관리자가 검토할 요청 큐 파일
        
        # STEP 3-1: 기존 요청들 로드
        if os.path.exists(learning_file):
            # 파일이 존재하면 기존 요청 목록을 읽어옴
            with open(learning_file, 'r', encoding='utf-8') as f:
                all_requests = json.load(f)  # 배열 형태의 요청 목록
        else:
            # 파일이 없으면 빈 배열로 초기화 (첫 번째 요청인 경우)
            all_requests = []
        
        # STEP 3-2: 새 요청을 기존 목록에 추가
        all_requests.append(learning_data)  # 배열 끝에 새 요청 추가
        
        # STEP 3-3: 업데이트된 목록을 파일에 저장
        with open(learning_file, 'w', encoding='utf-8') as f:
            # ensure_ascii=False: 한글 깨짐 방지
            # indent=2: 가독성을 위한 들여쓰기
            json.dump(all_requests, f, ensure_ascii=False, indent=2)
        
        # STEP 4: 사용자에게 보상 지급
        # WIKI 학습 자료 기여에 대한 인센티브로 100포인트 지급 (보안 강화)
        from utils import save_data
        data = initialize_data()  # 포인트 시스템 데이터 로드
        current_user = get_current_user()  # 현재 로그인한 사용자 정보 가져오기
        username = current_user.get("username", "Unknown") if current_user else "Anonymous"
        add_user_points(data, username, 100, "WIKI학습")  # 올바른 순서로 호출
        save_data(data)  # 포인트 데이터 저장
        
        return True  # 저장 성공
        
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

def save_term_learning_request(term_name, term_definition, additional_notes):
    """용어 학습 요청 데이터 저장"""
    try:
        user = get_current_user()
        term_data = {
            "id": f"term_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.get("user_id", ""),
            "nickname": user.get("nickname", ""),
            "term_name": term_name,
            "term_definition": term_definition,
            "additional_notes": additional_notes,
            "request_type": "용어학습",  # 요청 타입 추가
            "status": "대기중",
            "admin_notes": ""
        }
        
        # 학습 요청 파일에 저장 (동일한 파일 사용)
        from config import DATA_CONFIG
        learning_file = DATA_CONFIG["learning_requests_file"]
        
        # 기존 데이터 로드
        if os.path.exists(learning_file):
            with open(learning_file, 'r', encoding='utf-8') as f:
                all_requests = json.load(f)
        else:
            all_requests = []
        
        # 새 데이터 추가
        all_requests.append(term_data)
        
        # 파일에 저장
        with open(learning_file, 'w', encoding='utf-8') as f:
            json.dump(all_requests, f, ensure_ascii=False, indent=2)
        
        # 용어 학습으로 100포인트 지급 (보안 강화)
        from utils import save_data
        data = initialize_data()
        current_user = get_current_user()  # 현재 로그인한 사용자 정보 가져오기
        username = current_user.get("username", "Unknown") if current_user else "Anonymous"
        add_user_points(data, username, 100, "용어학습")  # 올바른 순서로 호출
        save_data(data)  # 포인트 데이터 저장
        
        return True
        
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False


def show_learning_guidelines():
    """자료 링크 학습 가이드라인"""
    with st.expander("📋 자료 링크 학습 가이드라인", expanded=False):
        st.markdown("""
        ### ✅ 제출 가능한 자료
        - **기술 문서**: 반도체 공정, 설계, 분석 관련 자료
        - **업무 매뉴얼**: 업무 절차, 규정, 가이드라인
        - **교육 자료**: 기술 교육, 업무 교육 자료
        - **품질 문서**: QC 기준, 검사 절차, 품질 가이드
        
        ### ❌ 제출 불가 자료  
        - 기밀 정보나 보안이 필요한 문서
        - 개인정보가 포함된 자료
        - 저작권 문제가 있는 외부 자료
        - 임시 파일이나 테스트 문서
        
        ### ⏱️ 처리 일정
        1. **제출 후 1-2일**: 관리자 검토 및 승인
        2. **승인 후 3-5일**: 자료 분석 및 학습 데이터 준비  
        3. **준비 완료 후 1-2일**: WIKI 시스템에 학습 적용
        4. **적용 완료 후**: 챗봇에서 해당 내용 답변 가능
        
        ### 📞 문의사항
        학습 관련 문의나 급한 요청사항이 있으시면 관리자에게 연락해주세요.
        """)

def show_term_learning_guidelines():
    """용어 학습 가이드라인"""
    with st.expander("📋 용어 학습 가이드라인", expanded=False):
        st.markdown("""
        ### ✅ 등록 가능한 용어
        - **반도체 기술 용어**: CMOS, FinFET, EUV, TSV 등
        - **공정 기술 용어**: CMP, ALD, CVD, PVD 등
        - **업무 관련 용어**: EOL, ECO, DFT, DFM 등
        - **품질/테스트 용어**: JEDEC, HTOL, WHTOL 등
        
        ### 📝 작성 가이드라인
        - **명확성**: 용어의 정의를 명확하고 이해하기 쉽게 작성
        - **완성도**: 정의, 특징, 활용 분야 등을 포함한 완전한 설명
        - **정확성**: 기술적으로 정확한 정보만 제공
        - **일관성**: 기존 용어집과 일관된 형식과 톤 유지
        
        ### ⏱️ 처리 일정
        1. **제출 후 1일**: 관리자 검토 및 승인
        2. **승인 후 1-2일**: 용어집 데이터베이스에 추가
        3. **추가 완료 후**: AE 용어집 챗봇에서 즉시 검색 가능
        
        ### 💡 작성 팁
        - 영문 용어의 경우 풀네임과 약어를 모두 포함
        - 관련 키워드를 많이 입력할수록 검색이 잘 됩니다
        - 참고 자료를 명시하면 신뢰도가 높아집니다
        """)

def show_index_request_section():
    """인덱스 추가요청 섹션"""

    # 안내 메시지
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;">
        <h3 style="margin-bottom: 1rem;">🚀 새로운 챗봇 추가요청 시스템</h3>
        <p style="margin-bottom: 0.5rem;">• <strong>새로운 전문 분야</strong>의 챗봇 인덱스를 요청할 수 있습니다</p>
        <p style="margin-bottom: 0.5rem;">• 승인된 인덱스는 <strong>통합 챗봇</strong>에 새로운 전문 분야로 추가됩니다</p>
        <p style="margin-bottom: 0.5rem;">• 요청 시 해당 분야의 RAG 데이터와 시스템 프롬프트가 함께 구성됩니다</p>
        <p style="margin-bottom: 0; background: rgba(255,255,255,0.2); padding: 0.8rem; border-radius: 8px; font-weight: bold;">💰 인덱스 추가요청 시 <strong>포인트</strong>를 획득할 수 있습니다!</p>
    </div>
    """, unsafe_allow_html=True)

    # 인덱스 요청 폼
    st.markdown("## 🎯 새로운 인덱스 요청")

    # 인덱스 기본 정보
    col1, col2 = st.columns(2)

    with col1:
        index_name = st.text_input(
            "🏷️ 인덱스명 *",
            placeholder="예: process_engineering",
            key="index_request_name",
            help="영문 소문자와 언더스코어로 구성 (예: process_engineering)"
        )

    with col2:
        display_name = st.text_input(
            "📋 표시명 *",
            placeholder="예: 프로젝트명",
            key="index_request_display_name",
            help="통합 챗봇에서 표시될 이름 (이모지 포함 가능)"
        )

    # 인덱스 설명
    description = st.text_input(
        "📝 간단 설명 *",
        placeholder="예: 반도체 공정 기술 전문 AI 어시스턴트",
        key="index_request_description",
        help="인덱스의 역할을 한 줄로 설명해주세요"
    )


    # 시스템 프롬프트 요청
    st.markdown("### 🤖 AI 어시스턴트 특성")

    system_prompt_description = st.text_area(
        "🧠 시스템 프롬프트 요청사항 *",
        placeholder="""예시:
- 역할: 반도체 공정엔지니어링 전문가
- 범위: 웨이퍼 가공, 식각, 증착, 리소그래피 등 제조 공정
- 목표: 공정 최적화와 수율 향상 지원
- 답변 스타일: 기술적으로 정확하고 실무에 바로 적용 가능한 답변""",
        height=150,
        key="index_request_system_prompt",
        help="새로운 AI 어시스턴트가 어떤 특성을 가져야 하는지 상세히 설명해주세요"
    )


    # 추가 요청사항
    additional_notes = st.text_area(
        "📝 추가 요청사항 (선택)",
        placeholder="특별한 요구사항이나 고려사항이 있다면 입력해주세요",
        height=80,
        key="index_request_additional_notes"
    )

    st.divider()

    # 등록 버튼
    col1, col2, col3 = st.columns([2, 1, 2])

    with col2:
        if st.button("🚀 인덱스 추가요청", type="primary", use_container_width=True):
            # 필수 필드 검증
            if not index_name.strip():
                st.error("❌ 인덱스명을 입력해주세요.")
            elif not display_name.strip():
                st.error("❌ 표시명을 입력해주세요.")
            elif not description.strip():
                st.error("❌ 간단 설명을 입력해주세요.")
            elif not system_prompt_description.strip():
                st.error("❌ 시스템 프롬프트 요청사항을 입력해주세요.")
            else:
                # 인덱스 요청 데이터 저장
                success = save_index_request(
                    index_name, display_name, description,
                    system_prompt_description, additional_notes
                )
                if success:
                    st.success("✅ 인덱스 추가요청이 제출되었습니다! 관리자 검토 후 통합 챗봇에 추가하겠습니다.")
                    st.balloons()

                    # 포인트 획득 알림
                    user = get_current_user()
                    if user:
                        st.info(f"🎉 {user['nickname']}님이 포인트를 획득하셨습니다!")

                    # 입력 필드 초기화
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 제출 중 오류가 발생했습니다. 다시 시도해주세요.")

    # 인덱스 요청 가이드라인
    show_index_request_guidelines()

def save_index_request(index_name, display_name, description,
                      system_prompt_description, additional_notes):
    """인덱스 추가요청 데이터 저장"""
    try:
        user = get_current_user()
        index_request_data = {
            "id": f"index_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.get("user_id", ""),
            "nickname": user.get("nickname", ""),

            # 기본 정보
            "index_name": index_name,
            "display_name": display_name,
            "description": description,

            # AI 특성
            "system_prompt_description": system_prompt_description,

            # 기타
            "additional_notes": additional_notes,

            "request_type": "인덱스추가",
            "status": "대기중",
            "admin_notes": ""
        }

        # 학습 요청 파일에 저장 (동일한 파일 사용)
        from config import DATA_CONFIG
        learning_file = DATA_CONFIG["learning_requests_file"]

        # 기존 데이터 로드
        if os.path.exists(learning_file):
            with open(learning_file, 'r', encoding='utf-8') as f:
                all_requests = json.load(f)
        else:
            all_requests = []

        # 새 요청 추가
        all_requests.append(index_request_data)

        # 파일에 저장
        with open(learning_file, 'w', encoding='utf-8') as f:
            json.dump(all_requests, f, ensure_ascii=False, indent=2)

        # 포인트 지급 (200포인트)
        from utils import save_data
        data = initialize_data()
        current_user = get_current_user()
        username = current_user.get("username", "Unknown") if current_user else "Anonymous"
        add_user_points(data, username, 200, "인덱스추가요청")
        save_data(data)

        return True

    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

def show_index_request_guidelines():
    """인덱스 요청 가이드라인"""
    with st.expander("📋 인덱스 추가요청 가이드라인", expanded=False):
        st.markdown("""
        ### 📝 요청 작성 가이드

        #### 🎯 인덱스명 작성 규칙
        - **형식**: 영문 소문자와 언더스코어(_)만 사용
        - **예시**: `process_engineering`, `data_analysis`, `quality_assurance`
        - **금지**: 대문자, 특수문자, 공백, 한글

        #### 🎨 표시명 및 아이콘
        - **표시명**: 이모지 + 한글명 (예: ⚙️ 공정엔지니어링)
        - **아이콘**: 관련성 있는 이모지 1개 권장
        - **색상**: 기존 인덱스와 구별되는 색상 선택

        #### 🤖 시스템 프롬프트 요청
        - **역할**: AI가 담당할 전문가 역할 명시
        - **범위**: 다룰 주제와 영역 구체적 설명
        - **목표**: 사용자에게 제공할 가치 명확화
        - **스타일**: 답변 방식과 톤 가이드라인

        ### ⏱️ 처리 일정
        1. **제출 후 2-3일**: 관리자 검토 및 기술적 검증
        2. **승인 후 1주일**: RAG 인덱스 및 시스템 프롬프트 구성
        3. **구성 완료 후**: 통합 챗봇에 새 인덱스 추가
        4. **테스트 후**: 정식 서비스 시작

        ### ✅ 승인 기준
        - **필요성**: 기존 인덱스로 커버되지 않는 새로운 영역
        - **활용도**: 실제 업무에 도움이 되는 실용적 가치
        - **데이터**: 충분한 참고 자료와 데이터 소스 확보 가능성
        - **차별성**: 기존 인덱스와의 명확한 차별점

        ### 💡 성공적인 요청 팁
        - **구체성**: 모호한 설명보다는 구체적이고 명확한 설명
        - **실용성**: 실제 업무 시나리오와 사용 사례 제시
        - **완성도**: 모든 필수 항목을 빠짐없이 작성
        - **근거**: 왜 이 인덱스가 필요한지 명확한 근거 제시
        """)

# ====================================
# 🚀 앱 실행
# ====================================

if __name__ == "__main__":
    main()