"""
=================================================================
📄 AE WIKI - 홈페이지 (🏠_Home.py)
=================================================================

📋 파일 역할:
- AE WIKI 시스템의 메인 대시보드 페이지
- 사용자 로그인 후 첫 화면, 전체 시스템 허브 역할
- 주요 서비스 소개, 빠른 액션, 최근 활동 피드 제공

🔗 주요 컴포넌트:
- 빠른 액션 버튼 (6개): 자주 사용하는 기능 원클릭 접근
- 최근 활동 피드: 내 질문 답변, 좋아요, 인기 질문, 시스템 업데이트
- Best Contributor: 포인트 기반 TOP 3 사용자 랭킹
- 서비스 카드: 4개 주요 챗봇 + 부가 서비스 소개

📊 입출력 데이터:
- 입력: 사용자 로그인 세션, 활동 데이터 (questions.json, answers.json, likes 등)
- 출력: 개인화된 대시보드 UI, 다른 페이지로의 네비게이션

🔄 연동 관계:
- utils.py: 사용자 인증, 데이터 초기화, CSS 스타일 로딩
- config.py: 앱 설정값 (제목, 아이콘, 레이아웃 등)
- 모든 페이지: 사이드바 네비게이션을 통한 페이지 전환

⚡ 처리 흐름:
사용자 접속 -> 로그인 확인 -> 개인 활동 데이터 로딩 -> 대시보드 렌더링 
-> 빠른 액션/최근 활동 표시 -> 사이드바 설정
"""

# 실행 방법: streamlit run 🏠_Home.py

import streamlit as st

from config import APP_CONFIG
from utils import (
    load_css_styles, require_login, get_current_user, logout_user, initialize_session_state,
    initialize_data, get_user_points_ranking, check_session_validity,
    resolve_user_label
)

# ====================================
# 🎨 페이지 설정 및 스타일
# ====================================

st.set_page_config(
    page_title=APP_CONFIG["page_title"],
    page_icon=APP_CONFIG["page_icon"],
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["initial_sidebar_state"]
)

# 다크 테마 적용
from theme import apply_dark_theme
apply_dark_theme()

# 전역 애니메이션 및 시각적 개선 CSS
st.markdown("""
<style>
/* 페이지 로딩 애니메이션 */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

@keyframes shimmer {
    0% { background-position: -200px 0; }
    100% { background-position: calc(200px + 100%) 0; }
}

/* 메인 컨테이너 애니메이션 */
.stApp > div > div > div > div {
    animation: fadeInUp 0.8s ease-out;
}

/* 버튼 호버 효과 개선 */
.stButton > button {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
    filter: brightness(110%) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* 카드 호버 효과 */
div[style*="background: linear-gradient"] {
    transition: all 0.4s ease !important;
    cursor: pointer !important;
}

div[style*="background: linear-gradient"]:hover {
    transform: translateY(-5px) scale(1.02) !important;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2) !important;
    filter: brightness(110%) !important;
}

/* 성공/정보 메시지 애니메이션 */
.stSuccess, .stInfo, .stWarning, .stError {
    animation: fadeInUp 0.6s ease-out !important;
}

/* 로딩 스피너 개선 */
.stSpinner {
    animation: pulse 2s infinite ease-in-out !important;
}

/* 텍스트 그라데이션 효과 */
.gradient-text {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: bold;
}

/* 반짝이는 효과 */
.shimmer {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200px 100%;
    animation: shimmer 2s infinite;
}

/* 사이드바 개선 */
.css-1d391kg {
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1) !important;
}

/* 스크롤바 스타일링 */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2, #667eea);
}

/* 토글 스위치 개선 */
.stCheckbox > div {
    padding: 0.5rem !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}

.stCheckbox > div:hover {
    background-color: rgba(102, 126, 234, 0.1) !important;
}

/* 선택박스 개선 */
.stSelectbox > div > div {
    border-radius: 10px !important;
    border: 2px solid #e0e0e0 !important;
    transition: all 0.3s ease !important;
}

.stSelectbox > div > div:focus-within {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* 입력창 개선 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 10px !important;
    border: 2px solid #e0e0e0 !important;
    transition: all 0.3s ease !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* 메트릭 카드 애니메이션 */
.metric-card {
    animation: fadeInUp 0.8s ease-out;
    transition: transform 0.3s ease;
}

.metric-card:hover {
    transform: scale(1.05);
}

/* 페이지 전환 효과 */
.stApp {
    transition: all 0.3s ease !important;
}

/* 테이블 개선 */
.stDataFrame {
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

/* 알림 배지 효과 */
.notification-badge {
    animation: pulse 2s infinite;
    background: linear-gradient(45deg, #ff6b6b, #ee5a24);
    border-radius: 50%;
    color: white;
    font-size: 0.8rem;
    padding: 0.2rem 0.5rem;
    position: absolute;
    top: -5px;
    right: -5px;
}
</style>
""", unsafe_allow_html=True)

# ====================================
# 🚀 빠른 액션 버튼 시스템
# ====================================

def show_quick_actions():
    """
    🎯 목적: 사용자가 자주 사용하는 6개 기능에 원클릭으로 접근할 수 있는 대시보드 제공
    
    📊 입력: 
    - st.session_state의 사용자 로그인 정보
    - data (questions, answers, likes 등 활동 데이터)
    
    📤 출력:
    - 6개의 그라데이션 카드 UI (2행 3열)
    - 각 카드 클릭 시 해당 페이지로 이동
    
    🔄 부작용:
    - st.session_state.show_detailed_activity 설정 (내 활동 현황 버튼)
    - st.switch_page() 호출로 페이지 전환
    
    📞 호출 관계:
    - 호출자: show_home_dashboard() -> show_quick_actions()
    - 호출 대상: get_current_user(), initialize_data()
    
    🎨 UI 이벤트:
    - '질문 작성하기' 버튼 -> pages/6_📚_AE Help Desk.py
    - '활동 상세보기' 버튼 -> 사이드바 상세 활동 내역 펼치기
    - '용어 등록하기' 버튼 -> pages/5_✨WIKI_학습시키기.py
    - '포인트 상세' 버튼 -> 포인트 내역 팝업 표시
    - '챗봇 둘러보기' 버튼 -> 챗봇 목록 정보 팝업
    - '자료 기여하기' 버튼 -> pages/5_✨WIKI_학습시키기.py
    
    📊 데이터 흐름:
    사용자 데이터 조회 -> 개인 활동 통계 계산 -> 카드별 정보 표시 -> 버튼 클릭 이벤트 처리
    """
    st.markdown("## ⚡ 빠른 액션")
    
    # STEP 1: 사용자 인증 및 데이터 로딩
    # 현재 로그인된 사용자 정보와 전체 시스템 데이터를 가져옴
    user = get_current_user()  # utils.py에서 세션 상태 기반으로 사용자 정보 반환
    data = initialize_data()   # 모든 질문, 답변, 좋아요 데이터 로딩 (JSON 파일들)
    
    # 로그인된 사용자만 빠른 액션 버튼을 볼 수 있음
    if user:
        # STEP 2: 개인 식별 정보 추출
        user_id = user['user_id']      # 내부 사용자 ID (데이터 필터링용)
        nickname = user['nickname']    # 화면 표시용 닉네임
        
        # STEP 3: 개인 활동 통계 계산
        # 내가 작성한 질문들만 필터링 (author_id로 구분)
        my_questions = [q for q in data["questions"] if q.get("author_id") == user_id]
        # 내가 작성한 답변들만 필터링
        my_answers = [a for a in data["answers"] if a.get("author_id") == user_id]
        
        # TODO: 실제 "새" 답변을 구분하는 로직 필요 (현재는 전체 답변 수만 계산)
        # 향후 timestamp 기반으로 마지막 확인 시점 이후 답변만 카운트 필요
        new_answers_count = 0
        for question in my_questions:
            question_answers = [a for a in data["answers"] if a["question_id"] == question["id"]]
            new_answers_count += len(question_answers)
        
        # STEP 4: UI 레이아웃 구성 - 2행 3열 그리드
        # 첫 번째 행: 3개 카드
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 카드 1: 빠른 질문하기 (파란색 그라데이션)
            # 용도: 팀원에게 물어보기 페이지로 즉시 이동, 질문 작성 시작
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       padding: 1.5rem; border-radius: 15px; text-align: center; 
                       box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                       transition: transform 0.3s ease; margin-bottom: 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🚀</div>
                <h4 style="color: white; margin-bottom: 0.5rem;">📕 AE팀에게 질문하기</h4>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;">
                    팀원에게 바로 질문을 작성하세요
                </p>
            </div>
            """, unsafe_allow_html=True)

            # 🎨 UI 이벤트: 질문 작성 버튼 클릭
            # 목적: 팀원에게 물어보기 페이지로 이동하여 질문 작성 화면 바로 표시
            # 연결: st.switch_page() -> pages/6_📕_AE팀에게 질문하기.py
            if st.button("질문 작성하기", key="quick_question", use_container_width=True):
                st.switch_page("pages/6_📚_AE Help Desk.py")
        
        with col2:
            # 포인트 현황
            total_points = len(my_questions) * 100 + len(my_answers) * 100
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%); 
                       padding: 1.5rem; border-radius: 15px; text-align: center; 
                       box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
                       transition: transform 0.3s ease; margin-bottom: 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💎</div>
                <h4 style="color: white; margin-bottom: 0.5rem;">내 포인트</h4>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;">
                    현재 {total_points:,}P 보유 중
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("포인트 상세", key="point_details", use_container_width=True):
                st.info(f"""
                **🏆 {nickname}님의 포인트 내역**
                
                • 질문하기: {len(my_questions)} × 100P = {len(my_questions) * 100:,}P
                • 답변하기: {len(my_answers)} × 100P = {len(my_answers) * 100:,}P
                
                **총 획득 포인트: {total_points:,}P**
                
                💡 더 많은 활동으로 포인트를 모아보세요!
                """)
        
        with col3:
            # 학습 요청 현황
            st.markdown("""
            <div style="background: linear-gradient(135deg, #17a2b8 0%, #6610f2 100%); 
                       padding: 1.5rem; border-radius: 15px; text-align: center; 
                       box-shadow: 0 4px 15px rgba(23, 162, 184, 0.3);
                       transition: transform 0.3s ease; margin-bottom: 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📚</div>
                <h4 style="color: white; margin-bottom: 0.5rem;">자료 학습시키기</h4>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;">
                    WIKI를 더 똑똑하게!
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("자료 기여하기", key="contribute", use_container_width=True):
                st.switch_page("pages/5_✨WIKI_학습시키기.py")
    
    st.divider()

# ====================================
# 📡 최근 활동 피드 시스템
# ====================================

def show_recent_activity_feed():
    """
    🎯 목적: 사용자 개인화된 최근 활동들을 타임라인 형태로 표시하는 피드 시스템
    
    📊 입력:
    - st.session_state의 사용자 로그인 정보
    - data (questions.json, answers.json, likes.json 등)
    
    📤 출력:
    - 4가지 타입의 활동 카드들 (2열 레이아웃)
    - 최대 8개까지 최신 활동 표시
    
    🔄 부작용: 없음 (순수한 표시 함수)
    
    📞 호출 관계:
    - 호출자: show_home_dashboard() -> show_recent_activity_feed()
    - 호출 대상: get_current_user(), initialize_data(), show_activity_card()
    
    🎨 활동 타입별 카드 색상:
    - 💬 새 답변: 파란색 그라데이션 (#e3f2fd -> #bbdefb)
    - ❤️ 받은 좋아요: 핑크색 그라데이션 (#fce4ec -> #f8bbd9)  
    - 🔥 인기 질문: 주황색 그라데이션 (#fff3e0 -> #ffcc02)
    - 🔔 시스템 업데이트: 초록색 그라데이션 (#e8f5e8 -> #c8e6c9)
    
    📊 데이터 흐름:
    사용자 데이터 조회 -> 4가지 활동 타입별 데이터 수집 -> timestamp 기준 정렬 
    -> 최신 8개 선택 -> 2열 카드 레이아웃으로 표시
    """
    st.markdown("## 📡 최근 활동")
    
    user = get_current_user()
    data = initialize_data()
    
    if user:
        user_id = user['user_id']
        nickname = user['nickname']
        
        # 활동 데이터 수집
        activities = []
        
        # 1. 내 질문에 달린 새 답변들
        my_questions = [q for q in data["questions"] if q.get("author_id") == user_id]
        for question in my_questions[-3:]:  # 최근 3개 질문만
            question_answers = [a for a in data["answers"] if a["question_id"] == question["id"]]
            for answer in question_answers[-2:]:  # 질문당 최근 2개 답변
                activities.append({
                    "type": "new_answer",
                    "timestamp": answer["timestamp"],
                    "data": {
                        "question_title": question["title"],
                        "answer_author": answer["author"],
                        "answer_preview": answer["content"][:100] + "..." if len(answer["content"]) > 100 else answer["content"]
                    }
                })
        
        # 2. 내 답변에 받은 좋아요들  
        my_answers = [a for a in data["answers"] if a.get("author_id") == user_id]
        for answer in my_answers[-5:]:  # 최근 5개 답변 확인
            like_key = f"answer_{answer['id']}"
            likes = data.get("likes", {}).get(like_key, [])
            if likes:
                question = next((q for q in data["questions"] if q["id"] == answer["question_id"]), None)
                if question:
                    activities.append({
                        "type": "received_likes", 
                        "timestamp": answer["timestamp"],
                        "data": {
                            "question_title": question["title"],
                            "likes_count": len(likes),
                            "answer_preview": answer["content"][:80] + "..." if len(answer["content"]) > 80 else answer["content"]
                        }
                    })
        
        # 3. 인기 질문들 (전체 사용자 대상)
        for question in data["questions"][-10:]:  # 최근 10개 질문 중
            question_answers = [a for a in data["answers"] if a["question_id"] == question["id"]]
            if len(question_answers) >= 2:  # 답변이 2개 이상인 질문
                activities.append({
                    "type": "popular_question",
                    "timestamp": question["timestamp"],
                    "data": {
                        "question_title": question["title"],
                        "author": question["author"],
                        "answers_count": len(question_answers),
                        "category": question.get("category", "일반")
                    }
                })
        
        # 4. 시스템 업데이트 (가상 데이터)
        activities.append({
            "type": "system_update",
            "timestamp": "2025-09-01 22:00:00",
            "data": {
                "title": "🆕 JEDEC SPEC 챗봇 성능 개선",
                "description": "JEDEC 표준 문서 검색 정확도가 30% 향상되었습니다!"
            }
        })
        
        activities.append({
            "type": "system_update", 
            "timestamp": "2025-09-01 18:00:00",
            "data": {
                "title": "✨ 용어집 데이터베이스 업데이트",
                "description": "새로운 반도체 기술 용어 150개가 추가되었습니다."
            }
        })
        
        # 시간순 정렬 (최신순)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 활동 피드 표시 (최대 8개)
        if activities:
            col1, col2 = st.columns(2)
            
            for i, activity in enumerate(activities[:8]):
                with col1 if i % 2 == 0 else col2:
                    show_activity_card(activity, nickname)
        else:
            st.info("💡 아직 활동이 없습니다. 질문하기나 답변하기로 첫 활동을 시작해보세요!")
    
    st.divider()

def show_activity_card(activity, current_nickname):
    """개별 활동 카드 표시"""
    
    if activity["type"] == "new_answer":
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                   padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem;
                   border-left: 4px solid #2196f3;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">💬</span>
                <strong style="color: #1976d2;">새 답변이 달렸습니다!</strong>
            </div>
            <p style="margin: 0.3rem 0; color: #424242; font-size: 0.9rem;">
                <strong>질문:</strong> {activity["data"]["question_title"][:50]}{"..." if len(activity["data"]["question_title"]) > 50 else ""}
            </p>
            <p style="margin: 0.3rem 0; color: #666; font-size: 0.85rem;">
                <strong>{activity["data"]["answer_author"]}</strong>님이 답변했습니다
            </p>
            <p style="margin: 0.3rem 0; color: #757575; font-size: 0.8rem;">
                {activity["data"]["answer_preview"]}
            </p>
            <small style="color: #999;">{activity["timestamp"]}</small>
        </div>
        """, unsafe_allow_html=True)
        
    elif activity["type"] == "received_likes":
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fce4ec 0%, #f8bbd9 100%); 
                   padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem;
                   border-left: 4px solid #e91e63;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">❤️</span>
                <strong style="color: #c2185b;">답변에 좋아요 {activity["data"]["likes_count"]}개!</strong>
            </div>
            <p style="margin: 0.3rem 0; color: #424242; font-size: 0.9rem;">
                <strong>질문:</strong> {activity["data"]["question_title"][:50]}{"..." if len(activity["data"]["question_title"]) > 50 else ""}
            </p>
            <p style="margin: 0.3rem 0; color: #757575; font-size: 0.8rem;">
                "{activity["data"]["answer_preview"]}"
            </p>
            <small style="color: #999;">{activity["timestamp"]}</small>
        </div>
        """, unsafe_allow_html=True)
        
    elif activity["type"] == "popular_question":
        if activity["data"]["author"] != current_nickname:  # 내 질문이 아닌 경우만 표시
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffcc02 100%); 
                       padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem;
                       border-left: 4px solid #ff9800;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem; margin-right: 0.5rem;">🔥</span>
                    <strong style="color: #ef6c00;">인기 질문</strong>
                </div>
                <p style="margin: 0.3rem 0; color: #424242; font-size: 0.9rem;">
                    <strong>{activity["data"]["question_title"]}</strong>
                </p>
                <p style="margin: 0.3rem 0; color: #666; font-size: 0.85rem;">
                    📂 {activity["data"]["category"]} • 👤 {activity["data"]["author"]}님
                </p>
                <p style="margin: 0.3rem 0; color: #757575; font-size: 0.8rem;">
                    💬 {activity["data"]["answers_count"]}개의 답변
                </p>
                <small style="color: #999;">{activity["timestamp"]}</small>
            </div>
            """, unsafe_allow_html=True)
            
    elif activity["type"] == "system_update":
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); 
                   padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem;
                   border-left: 4px solid #4caf50;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">🔔</span>
                <strong style="color: #2e7d32;">{activity["data"]["title"]}</strong>
            </div>
            <p style="margin: 0.3rem 0; color: #424242; font-size: 0.9rem;">
                {activity["data"]["description"]}
            </p>
            <small style="color: #999;">{activity["timestamp"]}</small>
        </div>
        """, unsafe_allow_html=True)

# ====================================
# 📢 최근 소식 함수
# ====================================

def show_recent_news():
    """최근 소식 및 업데이트 섹션"""
    st.markdown("## 📢 최근 소식")
    
    # 2열 레이아웃으로 구성
    col1, col2 = st.columns(2)
    
    with col1:
        # 인기 질문 TOP 3
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); 
                   padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;
                   box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);">
            <h4 style="color: white; margin-bottom: 1rem; text-align: center;">🏆 Best Contributor에 도전하세요 🏆</h4>
            <div style="font-size: 0.95rem;">
                <p style="margin: 0.5rem 0; text-align: center; "><strong></strong> </p>
                <p style="margin: 0.5rem 0; text-align: center; "><strong>활동이 쌓일수록 포인트 UP!</strong></p>
                <p style="margin: 0.5rem 0; text-align: center; "><strong></strong> </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # 이번 주 업데이트
        st.markdown("""
        <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); 
                   padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;
                   box-shadow: 0 4px 15px rgba(116, 185, 255, 0.3);">
            <h4 style="color: white; margin-bottom: 1rem; text-align: center;">🎮 미션을 완료하고 포인트를 모아보세요!</h4>
            <div style="font-size: 0.9rem;">
                <p style="margin: 0.4rem 0; text-align: center; ">MISSION 1: 지식 등록하기</strong> 📚 당신의 노하우를 AE PLUS에 학습시켜주세요</p>
                <p style="margin: 0.4rem 0; text-align: center; ">MISSION 2: 질문하기</strong>💬 궁금한 점을 팀원들에게 물어보세요</p>
                <p style="margin: 0.4rem 0; text-align: center; ">MISSION 3: 답변하기</strong>✍️ 팀원들의 질문에 답변을 남겨주세요</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 시스템 공지사항 (전체 너비)
    st.markdown("""
    <div style="background: linear-gradient(135deg, #00b894 0%, #00a085 100%); 
               padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1.5rem;
               box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3); text-align: center;">
        <p style="margin: 0.5rem 0; font-size: 1.1rem;">
            <strong>🙏 여러분의 의견이 큰 힘이 됩니다. 불편함이 있더라도 양해 부탁드리며, 피드백은 언제나 환영합니다! </strong>  
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()

# ====================================
# 🏆 Best Contributor 함수
# ====================================

def show_hall_of_fame():
    """포인트 기반 Best Contributor"""
    data = initialize_data()
    ranking = get_user_points_ranking(data)
    
    if ranking:
        st.markdown("## 🏆 Best Contributor")
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
        
        cols = st.columns(3)
        medals = ["🥇", "🥈", "🥉"]
        colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
        gradients = [
            "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)",
            "linear-gradient(135deg, #C0C0C0 0%, #A0A0A0 100%)", 
            "linear-gradient(135deg, #CD7F32 0%, #8B4513 100%)"
        ]
        
        for i, (username, points) in enumerate(ranking):
            display_name = resolve_user_label(username)
            # ⬅️ 핵심: ID → 닉네임/실명
            if i < 3:
                with cols[i]:
                    # 포인트 기반 카드 형태로 표시
                    st.markdown(
                        f"""
                        <div style="
                            background: {gradients[i]};
                            border: 3px solid {colors[i]};
                            border-radius: 15px;
                            padding: 1.5rem;
                            text-align: center;
                            margin: 10px 0;
                            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                            transform: scale(1.02);
                            color: white;
                        ">
                            <div style="font-size: 3rem; margin-bottom: 0.5rem;">{medals[i]}</div>
                            <h3 style="margin-bottom: 0.5rem; font-weight: bold;">{display_name}</h3>
                            <p style="margin: 0; font-size: 1.2rem; font-weight: 600;">
                                {points:,} 포인트
                            </p>
                            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">
                                지식 공유 챔피언
                            </p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
    else:
        st.markdown("## 🏆 Best Contributor")
        st.info("🎯 아직 포인트를 획득한 사용자가 없습니다. 첫 번째 챔피언이 되어보세요!")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   padding: 1.5rem; border-radius: 10px; color: white; text-align: center; margin: 1rem 0;">
            <h4>💡 포인트 획득 방법</h4>
            <p style="margin: 0.5rem 0;">
                • 질문하기: <strong>100 포인트</strong><br>
                • 답변하기: <strong>100 포인트</strong><br>
                • WIKI 학습 자료 제공: <strong>100 포인트</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()

# ====================================
# 🎯 메인 진입점 함수
# ====================================

def main():
    """
    🎯 목적: AE WIKI 홈페이지의 메인 실행 함수, 전체 페이지 렌더링 담당
    
    📊 입력: 없음 (Streamlit 웹 요청)
    📤 출력: 완성된 홈페이지 UI
    
    🔄 부작용:
    - st.session_state에 사용자 인증 및 앱 상태 정보 저장
    - 로그인 페이지로 리다이렉트 가능 (미인증 시)
    
    📞 호출 관계:
    - 호출자: Streamlit 앱 엔트리포인트 (__name__ == "__main__")
    - 호출 대상: initialize_session_state(), require_login(), setup_sidebar(), show_home_dashboard()
    
    ⚡ 처리 흐름:
    세션 초기화 -> 로그인 검증 -> 사이드바 설정 -> 메인 대시보드 표시
    """
    
    # STEP 1: 세션 상태 초기화
    # Streamlit의 st.session_state에 앱 전역 상태 설정 (사용자 정보, 설정값 등)
    initialize_session_state()  # utils.py의 함수, 기본값 설정 및 상태 복원
    
    # STEP 1.5: 세션 유효성 검사 및 자동 연장
    # 로그인된 사용자의 세션 유효기간을 확인하고 자동으로 연장
    check_session_validity()
    
    # STEP 2: 사용자 인증 확인
    # 로그인하지 않은 사용자는 로그인 페이지로 자동 리다이렉트
    if not require_login():  # utils.py의 함수, False 반환 시 이미 리다이렉트 처리됨
        return  # 미인증 사용자는 여기서 종료 (로그인 페이지로 이동됨)
    
    # STEP 3: 사이드바 UI 구성
    # 사용자 정보, 네비게이션 등
    setup_sidebar()
    
    # STEP 4: 메인 콘텐츠 영역 렌더링
    # 빠른 액션, 최근 활동, Best Contributor, 서비스 소개 등
    show_home_dashboard()

def setup_sidebar():
    """공통 사이드바 설정"""
    with st.sidebar:
        # 사용자 정보 섹션
        st.markdown("### 👤 사용자 정보")
        
        user = get_current_user()
        if user:
            # 로그인된 사용자 정보 표시
            st.success(f"👋 **{user['nickname']}**님 환영합니다!")
            
            with st.expander("ℹ️ 내 정보", expanded=False):
                st.markdown(f"**녹스아이디**: {user['knox_id']}")
                st.markdown(f"**닉네임**: {user['nickname']}")
                st.markdown(f"**소속부서**: {user['department']}")
                if user.get('created_at'):
                    st.markdown(f"**등록일**: {user['created_at'].split()[0]}")
                if user.get('last_login'):
                    st.markdown(f"**마지막 로그인**: {user['last_login']}")
                
                st.divider()
                
                # 내 활동 현황 추가
                show_user_activity_summary(user)
            
            # 로그아웃 버튼
            if st.button("🚪 로그아웃", use_container_width=True):
                logout_user()
                st.rerun()
        
# REMOVED: 개인 설정 및 즐겨찾기 기능 - 사용자 요청으로 제거
        
        # 응답 속도 설정 - 백엔드 설정 (프론트엔드 숨김)
        # 기본값 설정
        if 'response_speed' not in st.session_state:
            st.session_state.response_speed = 'fast'
        if 'typing_enabled' not in st.session_state:
            st.session_state.typing_enabled = True
        
        st.divider()

def show_user_activity_summary(user):
    """사용자 활동 요약 표시"""
    data = initialize_data()
    user_id = user['user_id']
    
    st.markdown("**📊 나의 활동 현황**")
    
    # 활동 통계
    my_questions = [q for q in data["questions"] if q.get("author_id") == user_id]
    my_answers = [a for a in data["answers"] if a.get("author_id") == user_id]
    
    # 통계 카드
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🙋‍♂️ 내 질문", len(my_questions))
        st.metric("💬 내 답변", len(my_answers))
    
    with col2:
        # 내 답변에 받은 좋아요 수
        total_likes = 0
        for answer in my_answers:
            like_key = f"answer_{answer['id']}"
            likes = data.get("likes", {}).get(like_key, [])
            total_likes += len(likes)
        st.metric("❤️ 받은 좋아요", total_likes)
        
        # 포인트 계산
        total_points = len(my_questions) * 100 + len(my_answers) * 100
        st.metric("🏆 획득 포인트", total_points)
    
    if st.button("📋 상세 활동 내역 보기", use_container_width=True):
        st.session_state.show_detailed_activity = True
        
    # 상세 활동 내역
    if st.session_state.get('show_detailed_activity', False):
        st.markdown("---")
        st.markdown("**📋 상세 활동 내역**")
        
        # 최근 질문 3개
        if my_questions:
            st.markdown("**🙋‍♂️ 최근 질문 (최대 3개)**")
            recent_questions = sorted(my_questions, key=lambda x: x["timestamp"], reverse=True)[:3]
            for question in recent_questions:
                question_answers = [a for a in data["answers"] if a["question_id"] == question["id"]]
                st.markdown(f"• {question['title']} ({len(question_answers)}개 답변) - {question['timestamp']}")
        
        # 최근 답변 3개
        if my_answers:
            st.markdown("**💬 최근 답변 (최대 3개)**")
            recent_answers = sorted(my_answers, key=lambda x: x["timestamp"], reverse=True)[:3]
            for answer in recent_answers:
                question = next((q for q in data["questions"] if q["id"] == answer["question_id"]), None)
                if question:
                    like_key = f"answer_{answer['id']}"
                    likes = data.get("likes", {}).get(like_key, [])
                    st.markdown(f"• Re: {question['title']} (❤️{len(likes)}) - {answer['timestamp']}")
        
        if st.button("🔼 접기"):
            st.session_state.show_detailed_activity = False
            st.rerun()

    

def show_navigation_menu():
    """페이지 네비게이션 메뉴"""
    st.markdown("### 📋 페이지 메뉴")
    
    # 메뉴 항목들 (관리자 페이지 제외) - 큰 글자와 이모지로 개선
    # REMOVED: 🏢 행정 챗봇 - 사용자 요청으로 완전 제거
    menu_items = [
        {"name": "🏠 홈페이지", "page": "🏠_Home.py", "key": "home"},
        {"name": "❓ 질문하기", "page": "pages/4_질문하기.py", "key": "question"},
        {"name": "💬 답변하기", "page": "pages/5_답변하기.py", "key": "answer"},
        {"name": "🔍 질문 검색", "page": "pages/6_질문_검색.py", "key": "search"}
    ]
    
    # 메뉴 버튼 스타일 개선
    st.markdown("""
    <style>
    div[data-testid="stSidebar"] button {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        padding: 0.9rem 1.2rem !important;
        margin: 0.4rem 0 !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stSidebar"] button:hover {
        transform: translateX(3px) !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 메뉴 버튼들
    for item in menu_items:
        if st.button(item['name'], key=f"nav_{item['key']}", use_container_width=True):
            if item["key"] == "home":
                st.switch_page("🏠_Home.py")
            else:
                st.switch_page(item["page"])

def show_home_dashboard():
    """홈 대시보드 메인 콘텐츠"""
    
    # 메인 헤더
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1 style="color: #667eea; font-size: 3rem; margin-bottom: 0.5rem;">🧠 AE PLUS</h1>
        <p style="font-size: 1.5rem; color: #888; margin-bottom: 0.5rem;">Application Engineering Knowledge Hub</p>
        <p style="font-size: 1.1rem; color: #aaa;">AE 업무 지식의 모든 것</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사용자 환영 메시지
    user = get_current_user()
    if user:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                   padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; color: white;">
            <h3>안녕하세요, <strong>{user['nickname']}</strong>님! 👋</h3>
            <p style="margin-bottom: 0; opacity: 0.9;">오늘도 새로운 지식을 탐험해보세요!</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Best Contributor 섹션
    show_hall_of_fame()
    
    # 최근 소식 섹션
    show_recent_news()
    
    # 빠른 액션 버튼 섹션
    show_quick_actions()
    
    # 최근 활동 피드 섹션
    show_recent_activity_feed()
    
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 2rem 0;">
        <p><strong>AE PLUS</strong> - 함께 만들어가는 지식 공유 플랫폼</p>
        <p style="font-size: 0.9rem;">궁금한 점이나 개선사항이 있으시면 언제든 VOC를 통해 문의해주세요 🙂</p>
    </div>
    """, unsafe_allow_html=True)



# ====================================
# 🚀 앱 실행
# ====================================

if __name__ == "__main__":
    main()