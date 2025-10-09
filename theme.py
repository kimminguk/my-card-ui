"""
======================================================================
AE WIKI 공통 다크 테마 모듈 (theme.py)
======================================================================

📋 파일 역할:
- Streamlit 애플리케이션 전체에 일관된 다크 테마 UI 제공
- 모든 페이지에서 공통으로 사용하는 CSS 스타일 중앙집중 관리
- 브랜드 컬러와 디자인 시스템 통합으로 전문적인 UX 구현

🎨 주요 기능:
- 다크 모드 기반 그라데이션 배경 (파란색 계열)
- 모든 Streamlit 컴포넌트 다크 테마 적용 (입력필드, 버튼, 사이드바 등)
- 반투명 효과와 백드롭 필터로 현대적 UI 구현
- 마우스 호버 애니메이션과 그림자 효과

🔗 연동 관계:
- 호출: 모든 페이지 파일에서 apply_dark_theme() 함수 호출
- 설정: config.py의 THEME_CONFIG에서 색상 팔레트 참조
- 적용: st.markdown(unsafe_allow_html=True)로 CSS 주입
"""

def get_dark_theme_css():
    """
    🎨 다크 테마 CSS 스타일 반환 함수
    
    AE WIKI 전용 다크 테마 CSS를 문자열로 반환합니다.
    Streamlit의 모든 컴포넌트에 일관된 다크 모드 스타일을 적용하며,
    브랜드 컬러(#667eea)와 그라데이션 효과를 통해 전문적인 UI를 구현합니다.
    
    📊 적용 범위:
    - 기본 앱 배경과 레이아웃
    - 모든 입력 필드 (텍스트, 숫자, 파일업로드 등)
    - 버튼과 다운로드 버튼
    - 사이드바와 툴바
    - 탭, 폼, 메시지 박스
    - 데이터프레임과 차트
    
    Returns:
        str: 완전한 CSS 스타일 문자열 (<style> 태그 포함)
    """
    return """
<style>
/* 🌙 다크모드 기본 설정 */
.stApp {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #ffffff;
}

.main .block-container {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    padding: 2rem;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 입력 필드 다크모드 스타일 */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px;
}

.stTextInput > div > div > input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 10px rgba(102, 126, 234, 0.3) !important;
}

.stTextInput > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 텍스트 영역 다크모드 */
.stTextArea > div > div > textarea {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px;
}

.stTextArea > div > div > textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 10px rgba(102, 126, 234, 0.3) !important;
}

.stTextArea > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 셀렉트박스 다크모드 */
.stSelectbox > div > div > div {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
}

.stSelectbox > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 넘버 입력 다크모드 */
.stNumberInput > div > div > input {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px;
}

.stNumberInput > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 파일 업로더 다크모드 */
.stFileUploader > div > div > div {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px;
}

.stFileUploader > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 슬라이더 다크모드 */
.stSlider > div > div > div {
    background: rgba(255, 255, 255, 0.1) !important;
}

.stSlider > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 체크박스 다크모드 */
.stCheckbox > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 라디오 버튼 다크모드 */
.stRadio > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 멀티셀렉트 다크모드 */
.stMultiSelect > div > div > div {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
}

.stMultiSelect > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 버튼 스타일 */
.stButton > button {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* 다운로드 버튼 */
.stDownloadButton > button {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 5px;
}

.stTabs [data-baseweb="tab"] {
    color: #ffffff;
    background: transparent;
    border-radius: 8px;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
}

/* 폼 스타일 */
.stForm {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 메시지 박스 스타일 */
.stAlert {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 8px;
}

.stSuccess {
    background: rgba(34, 197, 94, 0.2) !important;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

.stError {
    background: rgba(239, 68, 68, 0.2) !important;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.stInfo {
    background: rgba(59, 130, 246, 0.2) !important;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

.stWarning {
    background: rgba(245, 158, 11, 0.2) !important;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Expander 스타일 */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 8px;
}

.streamlit-expanderContent {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 0 0 8px 8px;
}

/* 사이드바 스타일 */
.css-1d391kg {
    background: rgba(26, 26, 46, 0.9) !important;
    backdrop-filter: blur(10px);
}

.css-1wy4zb1 {
    background: rgba(26, 26, 46, 0.9) !important;
}

section[data-testid="stSidebar"] {
    background: rgba(26, 26, 46, 0.9) !important;
    backdrop-filter: blur(10px);
}

/* 헤더 텍스트 스타일 */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

/* 일반 텍스트 */
p, div, span, label {
    color: #ffffff !important;
}

/* 데이터프레임 스타일 */
.dataframe {
    background: rgba(255, 255, 255, 0.05) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

.dataframe th {
    background: rgba(102, 126, 234, 0.3) !important;
    color: #ffffff !important;
}

.dataframe td {
    background: rgba(255, 255, 255, 0.05) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* 메트릭 스타일 */
[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 1rem;
}

[data-testid="metric-container"] > div {
    color: #ffffff !important;
}

/* 차트 컨테이너 */
.js-plotly-plot {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 8px;
}

/* 프로그레스 바 */
.stProgress > div > div {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
}

/* 🔧 상단 툴바 다크모드 */
.stAppToolbar {
    background: rgba(26, 26, 46, 0.9) !important;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.stAppToolbar button {
    color: #ffffff !important;
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
}

.stAppToolbar button:hover {
    background: rgba(255, 255, 255, 0.2) !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.stAppToolbar svg {
    color: #ffffff !important;
}

/* 메인 메뉴 버튼 */
.stMainMenu button {
    background: rgba(255, 255, 255, 0.1) !important;
    border-radius: 50%;
    padding: 8px;
}

.stMainMenu button:hover {
    background: rgba(102, 126, 234, 0.3) !important;
}

/* Deploy 버튼 */
.stAppDeployButton button {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    font-weight: 600;
}

.stAppDeployButton button:hover {
    background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 3px 12px rgba(102, 126, 234, 0.4);
}

/* 캡션 텍스트 */
.caption {
    color: rgba(255, 255, 255, 0.7) !important;
}

/* JSON 텍스트 */
.stJson {
    background: rgba(255, 255, 255, 0.05) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

/* 코드 블록 */
.stCode {
    background: rgba(255, 255, 255, 0.05) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

/* 스피너 */
.stSpinner > div {
    border-color: #667eea !important;
}

/* 토글 버튼 */
.stToggle > label {
    color: #ffffff !important;
}

/* 날짜 입력 */
.stDateInput > label {
    color: #ffffff !important;
    font-weight: 500;
}

.stDateInput > div > div > input {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px;
}

/* 시간 입력 */
.stTimeInput > label {
    color: #ffffff !important;
    font-weight: 500;
}

.stTimeInput > div > div > input {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px;
}

/* 색상 선택 */
.stColorPicker > label {
    color: #ffffff !important;
    font-weight: 500;
}

/* 페이지 로드 애니메이션 */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.main .block-container {
    animation: fadeInUp 0.6s ease-out;
}
</style>
"""

def apply_dark_theme():
    """
    🌙 다크 테마 적용 함수
    
    Streamlit 애플리케이션에 다크 테마 CSS를 주입합니다.
    모든 페이지에서 호출하여 일관된 UI 스타일을 보장합니다.
    
    동작 과정:
    1. get_dark_theme_css()에서 CSS 문자열 획득
    2. st.markdown()으로 HTML/CSS 주입
    3. unsafe_allow_html=True로 CSS 스타일 활성화
    
    ⚠️ 주의사항:
    - 페이지 로드 시 가장 먼저 호출해야 함
    - CSS가 전체 앱에 전역적으로 적용됨
    - 다른 CSS와 충돌 가능성 있음
    """
    import streamlit as st  # Streamlit 라이브러리 임포트
    st.markdown(get_dark_theme_css(), unsafe_allow_html=True)  # CSS 스타일 주입