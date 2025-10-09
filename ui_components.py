"""
=================================================================
🎨 AE WIKI - UI 컴포넌트 모듈 (ui_components.py)
=================================================================

📋 파일 역할:
- UI 컴포넌트 및 스타일 관리
- 타이핑 효과 및 동적 UI
- CSS 스타일링 시스템

🔗 주요 컴포넌트:
- 타이핑 효과 함수
- CSS 스타일 로더
- 동적 UI 헬퍼 함수
"""

import streamlit as st
import time
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

def display_typing_effect(text: str, container, delay: float = None) -> None:
    """
    🎯 목적: 타이핑 효과로 텍스트를 순차적으로 표시

    📊 입력:
    - text (str): 표시할 텍스트
    - container: Streamlit 컨테이너 객체
    - delay (float): 문자당 지연 시간 (초)

    🔄 처리 흐름:
    1. 기본 지연 시간 설정
    2. 문자별 순차 표시
    3. 실시간 UI 업데이트
    """

    if delay is None:
        delay = 0.05  # 기본 지연 시간: 50ms

    # 빈 문자열로 시작
    displayed_text = ""

    # 각 문자를 순차적으로 추가하며 표시
    for char in text:
        displayed_text += char
        container.markdown(displayed_text)
        time.sleep(delay)

def load_css_styles() -> str:
    """
    🎯 목적: AE WIKI 전용 CSS 스타일 로드

    📤 출력:
    - str: CSS 스타일 문자열

    🎨 스타일 포함 요소:
    - 다크 테마 기본 설정
    - 버튼 및 입력 요소 스타일
    - 그라데이션 및 애니메이션
    - 반응형 레이아웃
    """

    return """
    <style>
    /* ===== AE WIKI 전용 CSS 스타일 ===== */

    /* 전역 다크 테마 설정 */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #1a1d24 100%);
        color: #ffffff;
    }

    /* 메인 컨테이너 스타일 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* 사이드바 스타일 */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1e2127 0%, #2c2f36 100%);
        border-right: 2px solid #3a3d44;
    }

    /* 헤더 및 제목 스타일 */
    h1, h2, h3, h4 {
        color: #b8bcc8;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    h1 {
        font-size: 2.5rem;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }

    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.5);
        filter: brightness(110%);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* 입력 필드 스타일 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #2c2f36;
        border: 2px solid #3a3d44;
        border-radius: 8px;
        color: #b8bcc8;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* 선택박스 스타일 */
    .stSelectbox > div > div {
        background-color: #2c2f36;
        border: 2px solid #3a3d44;
        border-radius: 8px;
        color: #b8bcc8;
    }

    .stSelectbox > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* 채팅 메시지 스타일 */
    .stChatMessage {
        background-color: #1e2127;
        border: 1px solid #3a3d44;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    .stChatMessage[data-testid="user"] {
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
        margin-left: 2rem;
    }

    .stChatMessage[data-testid="assistant"] {
        background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
        margin-right: 2rem;
    }

    /* 카드 컴포넌트 스타일 */
    .info-card {
        background: linear-gradient(135deg, #1e2127 0%, #2c2f36 100%);
        border: 2px solid #3a3d44;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }

    .info-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
        border-color: #667eea;
    }

    /* 성공/경고/오류 메시지 스타일 */
    .stSuccess {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        border: none;
        border-radius: 10px;
        color: white;
        font-weight: 600;
    }

    .stWarning {
        background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
        border: none;
        border-radius: 10px;
        color: #212529;
        font-weight: 600;
    }

    .stError {
        background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%);
        border: none;
        border-radius: 10px;
        color: white;
        font-weight: 600;
    }

    .stInfo {
        background: linear-gradient(135deg, #17a2b8 0%, #6610f2 100%);
        border: none;
        border-radius: 10px;
        color: white;
        font-weight: 600;
    }

    /* 테이블 스타일 */
    .dataframe {
        background-color: #1e2127;
        border: 2px solid #3a3d44;
        border-radius: 10px;
        overflow: hidden;
    }

    .dataframe th {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 1rem;
        border: none;
    }

    .dataframe td {
        background-color: #2c2f36;
        color: #b8bcc8;
        padding: 0.75rem;
        border-bottom: 1px solid #3a3d44;
    }

    .dataframe tr:hover td {
        background-color: #3a3d44;
    }

    /* 메트릭 카드 스타일 */
    .metric-card {
        background: linear-gradient(135deg, #1e2127 0%, #2c2f36 100%);
        border: 2px solid #3a3d44;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        border-color: #667eea;
        transform: scale(1.02);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        color: #b8bcc8;
        font-size: 0.9rem;
        font-weight: 500;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1e2127;
        border-radius: 10px;
        padding: 0.5rem;
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #2c2f36;
        color: #b8bcc8;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #3a3d44;
        color: #ffffff;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #667eea;
    }

    /* 진행률 바 스타일 */
    .stProgress .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 5px;
    }

    /* 토글 스위치 스타일 */
    .stCheckbox > div {
        background-color: #2c2f36;
        border: 2px solid #3a3d44;
        border-radius: 8px;
        padding: 0.5rem;
        transition: all 0.3s ease;
    }

    .stCheckbox > div:hover {
        border-color: #667eea;
        background-color: #3a3d44;
    }

    /* 사용자 정의 컴포넌트 */
    .gradient-text {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        font-size: 1.2rem;
    }

    .highlight-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.2rem;
    }

    .status-active {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        color: white;
    }

    .status-pending {
        background: linear-gradient(90deg, #ffc107 0%, #fd7e14 100%);
        color: #212529;
    }

    .status-inactive {
        background: linear-gradient(90deg, #6c757d 0%, #495057 100%);
        color: white;
    }

    /* 애니메이션 효과 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes slideIn {
        from { transform: translateX(-100%); }
        to { transform: translateX(0); }
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }

    .slide-in {
        animation: slideIn 0.4s ease-out;
    }

    .pulse {
        animation: pulse 2s infinite;
    }

    /* 스크롤바 스타일 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1e2127;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a6fd8, #6a63ad);
    }

    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        h1 {
            font-size: 2rem;
        }

        .stChatMessage[data-testid="user"] {
            margin-left: 0;
        }

        .stChatMessage[data-testid="assistant"] {
            margin-right: 0;
        }

        .metric-card {
            padding: 1rem;
        }

        .info-card {
            padding: 1rem;
        }
    }

    /* 로딩 스피너 스타일 */
    .loading-spinner {
        border: 4px solid #2c2f36;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* 커스텀 알림 박스 */
    .custom-alert {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid;
        background-color: rgba(255, 255, 255, 0.05);
    }

    .alert-info {
        border-left-color: #17a2b8;
        background: linear-gradient(135deg, rgba(23, 162, 184, 0.1) 0%, rgba(102, 16, 242, 0.1) 100%);
    }

    .alert-success {
        border-left-color: #28a745;
        background: linear-gradient(135deg, rgba(40, 167, 69, 0.1) 0%, rgba(32, 201, 151, 0.1) 100%);
    }

    .alert-warning {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(253, 126, 20, 0.1) 100%);
    }

    .alert-danger {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, rgba(220, 53, 69, 0.1) 0%, rgba(232, 62, 140, 0.1) 100%);
    }
    </style>
    """

def create_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal") -> str:
    """
    🎯 목적: 메트릭 카드 HTML 생성

    📊 입력:
    - title (str): 메트릭 제목
    - value (str): 메트릭 값
    - delta (str): 변화량 (선택)
    - delta_color (str): 변화량 색상 ("normal", "inverse")

    📤 출력:
    - str: 메트릭 카드 HTML
    """

    delta_html = ""
    if delta:
        color = "#28a745" if delta_color == "normal" else "#dc3545"
        delta_html = f'<div style="color: {color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>'

    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{title}</div>
        {delta_html}
    </div>
    """

def create_status_badge(text: str, status: str = "active") -> str:
    """
    🎯 목적: 상태 배지 HTML 생성

    📊 입력:
    - text (str): 배지 텍스트
    - status (str): 상태 ("active", "pending", "inactive")

    📤 출력:
    - str: 상태 배지 HTML
    """

    return f'<span class="status-badge status-{status}">{text}</span>'

def create_info_card(title: str, content: str, icon: str = "ℹ️") -> str:
    """
    🎯 목적: 정보 카드 HTML 생성

    📊 입력:
    - title (str): 카드 제목
    - content (str): 카드 내용
    - icon (str): 아이콘

    📤 출력:
    - str: 정보 카드 HTML
    """

    return f"""
    <div class="info-card">
        <h4 style="color: #667eea; margin-bottom: 1rem;">
            {icon} {title}
        </h4>
        <p style="color: #b8bcc8; margin-bottom: 0; line-height: 1.6;">
            {content}
        </p>
    </div>
    """

def create_alert_box(message: str, alert_type: str = "info") -> str:
    """
    🎯 목적: 커스텀 알림 박스 HTML 생성

    📊 입력:
    - message (str): 알림 메시지
    - alert_type (str): 알림 타입 ("info", "success", "warning", "danger")

    📤 출력:
    - str: 알림 박스 HTML
    """

    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "danger": "❌"
    }

    icon = icons.get(alert_type, "ℹ️")

    return f"""
    <div class="custom-alert alert-{alert_type}">
        <strong>{icon} {message}</strong>
    </div>
    """

def show_loading_spinner(container) -> None:
    """
    🎯 목적: 로딩 스피너 표시

    📊 입력:
    - container: Streamlit 컨테이너 객체
    """

    container.markdown("""
    <div class="loading-spinner"></div>
    """, unsafe_allow_html=True)

def create_gradient_text(text: str, gradient: str = None) -> str:
    """
    🎯 목적: 그라데이션 텍스트 HTML 생성

    📊 입력:
    - text (str): 텍스트
    - gradient (str): CSS 그라데이션 (선택)

    📤 출력:
    - str: 그라데이션 텍스트 HTML
    """

    if not gradient:
        gradient = "linear-gradient(90deg, #667eea 0%, #764ba2 100%)"

    return f"""
    <span style="
        background: {gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        font-size: 1.2rem;
    ">{text}</span>
    """

def apply_animation(element_html: str, animation: str = "fadeIn") -> str:
    """
    🎯 목적: HTML 요소에 애니메이션 클래스 추가

    📊 입력:
    - element_html (str): HTML 요소
    - animation (str): 애니메이션 타입 ("fadeIn", "slideIn", "pulse")

    📤 출력:
    - str: 애니메이션이 적용된 HTML
    """

    # 기존 class 속성 찾기
    if 'class="' in element_html:
        element_html = element_html.replace('class="', f'class="{animation} ')
    else:
        # div 태그 찾아서 class 추가
        if element_html.startswith('<div'):
            element_html = element_html.replace('<div', f'<div class="{animation}"', 1)
        else:
            # 전체를 div로 감싸기
            element_html = f'<div class="{animation}">{element_html}</div>'

    return element_html