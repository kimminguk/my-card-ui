"""
======================================================================
AE WIKI 통합 챗봇 시스템 - 데이터 관리 모듈 (data_manager.py)
======================================================================

📋 파일 역할:
- JSON 기반 로컬 데이터베이스 관리
- 데이터 초기화, 저장, 로드 및 스키마 호환성 보장
- 메인 데이터 저장소와 사용자 데이터 저장소 통합 관리

🔧 주요 기능:
1. 메인 데이터베이스 (knowledge_data.json) 관리
2. 사용자 데이터베이스 (users_data.json) 관리
3. 스키마 진화 및 하위 호환성 지원
4. 안전한 파일 I/O 처리

🔗 연동 관계:
- 모든 페이지에서 데이터 접근 시 호출
- auth_manager.py: 사용자 인증 데이터 관리
- chat_manager.py: 채팅 기록 저장
- qa_manager.py: Q&A 데이터 관리
"""

import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

# 로거 설정
logger = logging.getLogger(__name__)

# 설정 파일에서 데이터 경로 로드
try:
    from config import DATA_CONFIG
except ImportError:
    # 폴백 설정
    import os
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = os.path.join(PROJECT_ROOT, "datalog")
    os.makedirs(DATA_FOLDER, exist_ok=True)

    DATA_CONFIG = {
        "data_file": os.path.join(DATA_FOLDER, "knowledge_data.json"),
        "users_file": os.path.join(DATA_FOLDER, "users_data.json"),
    }

# ====================================
# 📁 메인 데이터베이스 관리
# ====================================

def initialize_data() -> Dict[str, Any]:
    """
    메인 데이터 저장소 초기화

    시스템 최초 실행 시 또는 데이터 파일이 없을 때 기본 구조를 생성합니다.
    Q&A 시스템, 채팅 기록, 사용자 포인트 등 모든 데이터 스키마를 통합 관리합니다.

    호출 관계:
    - 🏠_Home.py, 챗봇 페이지들에서 시스템 시작 시 호출
    - load_data() -> save_data() 체인 호출로 데이터 초기화

    부작용:
    - knowledge_data.json 파일이 없으면 새로 생성
    - 파일 시스템에 JSON 데이터 영구 저장

    Returns:
        Dict[str, Any]: 초기화된 데이터 구조 또는 기존 데이터
            - questions: List[Dict] - Q&A 시스템용 질문 목록
            - answers: List[Dict] - Q&A 시스템용 답변 목록
            - chat_history: List[Dict] - 기술 챗봇 대화 기록
            - admin_chat_history: List[Dict] - 관리자 챗봇 대화 기록
            - user_points: Dict[str, int] - 사용자별 포인트 시스템
    """
    data_file = DATA_CONFIG["data_file"]

    if not os.path.exists(data_file):
        # 시스템 기본 스키마 정의
        initial_data = {
            "questions": [],  # Q&A 시스템용 질문 목록
            "answers": [],    # Q&A 시스템용 답변 목록
            "users": {},      # 레거시 사용자 정보 (하위 호환성)
            "likes": {},      # 답변 좋아요 시스템
            "search_logs": [],  # 검색 기록 분석용
            "chat_history": [],  # 기술 챗봇 대화 기록
            "admin_chat_history": [],  # 관리자 챗봇 대화 기록 (호환성)
            "user_points": {},  # 사용자 포인트 시스템
            "registration_requests": [],  # 회원가입 신청 목록 (관리자 승인 대기)
            "approved_users": {}  # 승인된 사용자 목록 (자동 로그인 가능)
        }
        save_data(initial_data)
        return initial_data
    else:
        # 기존 데이터 로드 및 호환성 업데이트
        data = load_data()

        # 회원가입 관련 필드가 없으면 추가
        updated = False
        if "registration_requests" not in data:
            data["registration_requests"] = []
            updated = True
            logger.info("기존 데이터베이스에 registration_requests 필드 추가됨")

        if "approved_users" not in data:
            data["approved_users"] = {}
            updated = True
            logger.info("기존 데이터베이스에 approved_users 필드 추가됨")

        if updated:
            save_data(data)

        return data

def save_data(data: Dict[str, Any]) -> None:
    """
    데이터를 JSON 파일에 안전하게 저장

    메모리의 데이터 변경사항을 영구 저장소에 동기화합니다.
    UTF-8 인코딩과 들여쓰기를 적용하여 가독성과 국제화를 지원합니다.

    호출 관계:
    - save_chat_history(), add_question(), add_answer() 등에서 호출
    - 모든 데이터 변경 작업 후 자동으로 호출되어 일관성 보장

    부작용:
    - knowledge_data.json 파일을 완전히 덮어씀 (원자적 쓰기)
    - 파일 쓰기 오류 시 IOError 예외 발생 (상위로 전파)

    Args:
        data: 저장할 데이터 구조 (JSON 직렬화 가능한 타입)
    """
    data_file = DATA_CONFIG["data_file"]
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data() -> Dict[str, Any]:
    """
    JSON 파일에서 데이터 로드 및 스키마 호환성 보장

    영구 저장소에서 데이터를 메모리로 로드하면서 스키마 진화를 지원합니다.
    새로 추가된 필드들을 자동으로 보완하여 하위 호환성을 유지합니다.

    호출 관계:
    - initialize_data()에서 호출하여 기존 데이터 검증
    - 모든 데이터 접근 함수에서 최신 데이터 보장용으로 호출

    부작용:
    - 파일 읽기 오류 시 FileNotFoundError 예외 발생
    - 스키마 업데이트 시 자동으로 save_data() 호출

    Returns:
        Dict[str, Any]: 로드된 데이터 구조

    Raises:
        FileNotFoundError: 데이터 파일이 존재하지 않을 때
        json.JSONDecodeError: JSON 파싱 오류 시
    """
    data_file = DATA_CONFIG["data_file"]

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 스키마 호환성 검사 및 보완
        schema_updated = False

        # 필수 필드들 검사
        required_fields = {
            "questions": [],
            "answers": [],
            "users": {},
            "likes": {},
            "search_logs": [],
            "chat_history": [],
            "admin_chat_history": [],
            "user_points": {},
            "registration_requests": [],
            "approved_users": {}
        }

        for field, default_value in required_fields.items():
            if field not in data:
                data[field] = default_value
                schema_updated = True
                logger.info(f"스키마 업데이트: {field} 필드 추가됨")

        # 스키마 업데이트가 있었다면 저장
        if schema_updated:
            save_data(data)
            logger.info("데이터 스키마 호환성 업데이트 완료")

        return data

    except FileNotFoundError:
        logger.error(f"데이터 파일을 찾을 수 없음: {data_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        raise

# ====================================
# 👥 사용자 데이터베이스 관리
# ====================================

def initialize_users_data() -> Dict[str, Any]:
    """
    사용자 전용 데이터 저장소 초기화

    사용자 계정 정보를 별도 파일로 관리하여 보안성과 성능을 향상시킵니다.
    메인 데이터와 분리하여 백업 및 마이그레이션을 용이하게 합니다.

    Returns:
        Dict[str, Any]: 초기화된 사용자 데이터 구조
            - users: Dict[str, Dict] - 사용자 계정 정보
            - last_updated: str - 마지막 업데이트 시간
    """
    users_file = DATA_CONFIG["users_file"]

    if not os.path.exists(users_file):
        initial_users_data = {
            "users": {},
            "last_updated": datetime.now().isoformat()
        }
        save_users_data(initial_users_data)
        logger.info("새로운 사용자 데이터베이스 생성됨")
        return initial_users_data
    else:
        return load_users_data()

def save_users_data(users_data: Dict[str, Any]) -> None:
    """
    사용자 데이터를 JSON 파일에 안전하게 저장

    Args:
        users_data: 저장할 사용자 데이터 구조
    """
    users_file = DATA_CONFIG["users_file"]
    users_data["last_updated"] = datetime.now().isoformat()

    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

    logger.debug(f"사용자 데이터 저장 완료: {len(users_data.get('users', {}))}명")

def load_users_data() -> Dict[str, Any]:
    """
    사용자 데이터 파일에서 데이터 로드

    Returns:
        Dict[str, Any]: 로드된 사용자 데이터 구조

    Raises:
        FileNotFoundError: 사용자 데이터 파일이 존재하지 않을 때
        json.JSONDecodeError: JSON 파싱 오류 시
    """
    users_file = DATA_CONFIG["users_file"]

    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)

        # 스키마 호환성 검사
        if "users" not in users_data:
            users_data["users"] = {}
        if "last_updated" not in users_data:
            users_data["last_updated"] = datetime.now().isoformat()

        return users_data

    except FileNotFoundError:
        logger.warning(f"사용자 데이터 파일을 찾을 수 없음: {users_file}")
        return initialize_users_data()
    except json.JSONDecodeError as e:
        logger.error(f"사용자 데이터 JSON 파싱 오류: {e}")
        raise