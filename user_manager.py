"""
======================================================================
사용자 관리 모듈 (user_manager.py)
======================================================================

📋 파일 역할:
- AE WIKI 시스템의 모든 사용자 관리 기능 통합 제공
- 로그인, 회원가입, 승인 관리를 users_management.json 하나로 일원화
- bcrypt 암호화를 통한 보안성 강화
- 세션 관리 및 권한 제어

🔐 주요 기능:
- 사용자 인증 (로그인/로그아웃)
- 회원가입 요청 및 관리자 승인 시스템
- 비밀번호 bcrypt 해싱 암호화
- 활성/비활성 사용자 관리
- 로그인 시도 추적 및 보안

🔗 연동 관계:
- pages/1_🔑_로그인.py: 로그인 UI에서 인증 함수 호출
- pages/9_⚙️_관리자.py: 사용자 승인 및 관리 기능
- utils.py: require_login()에서 인증 상태 확인
"""

import json  # JSON 파일 읽기/쓰기용
import os  # 파일 시스템 접근용
import bcrypt  # 비밀번호 해싱 암호화용
import uuid  # 고유 사용자 ID 생성용
from datetime import datetime  # 시간 정보 기록용
from typing import Dict, List, Optional, Tuple, Any  # 타입 힌팅용
import logging  # 로깅 시스템용

logger = logging.getLogger(__name__)  # 로거 인스턴스 생성

# config.py에서 파일 경로 가져오기
from config import DATA_CONFIG
USERS_FILE = DATA_CONFIG["users_management_file"]  # 사용자 데이터 저장 파일 경로

def load_users_data() -> Dict[str, Any]:
    """
    🔄 사용자 관리 데이터 로드 함수
    
    users_management.json 파일에서 모든 사용자 데이터를 읽어옵니다.
    파일이 없으면 기본 구조를 가진 빈 데이터를 반환합니다.
    
    Returns:
        Dict[str, Any]: 사용자 관리 데이터
            - active_users: 활성 사용자 계정 정보
            - registration_requests: 회원가입 승인 대기 목록
            - sessions: 로그인 세션 정보
            - login_attempts: 로그인 시도 기록
            - metadata: 시스템 메타데이터
    """
    if not os.path.exists(USERS_FILE):  # 파일이 존재하지 않으면
        return {  # 기본 구조 반환
            "active_users": {},  # 빈 활성 사용자 딕셔너리
            "registration_requests": [],  # 빈 회원가입 요청 리스트
            "sessions": {},  # 빈 세션 딕셔너리
            "login_attempts": {},  # 빈 로그인 시도 기록 딕셔너리
            "metadata": {  # 시스템 메타데이터
                "version": "1.0",  # 시스템 버전
                "last_updated": datetime.now().isoformat(),  # 마지막 업데이트 시간
                "description": "통합 사용자 관리 시스템"  # 시스템 설명
            }
        }
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:  # UTF-8 인코딩으로 파일 열기
            return json.load(f)  # JSON 데이터 파싱하여 반환
    except Exception as e:  # 파일 읽기 실패 시
        logger.error(f"사용자 데이터 로드 실패: {e}")  # 에러 로깅
        return {"active_users": {}, "registration_requests": [], "sessions": {}, "login_attempts": {}}  # 기본 구조 반환

def save_users_data(data: Dict[str, Any]) -> bool:
    """
    💾 사용자 관리 데이터 저장 함수
    
    수정된 사용자 데이터를 users_management.json 파일에 저장합니다.
    메타데이터의 마지막 업데이트 시간도 자동으로 갱신합니다.
    
    Args:
        data (Dict[str, Any]): 저장할 사용자 관리 데이터
            - active_users: 활성 사용자 정보
            - registration_requests: 회원가입 신청 목록
            - sessions: 세션 정보
            - login_attempts: 로그인 시도 기록
            - metadata: 시스템 메타데이터
    
    Returns:
        bool: 저장 성공 여부 (True: 성공, False: 실패)
    """
    try:
        data["metadata"]["last_updated"] = datetime.now().isoformat()  # 마지막 업데이트 시간 갱신
        with open(USERS_FILE, 'w', encoding='utf-8') as f:  # UTF-8 인코딩으로 파일 쓰기
            json.dump(data, f, ensure_ascii=False, indent=2)  # JSON 형태로 데이터 저장 (한글 지원, 들여쓰기 2칸)
        return True  # 저장 성공
    except Exception as e:  # 저장 실패 시
        logger.error(f"사용자 데이터 저장 실패: {e}")  # 에러 로깅
        return False  # 저장 실패

def get_active_user(username: str) -> Optional[Dict[str, Any]]:
    """
    👤 활성 사용자 정보 조회 함수
    
    주어진 사용자명으로 활성 사용자 정보를 검색합니다.
    
    Args:
        username (str): 조회할 사용자명 (NOX ID)
    
    Returns:
        Optional[Dict[str, Any]]: 사용자 정보 딕셔너리 또는 None
            - user_id: 고유 사용자 ID
            - nox_id: NOX 아이디
            - nickname: 사용자 별명
            - name: 실명
            - department: 부서
            - is_active: 활성 상태
            - role: 역할 (user/admin)
            - created_at: 계정 생성일
            - last_login: 마지막 로그인
    """
    data = load_users_data()  # 사용자 데이터 로드
    return data.get("active_users", {}).get(username)  # 해당 사용자명의 정보 반환 (없으면 None)

def verify_user_password(username: str, password: str) -> bool:
    """
    🔐 사용자 비밀번호 검증 함수
    
    입력받은 평문 비밀번호와 저장된 해시값을 bcrypt로 비교 검증합니다.
    
    Args:
        username (str): 검증할 사용자명
        password (str): 평문 비밀번호
    
    Returns:
        bool: 비밀번호 일치 여부 (True: 일치, False: 불일치 또는 오류)
    """
    user = get_active_user(username)  # 사용자 정보 조회
    if not user or not user.get("is_active", False):  # 사용자가 없거나 비활성 상태이면
        return False  # 검증 실패
    
    stored_hash = user.get("password", "")  # 저장된 해시 비밀번호 가져오기
    if not stored_hash:  # 저장된 비밀번호가 없으면
        return False  # 검증 실패
    
    try:
        # bcrypt로 평문 비밀번호와 해시값 비교
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception as e:  # 검증 중 오류 발생 시
        logger.error(f"비밀번호 확인 실패: {e}")  # 에러 로깅
        return False  # 검증 실패

def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    🔑 사용자 인증 함수
    
    사용자의 로그인 요청을 처리하고 인증을 수행합니다.
    입력값 검증, 사용자 존재 확인, 계정 상태 확인, 비밀번호 검증을 단계적으로 진행합니다.
    
    Args:
        username (str): 로그인할 사용자명 (NOX ID)
        password (str): 평문 비밀번호
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (인증 성공 여부, 메시지, 사용자 정보)
            - 성공 시: (True, "로그인 성공", 사용자_정보_딕셔너리)
            - 실패 시: (False, 오류_메시지, None)
    """
    # 입력값 검증
    if not username or not password:  # 아이디나 비밀번호가 비어있으면
        return False, "아이디와 비밀번호를 입력해주세요", None  # 입력 요구 메시지
    
    # 사용자 존재 확인
    user = get_active_user(username)  # 활성 사용자 정보 조회
    if not user:  # 사용자가 존재하지 않으면
        return False, "존재하지 않는 사용자입니다", None  # 존재하지 않음 메시지
    
    # 계정 활성화 상태 확인
    if not user.get("is_active", False):  # 계정이 비활성 상태이면
        return False, "비활성화된 계정입니다", None  # 비활성 계정 메시지
    
    # 비밀번호 확인
    if not verify_user_password(username, password):  # 비밀번호가 틀리면
        return False, "비밀번호가 틀렸습니다", None  # 비밀번호 오류 메시지
    
    # 마지막 로그인 시간 업데이트
    data = load_users_data()  # 현재 데이터 로드
    data["active_users"][username]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 로그인 시간 갱신
    save_users_data(data)  # 업데이트된 데이터 저장
    
    return True, "로그인 성공", user  # 인증 성공 및 사용자 정보 반환

def get_all_active_users() -> Dict[str, Dict[str, Any]]:
    """
    📋 전체 활성 사용자 목록 조회 함수
    
    시스템에 등록된 모든 활성 사용자의 정보를 반환합니다.
    관리자 페이지에서 사용자 목록을 표시할 때 사용됩니다.
    
    Returns:
        Dict[str, Dict[str, Any]]: 사용자명을 키로 하는 사용자 정보 딕셔너리
            - 키: 사용자명 (NOX ID)
            - 값: 사용자 정보 딕셔너리 (user_id, name, department, role 등)
    """
    data = load_users_data()  # 사용자 데이터 로드
    return data.get("active_users", {})  # 활성 사용자 딕셔너리 반환 (없으면 빈 딕셔너리)

def add_registration_request(nox_id: str, name: str, department: str, password: str) -> Tuple[bool, str]:
    """
    📝 회원가입 신청 추가 함수
    
    새로운 사용자의 회원가입 신청을 처리합니다.
    중복 확인, 비밀번호 해싱, 신청 정보 저장을 수행합니다.
    
    Args:
        nox_id (str): 신청자의 NOX 아이디
        name (str): 신청자의 실명
        department (str): 신청자의 소속 부서
        password (str): 평문 비밀번호
    
    Returns:
        Tuple[bool, str]: (신청 성공 여부, 결과 메시지)
            - 성공 시: (True, "신청 완료 메시지")
            - 실패 시: (False, "오류 메시지")
    """
    data = load_users_data()  # 현재 사용자 데이터 로드
    
    # 중복 확인 - users_management.json의 active_users
    if nox_id in data.get("active_users", {}):  # 이미 활성 사용자로 등록된 경우
        return False, "이미 가입된 사용자입니다"  # 중복 가입 거부
    
    # 중복 확인 - knowledge_data.json의 approved_users (기존 시스템과의 호환성)
    try:
        import json  # JSON 처리를 위한 임포트
        from config import DATA_CONFIG  # 설정 파일에서 데이터 경로 가져오기
        
        if os.path.exists(DATA_CONFIG["data_file"]):  # 기존 데이터 파일이 존재하면
            with open(DATA_CONFIG["data_file"], 'r', encoding='utf-8') as f:  # 파일 읽기
                main_data = json.load(f)  # JSON 데이터 로드
                if nox_id in main_data.get("approved_users", {}):  # 기존 승인 사용자에 존재하면
                    return False, "이미 가입된 사용자입니다"  # 중복 가입 거부
    except Exception as e:  # 기존 데이터 확인 중 오류 발생 시
        logger.warning(f"approved_users 확인 중 오류: {e}")  # 경고 로깅 (치명적이지 않음)
    
    # 대기 중인 신청 확인
    for req in data.get("registration_requests", []):  # 모든 신청 목록 확인
        if req.get("nox_id") == nox_id and req.get("status") == "pending":  # 동일 ID로 대기 중인 신청이 있으면
            return False, "이미 가입 신청이 진행 중입니다"  # 중복 신청 거부
    
    # 비밀번호 해싱
    try:
        # bcrypt로 안전한 해시 생성 (salt 자동 생성)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as e:  # 해싱 실패 시
        return False, f"비밀번호 처리 실패: {e}"  # 해싱 오류 메시지
    
    # 신청 추가
    request_id = str(uuid.uuid4())  # 고유한 신청 ID 생성
    new_request = {  # 새 신청 정보 구성
        "id": request_id,  # 고유 신청 ID
        "nox_id": nox_id,  # 신청자 NOX ID
        "name": name,  # 신청자 실명
        "department": department,  # 소속 부서
        "password_hash": password_hash,  # 해싱된 비밀번호
        "status": "pending",  # 신청 상태 (대기중)
        "requested_at": datetime.now().isoformat(),  # 신청 일시
        "processed_at": None,  # 처리 일시 (아직 미처리)
        "processed_by": None  # 처리자 (아직 미처리)
    }
    
    if "registration_requests" not in data:  # 신청 목록이 없으면
        data["registration_requests"] = []  # 빈 리스트 생성
    data["registration_requests"].append(new_request)  # 새 신청 추가
    
    if save_users_data(data):  # 데이터 저장 성공 시
        return True, "회원가입 신청이 완료되었습니다. 관리자 승인을 기다려주세요."  # 성공 메시지
    else:  # 데이터 저장 실패 시
        return False, "회원가입 신청 중 오류가 발생했습니다"  # 실패 메시지

def get_pending_requests() -> List[Dict[str, Any]]:
    """
    ⏳ 대기 중인 회원가입 신청 목록 조회 함수
    
    관리자 승인을 기다리고 있는 회원가입 신청 목록을 반환합니다.
    관리자 페이지에서 승인 대기 목록을 표시할 때 사용됩니다.
    
    Returns:
        List[Dict[str, Any]]: 대기 중인 신청 목록
            - 각 항목은 신청 ID, NOX ID, 이름, 부서, 신청일 등의 정보 포함
    """
    data = load_users_data()  # 사용자 데이터 로드
    # 등록 신청 중 상태가 'pending'인 것들만 필터링하여 반환
    return [req for req in data.get("registration_requests", []) if req.get("status") == "pending"]

def get_processed_requests() -> List[Dict[str, Any]]:
    """
    ✅ 처리된 회원가입 신청 목록 조회 함수
    
    이미 승인되거나 거부된 회원가입 신청 목록을 반환합니다.
    처리일 기준 최신순으로 정렬되어 반환됩니다.
    
    Returns:
        List[Dict[str, Any]]: 처리된 신청 목록 (최신순 정렬)
            - 각 항목은 신청 정보 + 처리 일시, 처리자, 승인/거부 상태 포함
    """
    data = load_users_data()  # 사용자 데이터 로드
    # 승인 또는 거부 상태인 신청들만 필터링
    processed = [req for req in data.get("registration_requests", []) if req.get("status") in ["approved", "rejected"]]
    # 처리일 기준 최신순 정렬 (최근 처리된 것이 먼저 나오도록)
    return sorted(processed, key=lambda x: x.get("processed_at", ""), reverse=True)

def approve_registration_request(request_id: str, admin_username: str) -> Tuple[bool, str]:
    """
    ✅ 회원가입 신청 승인 함수
    
    관리자가 대기 중인 회원가입 신청을 승인하는 함수입니다.
    신청자를 활성 사용자로 등록하고 신청 상태를 승인으로 변경합니다.
    
    Args:
        request_id (str): 승인할 신청의 고유 ID
        admin_username (str): 승인 처리하는 관리자의 사용자명
    
    Returns:
        Tuple[bool, str]: (승인 성공 여부, 결과 메시지)
            - 성공 시: (True, "승인 완료 메시지")
            - 실패 시: (False, "오류 메시지")
    """
    data = load_users_data()  # 현재 사용자 데이터 로드
    
    # 신청 찾기
    request_to_approve = None  # 승인할 신청 객체 초기화
    for req in data.get("registration_requests", []):  # 모든 등록 신청 순회
        if req.get("id") == request_id and req.get("status") == "pending":  # 해당 ID이고 대기중인 신청이면
            request_to_approve = req  # 승인할 신청 설정
            break  # 찾았으면 루프 종료
    
    if not request_to_approve:  # 승인할 신청을 찾지 못한 경우
        return False, "승인할 신청을 찾을 수 없습니다"  # 실패 메시지
    
    # 활성 사용자로 추가
    user_id = str(uuid.uuid4())  # 새로운 사용자 고유 ID 생성
    new_user = {  # 새 사용자 정보 구성
        "user_id": user_id,  # 고유 사용자 ID
        "nox_id": request_to_approve["nox_id"],  # NOX 아이디
        "nickname": request_to_approve["name"],  # 별명 (실명과 동일)
        "name": request_to_approve["name"],  # 실명
        "department": request_to_approve["department"],  # 소속 부서
        "password": request_to_approve["password_hash"],  # 해시된 비밀번호
        "is_active": True,  # 활성 상태로 설정
        "role": "user",  # 일반 사용자 권한
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 계정 생성 시간
        "last_login": None,  # 마지막 로그인 (아직 없음)
        "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 승인 시간
        "approved_by": admin_username  # 승인한 관리자
    }
    
    data["active_users"][request_to_approve["nox_id"]] = new_user  # 활성 사용자 목록에 추가
    
    # 신청 상태 업데이트
    request_to_approve["status"] = "approved"  # 상태를 승인으로 변경
    request_to_approve["processed_at"] = datetime.now().isoformat()  # 처리 시간 기록
    request_to_approve["processed_by"] = admin_username  # 처리한 관리자 기록
    
    if save_users_data(data):  # 데이터 저장 성공 시
        return True, f"{request_to_approve['name']}님의 가입을 승인했습니다"  # 성공 메시지
    else:  # 데이터 저장 실패 시
        return False, "승인 처리 중 오류가 발생했습니다"  # 실패 메시지

def reject_registration_request(request_id: str, admin_username: str, reason: str = "") -> Tuple[bool, str]:
    """
    ❌ 회원가입 신청 거부 함수
    
    관리자가 대기 중인 회원가입 신청을 거부하는 함수입니다.
    신청 상태를 거부로 변경하고 거부 사유를 기록합니다.
    
    Args:
        request_id (str): 거부할 신청의 고유 ID
        admin_username (str): 거부 처리하는 관리자의 사용자명
        reason (str, optional): 거부 사유 (선택사항)
    
    Returns:
        Tuple[bool, str]: (거부 성공 여부, 결과 메시지)
            - 성공 시: (True, "거부 완료 메시지")
            - 실패 시: (False, "오류 메시지")
    """
    data = load_users_data()  # 현재 사용자 데이터 로드
    
    # 신청 찾기
    request_to_reject = None  # 거부할 신청 객체 초기화
    for req in data.get("registration_requests", []):  # 모든 등록 신청 순회
        if req.get("id") == request_id and req.get("status") == "pending":  # 해당 ID이고 대기중인 신청이면
            request_to_reject = req  # 거부할 신청 설정
            break  # 찾았으면 루프 종료
    
    if not request_to_reject:  # 거부할 신청을 찾지 못한 경우
        return False, "거부할 신청을 찾을 수 없습니다"  # 실패 메시지
    
    # 신청 상태 업데이트
    request_to_reject["status"] = "rejected"  # 상태를 거부로 변경
    request_to_reject["processed_at"] = datetime.now().isoformat()  # 처리 시간 기록
    request_to_reject["processed_by"] = admin_username  # 처리한 관리자 기록
    request_to_reject["rejection_reason"] = reason  # 거부 사유 기록
    
    if save_users_data(data):  # 데이터 저장 성공 시
        return True, f"{request_to_reject['name']}님의 가입을 거부했습니다"  # 성공 메시지
    else:  # 데이터 저장 실패 시
        return False, "거부 처리 중 오류가 발생했습니다"  # 실패 메시지

def is_admin_user(username: str) -> bool:
    """
    🔑 관리자 권한 확인 함수
    
    주어진 사용자가 관리자 권한을 가지고 있는지 확인합니다.
    관리자 전용 기능에 접근하기 전에 권한을 검증할 때 사용됩니다.
    
    Args:
        username (str): 권한을 확인할 사용자명
    
    Returns:
        bool: 관리자 권한 여부 (True: 관리자, False: 일반 사용자 또는 비활성)
    """
    user = get_active_user(username)  # 사용자 정보 조회
    # 사용자가 존재하고 role이 'admin'인지 확인
    return user is not None and user.get("role") == "admin"

def get_user_stats() -> Dict[str, int]:
    """
    📊 사용자 통계 정보 조회 함수
    
    시스템의 사용자 및 회원가입 신청 현황을 통계로 반환합니다.
    관리자 대시보드에서 전체 현황을 한눈에 파악할 때 사용됩니다.
    
    Returns:
        Dict[str, int]: 사용자 통계 정보
            - total_active_users: 전체 활성 사용자 수
            - admin_users: 관리자 수
            - regular_users: 일반 사용자 수
            - pending_requests: 대기 중인 신청 수
            - approved_requests: 승인된 신청 수
            - rejected_requests: 거부된 신청 수
    """
    data = load_users_data()  # 사용자 데이터 로드
    active_users = data.get("active_users", {})  # 활성 사용자 데이터
    requests = data.get("registration_requests", [])  # 회원가입 신청 데이터
    
    return {
        "total_active_users": len(active_users),  # 전체 활성 사용자 개수
        "admin_users": len([u for u in active_users.values() if u.get("role") == "admin"]),  # 관리자 개수
        "regular_users": len([u for u in active_users.values() if u.get("role") == "user"]),  # 일반 사용자 개수
        "pending_requests": len([r for r in requests if r.get("status") == "pending"]),  # 대기중 신청 개수
        "approved_requests": len([r for r in requests if r.get("status") == "approved"]),  # 승인된 신청 개수
        "rejected_requests": len([r for r in requests if r.get("status") == "rejected"])  # 거부된 신청 개수
    }