"""
=================================================================
💬 AE WIKI - 채팅 관리자 모듈 (chat_manager.py)
=================================================================

📋 파일 역할:
- 채팅 기록 저장 및 로드
- 검색 로그 관리
- 사용자 활동 추적

🔗 주요 컴포넌트:
- 채팅 히스토리 관리 (슬라이딩 윈도우)
- 검색 로그 기록 및 분석
- 사용자별 활동 통계
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from auth_manager import get_current_user, get_user_id, get_username
from data_manager import save_data

logger = logging.getLogger(__name__)

def save_chat_history(data: Dict, user_message: str, bot_response: str, chatbot_type: str = "ae_wiki") -> None:
    """
    🎯 목적: 채팅 기록을 데이터에 저장 (슬라이딩 윈도우 메모리 관리)

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - user_message (str): 사용자 메시지
    - bot_response (str): 봇 응답
    - chatbot_type (str): 챗봇 타입

    🔄 처리 흐름:
    1. 사용자 정보 확인
    2. 채팅 기록 구조화
    3. 슬라이딩 윈도우 적용 (최대 100개 대화)
    4. 데이터 저장
    """

    try:
        # STEP 1: 사용자 정보 확인
        user = get_current_user()
        if not user:
            logger.warning("채팅 기록 저장 실패: 사용자 정보 없음")
            return

        user_id = user.get("user_id", "anonymous")
        username = user.get("username", "anonymous")

        # STEP 2: 채팅 기록 구조화
        chat_entry = {
            "id": f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "username": username,
            "chatbot_type": chatbot_type,
            "user_message": user_message,
            "bot_response": bot_response,
            "message_length": len(user_message),
            "response_length": len(bot_response)
        }

        # STEP 3: 채팅 기록을 데이터에 추가
        if "chat_history" not in data:
            data["chat_history"] = []

        data["chat_history"].append(chat_entry)

        # STEP 4: 슬라이딩 윈도우 적용 (최대 100개 대화 유지)
        # 메모리 효율성을 위해 오래된 채팅 기록 자동 삭제
        max_chat_history = 100
        if len(data["chat_history"]) > max_chat_history:
            # 최신 100개만 유지
            data["chat_history"] = data["chat_history"][-max_chat_history:]
            logger.info(f"채팅 기록 슬라이딩 윈도우 적용: {max_chat_history}개로 제한")

        # STEP 5: 데이터 저장
        save_data(data)
        logger.info(f"채팅 기록 저장 완료: {chatbot_type} - {username}")

    except Exception as e:
        logger.error(f"채팅 기록 저장 중 오류 발생: {e}")

def log_search(data: Dict, search_term: str, category_filter: str, results_count: int) -> None:
    """
    🎯 목적: 사용자 검색 활동을 로그에 기록

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - search_term (str): 검색어
    - category_filter (str): 카테고리 필터
    - results_count (int): 검색 결과 수

    🔄 처리 흐름:
    1. 사용자 정보 확인
    2. 검색 로그 엔트리 생성
    3. 검색 통계 업데이트
    4. 데이터 저장
    """

    try:
        # STEP 1: 사용자 정보 확인
        user = get_current_user()
        if not user:
            logger.warning("검색 로그 기록 실패: 사용자 정보 없음")
            return

        user_id = user.get("user_id", "anonymous")
        username = user.get("username", "anonymous")

        # STEP 2: 검색 로그 엔트리 생성
        search_entry = {
            "id": f"search_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "username": username,
            "search_term": search_term,
            "category_filter": category_filter,
            "results_count": results_count,
            "search_length": len(search_term)
        }

        # STEP 3: 검색 로그를 데이터에 추가
        if "search_logs" not in data:
            data["search_logs"] = []

        data["search_logs"].append(search_entry)

        # STEP 4: 검색 통계 업데이트
        if "search_stats" not in data:
            data["search_stats"] = {
                "total_searches": 0,
                "unique_users": set(),
                "popular_terms": {},
                "category_usage": {}
            }

        stats = data["search_stats"]
        stats["total_searches"] += 1
        stats["unique_users"].add(username)

        # 인기 검색어 추적
        if search_term in stats["popular_terms"]:
            stats["popular_terms"][search_term] += 1
        else:
            stats["popular_terms"][search_term] = 1

        # 카테고리 사용 추적
        if category_filter in stats["category_usage"]:
            stats["category_usage"][category_filter] += 1
        else:
            stats["category_usage"][category_filter] = 1

        # STEP 5: 슬라이딩 윈도우 적용 (최대 200개 검색 로그 유지)
        max_search_logs = 200
        if len(data["search_logs"]) > max_search_logs:
            data["search_logs"] = data["search_logs"][-max_search_logs:]

        # STEP 6: 데이터 저장
        save_data(data)
        logger.info(f"검색 로그 기록 완료: '{search_term}' by {username}")

    except Exception as e:
        logger.error(f"검색 로그 기록 중 오류 발생: {e}")

def get_user_chat_history(data: Dict, user_id: str = None, limit: int = 20) -> List[Dict]:
    """
    🎯 목적: 특정 사용자의 채팅 기록 조회

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - user_id (str): 사용자 ID (None이면 현재 사용자)
    - limit (int): 조회할 기록 수

    📤 출력:
    - List[Dict]: 채팅 기록 리스트
    """

    try:
        # 사용자 ID 확인
        if not user_id:
            user = get_current_user()
            if not user:
                return []
            user_id = user.get("user_id", "")

        # 채팅 기록 필터링
        if "chat_history" not in data:
            return []

        user_chats = [
            chat for chat in data["chat_history"]
            if chat.get("user_id") == user_id
        ]

        # 최신순 정렬 및 제한
        user_chats.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return user_chats[:limit]

    except Exception as e:
        logger.error(f"사용자 채팅 기록 조회 중 오류 발생: {e}")
        return []

def get_chatbot_usage_stats(data: Dict) -> Dict[str, Any]:
    """
    🎯 목적: 챗봇별 사용 통계 조회

    📊 입력:
    - data (Dict): 메인 데이터 저장소

    📤 출력:
    - Dict: 챗봇별 사용 통계
    """

    try:
        if "chat_history" not in data:
            return {}

        stats = {}

        for chat in data["chat_history"]:
            chatbot_type = chat.get("chatbot_type", "unknown")

            if chatbot_type not in stats:
                stats[chatbot_type] = {
                    "total_conversations": 0,
                    "unique_users": set(),
                    "total_messages": 0,
                    "avg_message_length": 0,
                    "avg_response_length": 0
                }

            stats[chatbot_type]["total_conversations"] += 1
            stats[chatbot_type]["unique_users"].add(chat.get("username", "unknown"))
            stats[chatbot_type]["total_messages"] += 1

            # 평균 길이 계산
            msg_len = chat.get("message_length", 0)
            resp_len = chat.get("response_length", 0)

            current_avg_msg = stats[chatbot_type]["avg_message_length"]
            current_avg_resp = stats[chatbot_type]["avg_response_length"]
            total_msgs = stats[chatbot_type]["total_messages"]

            stats[chatbot_type]["avg_message_length"] = (
                (current_avg_msg * (total_msgs - 1) + msg_len) / total_msgs
            )
            stats[chatbot_type]["avg_response_length"] = (
                (current_avg_resp * (total_msgs - 1) + resp_len) / total_msgs
            )

        # set을 리스트로 변환 (JSON 직렬화를 위해)
        for chatbot_type in stats:
            stats[chatbot_type]["unique_users"] = len(stats[chatbot_type]["unique_users"])

        return stats

    except Exception as e:
        logger.error(f"챗봇 사용 통계 조회 중 오류 발생: {e}")
        return {}

def get_search_analytics(data: Dict) -> Dict[str, Any]:
    """
    🎯 목적: 검색 분석 데이터 조회

    📊 입력:
    - data (Dict): 메인 데이터 저장소

    📤 출력:
    - Dict: 검색 분석 결과
    """

    try:
        if "search_logs" not in data:
            return {
                "total_searches": 0,
                "unique_users": 0,
                "popular_terms": [],
                "category_distribution": {},
                "search_trends": []
            }

        search_logs = data["search_logs"]

        # 기본 통계
        total_searches = len(search_logs)
        unique_users = len(set(log.get("username", "unknown") for log in search_logs))

        # 인기 검색어 (상위 10개)
        term_counts = {}
        for log in search_logs:
            term = log.get("search_term", "")
            term_counts[term] = term_counts.get(term, 0) + 1

        popular_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # 카테고리 분포
        category_counts = {}
        for log in search_logs:
            category = log.get("category_filter", "전체")
            category_counts[category] = category_counts.get(category, 0) + 1

        # 검색 트렌드 (최근 7일)
        from datetime import datetime, timedelta
        today = datetime.now()
        trends = []

        for i in range(7):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            count = sum(1 for log in search_logs if log.get("timestamp", "").startswith(date))
            trends.append({"date": date, "count": count})

        trends.reverse()  # 오래된 순으로 정렬

        return {
            "total_searches": total_searches,
            "unique_users": unique_users,
            "popular_terms": popular_terms,
            "category_distribution": category_counts,
            "search_trends": trends
        }

    except Exception as e:
        logger.error(f"검색 분석 데이터 조회 중 오류 발생: {e}")
        return {}

def cleanup_old_logs(data: Dict, days_to_keep: int = 30) -> None:
    """
    🎯 목적: 오래된 로그 데이터 정리

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - days_to_keep (int): 보관할 일수

    🔄 처리 흐름:
    1. 기준 날짜 계산
    2. 오래된 채팅 기록 삭제
    3. 오래된 검색 로그 삭제
    4. 데이터 저장
    """

    try:
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")

        # 채팅 기록 정리
        if "chat_history" in data:
            original_count = len(data["chat_history"])
            data["chat_history"] = [
                chat for chat in data["chat_history"]
                if chat.get("timestamp", "").split()[0] >= cutoff_date
            ]
            cleaned_count = original_count - len(data["chat_history"])
            logger.info(f"채팅 기록 정리: {cleaned_count}개 삭제")

        # 검색 로그 정리
        if "search_logs" in data:
            original_count = len(data["search_logs"])
            data["search_logs"] = [
                log for log in data["search_logs"]
                if log.get("timestamp", "").split()[0] >= cutoff_date
            ]
            cleaned_count = original_count - len(data["search_logs"])
            logger.info(f"검색 로그 정리: {cleaned_count}개 삭제")

        # 데이터 저장
        save_data(data)
        logger.info(f"로그 정리 완료: {days_to_keep}일 이전 데이터 삭제")

    except Exception as e:
        logger.error(f"로그 정리 중 오류 발생: {e}")

def export_chat_history(data: Dict, user_id: str = None, format: str = "json") -> str:
    """
    🎯 목적: 채팅 기록 내보내기

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - user_id (str): 사용자 ID (None이면 전체)
    - format (str): 내보내기 형식 ("json", "csv")

    📤 출력:
    - str: 내보낸 데이터 문자열
    """

    try:
        # 데이터 필터링
        if user_id:
            chat_data = [
                chat for chat in data.get("chat_history", [])
                if chat.get("user_id") == user_id
            ]
        else:
            chat_data = data.get("chat_history", [])

        if format.lower() == "json":
            return json.dumps(chat_data, ensure_ascii=False, indent=2)

        elif format.lower() == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            if chat_data:
                fieldnames = chat_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(chat_data)

            return output.getvalue()

        else:
            logger.warning(f"지원하지 않는 형식: {format}")
            return ""

    except Exception as e:
        logger.error(f"채팅 기록 내보내기 중 오류 발생: {e}")
        return ""