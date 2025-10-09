#!/usr/bin/env python3
"""
데이터 연동 테스트 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 패스에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_data_connectivity():
    """데이터 연동 상태 테스트"""
    print("🔍 데이터 연동 상태 확인 중...")

    try:
        # 1. data_manager 테스트
        print("\n1️⃣ data_manager 테스트")
        from data_manager import initialize_data, DATA_CONFIG
        data = initialize_data()
        print(f"✅ 데이터 초기화 성공")
        print(f"📁 데이터 파일 경로: {DATA_CONFIG['data_file']}")
        print(f"📊 Questions: {len(data.get('questions', []))}개")
        print(f"📝 Answers: {len(data.get('answers', []))}개")

    except Exception as e:
        print(f"❌ data_manager 오류: {e}")
        return False

    try:
        # 2. auth_manager 테스트
        print("\n2️⃣ auth_manager 테스트")
        from auth_manager import get_users_from_secrets
        users = get_users_from_secrets()
        print(f"✅ 사용자 관리 시스템 연결 성공")
        print(f"👥 활성 사용자: {len(users)}명")

    except Exception as e:
        print(f"❌ auth_manager 오류: {e}")
        return False

    try:
        # 3. utils 통합 테스트
        print("\n3️⃣ utils 통합 모듈 테스트")
        from utils import initialize_data as utils_init, get_all_users
        data = utils_init()
        users = get_all_users()
        print(f"✅ utils 모듈 통합 성공")
        print(f"📊 utils 데이터: {len(data.get('questions', []))}개 질문")
        print(f"👥 utils 사용자: {len(users)}명")

    except Exception as e:
        print(f"❌ utils 통합 오류: {e}")
        return False

    try:
        # 4. config 테스트
        print("\n4️⃣ config 설정 테스트")
        from config import DATA_CONFIG, CHATBOT_INDICES
        print(f"✅ 설정 로드 성공")
        print(f"📁 데이터 폴더: {os.path.dirname(DATA_CONFIG['data_file'])}")
        print(f"🤖 챗봇 인덱스: {len(CHATBOT_INDICES)}개")
        for idx_id in CHATBOT_INDICES.keys():
            print(f"   - {idx_id}: {CHATBOT_INDICES[idx_id].get('display_name', 'Unknown')}")

    except Exception as e:
        print(f"❌ config 오류: {e}")
        return False

    print("\n🎉 모든 데이터 연동 테스트 통과!")
    return True

if __name__ == "__main__":
    success = test_data_connectivity()
    sys.exit(0 if success else 1)