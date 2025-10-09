"""
=================================================================
📚 AE WIKI - 팀원에게 물어보기 페이지 (pages/6_📚_팀원에게_물어보기.py)
=================================================================

📋 파일 역할:
- 팀원 간 지식 공유를 위한 Q&A 커뮤니티 시스템 통합 허브
- 실시간 질문 등록, 답변, 좋아요 기능으로 활발한 소통 지원
- 카테고리별 검색 및 필터링으로 효율적인 정보 탐색
- 포인트 시스템으로 지식 공유 활동 장려

🔗 주요 컴포넌트:
- 질문 작성 폼: 제목/카테고리/내용 입력 (익명 질문 지원)
- 질문 목록: 검색/필터링 가능한 Q&A 리스트
- 답변 시스템: 질문별 답변 작성 및 좋아요 기능
- 포인트 적립: 질문/답변/좋아요 시 자동 포인트 지급

📊 입출력 데이터:
- 입력: 질문/답변 내용, 검색 키워드, 카테고리 필터
- 출력: Q&A 목록, 답변 내역, 좋아요 상태, 포인트 적립 알림
- 저장: knowledge_data.json의 questions/answers/likes 섹션

🔄 연동 관계:
- utils.py: Q&A CRUD 함수들, 포인트 시스템, 검색 기능
- config.py: CATEGORIES 설정에서 질문 분류 옵션 참조
- 🏠_Home.py: 빠른 액션 버튼에서 "질문 작성하기"로 연결

⚡ 처리 흐름:
질문 작성: 폼 입력 -> add_question() -> 포인트 적립 -> 목록 새로고침
답변 작성: 답변 폼 -> add_answer() -> 포인트 적립 -> 답변 표시  
좋아요: 버튼 클릭 -> toggle_like() -> 상태 업데이트 -> 포인트 적립

🎯 핵심 기능:
- 실시간 Q&A 상호작용
- 카테고리 기반 질문 분류  
- 검색 및 필터링 시스템
- 포인트 기반 참여 동기부여
"""

import streamlit as st
import time
from typing import List, Dict

from config import CATEGORIES
from utils import (
    load_css_styles, require_login, get_current_user, initialize_session_state,
    initialize_data, save_data, add_question, add_answer, search_questions,
    get_user_id, toggle_like
)

# ====================================
# 🎨 페이지 설정 및 스타일
# ====================================

st.set_page_config(
    page_title="📚 팀원에게 물어보기",
    page_icon="📚",
    layout="wide"
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
    
    show_knowledge_hub()

def show_knowledge_hub():
    """팀원에게 물어보기 메인 페이지"""
    
    # 페이지 헤더
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>📚 팀원에게 물어보기</h1>
        <p style="color: #888; font-size: 1.2rem;">질문하기 • 답변하기 • 검색하기 - 모든 지식 활동의 중심</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 데이터 초기화
    data = initialize_data()
    
    # 탭 구성
    tab1, tab2 = st.tabs(["🔍        질문 검색 & 답변하기        ", "❓      새로운 질문 작성하기      "])
    
    with tab1:
        show_search_and_answer_tab(data)
    
    with tab2:
        show_question_tab(data)

def show_question_tab(data: Dict):
    """질문하기 탭"""
    st.markdown("## ❓ 새 질문 작성")
    
    # 안내 메시지
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
               padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h4>💡 궁금한 것이 있으신가요?</h4>
        <p style="margin-bottom: 0.5rem;">• 기술적 질문부터 업무 관련 질문까지 무엇이든 환영합니다</p>
        <p style="margin-bottom: 0.5rem;">• 익명으로도 질문할 수 있으니 부담 없이 물어보세요</p>
        <p style="margin-bottom: 0;">• 질문하면 <strong>100포인트</strong>를 획득할 수 있습니다!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 질문 작성 폼 (일반 위젯 사용)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        category = st.selectbox(
            "📂 카테고리",
            CATEGORIES,
            key="question_category",
            help="질문이 속할 카테고리를 선택해주세요"
        )
    
    with col2:
        anonymous = st.checkbox(
            "🎭 익명 질문",
            key="question_anonymous",
            help="체크하면 이름 없이 질문됩니다"
        )
    
    title = st.text_input(
        "📌 질문 제목",
        placeholder="예: FinFET 기술의 장점이 궁금합니다",
        key="question_title",
        help="질문을 간단히 요약해주세요"
    )
    
    content = st.text_area(
        "📝 질문 내용",
        placeholder="""구체적인 질문 내용을 작성해주세요.
        
예시:
- 현재 상황: FinFET 기술에 대해 공부하고 있습니다
- 궁금한 점: 기존 MOSFET 대비 어떤 장점이 있는지 궁금합니다  
- 추가 정보: 전력 효율성이나 성능 면에서 구체적인 차이를 알고 싶습니다""",
        height=200,
        key="question_content",
        help="상세한 설명을 작성하시면 더 정확한 답변을 받을 수 있습니다"
    )
    
    st.divider()
    
    # 등록 버튼 (폼 외부)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        submitted = st.button(
            "📤 등록",
            type="primary",
            use_container_width=True
        )
    
    # 폼 검증 및 제출
    if submitted:
        if not title.strip():
            st.error("❌ 질문 제목을 입력해주세요.")
        elif not content.strip():
            st.error("❌ 질문 내용을 입력해주세요.")
        else:
            # 질문 저장 (익명 옵션 포함)
            add_question(data, title, category, content, anonymous)
            save_data(data)
            
            st.success("✅ 질문이 등록되었습니다! 곧 답변을 받아보실 수 있습니다.")
            st.balloons()
            
            # 포인트 획득 알림
            user = get_current_user()
            if user and not anonymous:
                st.info(f"🎉 {user['nickname']}님이 100포인트를 획득하셨습니다!")
            elif user and anonymous:
                st.info("🎉 익명 질문으로 100포인트를 획득하셨습니다!")
            
            # 입력 필드 초기화를 위해 세션 상태 키 삭제
            keys_to_clear = ["question_title", "question_content", "question_category", "question_anonymous"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # 페이지 새로고침으로 폼 초기화
            time.sleep(1)
            st.rerun()

def show_search_and_answer_tab(data: Dict):
    """질문 검색 & 답변 탭"""
    st.markdown("## 🔍 질문 검색 및 답변")
    
    # 검색 및 필터 영역
    col1, col2, col3 = st.columns([2, 1, 1])
    
    def perform_search():
        """검색 실행 함수"""
        # 검색 결과를 세션 상태에 저장
        filtered_questions = search_questions(data, search_term, category_filter)
        
        # 정렬 적용
        if sort_option == "답변많은순":
            # 각 질문의 답변 수 계산
            for q in filtered_questions:
                q["answer_count"] = len([a for a in data["answers"] if a["question_id"] == q["id"]])
            filtered_questions.sort(key=lambda x: x["answer_count"], reverse=True)
        else:  # 최신순
            filtered_questions.sort(key=lambda x: x["timestamp"], reverse=True)
        
        st.session_state.search_results = filtered_questions
        st.session_state.search_performed = True
    
    with col1:
        search_term = st.text_input(
            "🔍 검색어", 
            placeholder="키워드를 입력하고 엔터를 누르세요",
            key="search_input",
            on_change=perform_search if st.session_state.get("search_input", "").strip() else None
        )
    
    with col2:
        category_filter = st.selectbox(
            "📂 카테고리", 
            ["전체"] + CATEGORIES,
            on_change=perform_search if search_term and search_term.strip() else None
        )
    
    with col3:
        sort_option = st.selectbox(
            "🔄 정렬", 
            ["최신순", "답변많은순"],
            on_change=perform_search if search_term and search_term.strip() else None
        )
    
    # 검색어가 있을 때 자동 검색 실행
    if search_term and search_term.strip():
        perform_search()
    
    # 검색 결과 또는 질문 목록 표시
    if hasattr(st.session_state, 'search_performed') and st.session_state.search_performed:
        questions_to_show = st.session_state.search_results
        st.markdown(f"### 📋 검색 결과 ({len(questions_to_show)}개)")
    else:
        # 기본적으로 최근 질문 10개 표시
        questions_to_show = sorted(data["questions"], key=lambda x: x["timestamp"], reverse=True)[:10]
        st.markdown(f"### 📋 질문 목록 ({len(questions_to_show)}개)")
    
    # 질문 목록 표시
    if not questions_to_show:
        st.info("🤷‍♂️ 조건에 맞는 질문이 없습니다. 새로운 질문을 등록해보세요!")
    else:
        show_questions_with_answers(data, questions_to_show)

def show_questions_with_answers(data: Dict, questions: List[Dict]):
    """질문과 답변을 표시하는 함수"""
    for i, question in enumerate(questions):
        # 질문별 고유 키로 세션 상태 관리
        question_key = f"question_expanded_{question['id']}"
        
        # 질문 카드 스타일링 - 연한 색상 적용
        # card_color = "#fafbfc"  # 미사용 변수 제거
        # border_color = "#d1d9ff"  # 미사용 변수 제거
        
        # 답변 수 계산
        answer_count = len([a for a in data["answers"] if a["question_id"] == question["id"]])
        
        # 질문 카드 디자인 (버튼이 카드 안에 포함)
        is_expanded = st.session_state.get(question_key, False)
        button_icon = "🔼" if is_expanded else "🔽"
        
        # CSS로 해당 버튼의 텍스트를 왼쪽 정렬
        st.markdown(f"""
        <style>
        /* 모든 가능한 버튼 선택자로 왼쪽 정렬 강제 적용 */
        .stButton button,
        [data-testid="stButton"] button,
        button[kind="secondary"],
        .stButton > button {{
            text-align: left !important;
            justify-content: flex-start !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # 질문 카드 (클릭 가능한 버튼으로 만들기)
        if st.button(
            f"""❓ {question["title"]}

👤 {question.get('author', '익명')} • 📅 {question['timestamp']} • 💬 {answer_count}개 답변 {button_icon}""",
            key=f"card_{question['id']}",
            use_container_width=True,
            help="클릭하여 펼치기/접기"
        ):
            st.session_state[question_key] = not is_expanded
            st.rerun()
        
        # 질문 상세 내용 (토글 상태에 따라 표시)
        if st.session_state.get(question_key, False):
            # 질문 내용 (간단한 텍스트 형태)
            st.markdown("**📝 질문 내용:**")
            st.markdown(question['content'])
            
            st.divider()
            
            # 기존 답변들 표시
            question_answers = [a for a in data["answers"] if a["question_id"] == question["id"]]
            
            if question_answers:
                st.markdown(f"**💬 답변 ({len(question_answers)}개):**")
                
                for j, answer in enumerate(sorted(question_answers, key=lambda x: x["timestamp"], reverse=True)):
                    # 좋아요 정보
                    like_key = f"answer_{answer['id']}"
                    likes = data.get("likes", {}).get(like_key, [])
                    user_id = get_user_id()
                    liked = user_id in likes
                    
                    # 심플한 답변 표시
                    st.markdown(f"**👤 {answer['author']}** • {answer['timestamp']}")
                    st.markdown(answer['content'])
                    
                    # 좋아요 버튼 - 오른쪽 중앙 배치
                    col1, col2 = st.columns([6, 1])
                    with col2:
                        if st.button(
                            f"{'❤️' if liked else '🤍'} {len(likes)}", 
                            key=f"like_{answer['id']}",
                            use_container_width=True
                        ):
                            toggle_like(data, answer['id'])
                            save_data(data)
                            st.rerun()
                    
                    st.divider()
            else:
                st.info("💭 아직 답변이 없습니다. 첫 번째 답변을 작성해보세요!")
            
            # 새 답변 작성 섹션 (간단한 텍스트 형태)
            st.markdown("**✍️ 새 답변 작성:**")
            
            answer_content = st.text_area(
                "답변 내용",
                placeholder="💡 도움이 되는 답변을 작성해주세요...\n\n팁:\n• 구체적인 경험이나 지식을 공유해보세요\n• 참고 자료나 링크가 있으면 함께 제공해주세요\n• 다른 사람이 이해하기 쉽게 설명해주세요",
                height=150,
                key=f"answer_content_{question['id']}",
                label_visibility="collapsed"
            )
            
            # 답변 등록 버튼
            answer_col1, answer_col2, answer_col3 = st.columns([2, 1, 2])
            with answer_col2:
                answer_submitted = st.button(
                    "💬 답변 등록",
                    key=f"answer_submit_{question['id']}",
                    type="primary",
                    use_container_width=True
                )
            
            if answer_submitted:
                if not answer_content.strip():
                    st.error("❌ 답변 내용을 입력해주세요.")
                else:
                    # 답변 저장
                    add_answer(data, question['id'], answer_content)
                    save_data(data)
                    
                    st.success("✅ 답변이 등록되었습니다!")
                    
                    # 포인트 획득 알림
                    user = get_current_user()
                    if user:
                        st.info(f"🎉 {user['nickname']}님이 100포인트를 획득하셨습니다!")
                    
                    # 답변 입력 필드 초기화를 위해 세션 상태 키 삭제
                    answer_key = f"answer_content_{question['id']}"
                    if answer_key in st.session_state:
                        del st.session_state[answer_key]
                    
                    time.sleep(1)
                    st.rerun()
        
        # 질문 사이 최소 간격만 유지 - 구분선 제거
        if i < len(questions) - 1:
            st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
        else:
            # 마지막 질문 후 여백
            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

def show_my_activity_tab(data: Dict):
    """나의 활동 탭"""
    st.markdown("## 📊 나의 활동 현황")
    
    user = get_current_user()
    if not user:
        st.error("사용자 정보를 불러올 수 없습니다.")
        return
    
    # username = user['nickname']  # 미사용 변수 제거
    user_id = user['user_id']
    
    # 활동 통계
    my_questions = [q for q in data["questions"] if q.get("author_id") == user_id]
    my_answers = [a for a in data["answers"] if a.get("author_id") == user_id]
    
    # 통계 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🙋‍♂️ 내 질문", len(my_questions))
    
    with col2:
        st.metric("💬 내 답변", len(my_answers))
    
    with col3:
        # 내 답변에 받은 좋아요 수
        total_likes = 0
        for answer in my_answers:
            like_key = f"answer_{answer['id']}"
            likes = data.get("likes", {}).get(like_key, [])
            total_likes += len(likes)
        st.metric("❤️ 받은 좋아요", total_likes)
    
    with col4:
        # 포인트 계산
        total_points = len(my_questions) * 100 + len(my_answers) * 100
        st.metric("🏆 획득 포인트", total_points)
    
    st.divider()
    
    # 내 질문 목록
    if my_questions:
        st.markdown("### 🙋‍♂️ 내가 작성한 질문")
        
        for question in sorted(my_questions, key=lambda x: x["timestamp"], reverse=True):
            with st.expander(f"{question['title']} ({question['timestamp']})", expanded=False):
                st.markdown(f"**카테고리**: {question['category']}")
                st.markdown(f"**내용**: {question['content']}")
                
                # 이 질문에 대한 답변 수
                question_answers = [a for a in data["answers"] if a["question_id"] == question["id"]]
                st.markdown(f"**답변 수**: {len(question_answers)}개")
    
    st.divider()
    
    # 내 답변 목록
    if my_answers:
        st.markdown("### 💬 내가 작성한 답변")
        
        for answer in sorted(my_answers, key=lambda x: x["timestamp"], reverse=True):
            # 해당 질문 찾기
            question = next((q for q in data["questions"] if q["id"] == answer["question_id"]), None)
            
            if question:
                with st.expander(f"Re: {question['title']} ({answer['timestamp']})", expanded=False):
                    st.markdown(f"**원본 질문**: {question['title']}")
                    st.markdown(f"**내 답변**: {answer['content']}")
                    
                    # 이 답변에 받은 좋아요
                    like_key = f"answer_{answer['id']}"
                    likes = data.get("likes", {}).get(like_key, [])
                    st.markdown(f"**받은 좋아요**: ❤️ {len(likes)}개")

# ====================================
# 🚀 앱 실행
# ====================================

if __name__ == "__main__":
    main()