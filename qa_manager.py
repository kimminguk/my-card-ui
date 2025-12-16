"""
=================================================================
❓ AE WIKI - Q&A 관리자 모듈 (qa_manager.py)
=================================================================

📋 파일 역할:
- 질문/답변 시스템 관리
- 검색 및 필터링 기능
- 좋아요 시스템 및 랭킹
- 사용자 등록 요청 처리

🔗 주요 컴포넌트:
- 질문 등록/검색/삭제
- 답변 작성/좋아요 기능
- 사용자 등록 요청 승인/거부
- 랭킹 시스템
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from auth_manager import get_current_user, get_user_id, get_username
from data_manager import save_data, load_users_data, save_users_data

logger = logging.getLogger(__name__)

def search_questions(data: Dict, search_term: str = "", category_filter: str = "전체") -> List[Dict]:
    """
    🎯 목적: 질문 검색 및 필터링

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - search_term (str): 검색어
    - category_filter (str): 카테고리 필터

    📤 출력:
    - List[Dict]: 검색된 질문 리스트
    """

    try:
        questions = data.get("questions", [])

        # 검색어 필터링
        if search_term:
            search_term = search_term.lower()
            questions = [
                q for q in questions
                if search_term in q.get("title", "").lower() or
                   search_term in q.get("content", "").lower()
            ]

        # 카테고리 필터링
        if category_filter and category_filter != "전체":
            questions = [
                q for q in questions
                if q.get("category", "") == category_filter
            ]

        # 최신순 정렬
        questions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return questions

    except Exception as e:
        logger.error(f"질문 검색 중 오류 발생: {e}")
        return []

def add_question(data: Dict, title: str, category: str, content: str, anonymous: bool = False) -> str:
    """
    🎯 목적: 새 질문 등록

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - title (str): 질문 제목
    - category (str): 카테고리
    - content (str): 질문 내용
    - anonymous (bool): 익명 여부

    📤 출력:
    - str: 생성된 질문 ID
    """

    try:
        # 사용자 정보 확인
        user = get_current_user()
        if not user:
            logger.warning("질문 등록 실패: 사용자 정보 없음")
            return ""

        # 질문 ID 생성
        question_id = f"q_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # 질문 데이터 구조화
        question_data = {
            "id": question_id,
            "title": title,
            "category": category,
            "content": content,
            "author": "익명" if anonymous else user.get("nickname", "알 수 없음"),
            "author_id": user.get("user_id", ""),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "anonymous": anonymous,
            "views": 0,
            "tags": []  # 향후 확장용
        }

        # 데이터에 추가
        if "questions" not in data:
            data["questions"] = []

        data["questions"].append(question_data)

        # 포인트 적립 (익명이 아닌 경우만)
        if not anonymous:
            from utils import add_user_points
            username = user.get("knox_id") or user.get("username", "")
            if username:
                add_user_points(data, username, 100, "질문 작성")
                logger.info(f"포인트 적립: {username} +100P (질문 작성)")

        # 데이터 저장
        save_data(data)

        logger.info(f"질문 등록 완료: {question_id} by {user.get('username', 'unknown')}")
        return question_id

    except Exception as e:
        logger.error(f"질문 등록 중 오류 발생: {e}")
        return ""

def add_answer(data: Dict, question_id: str, content: str) -> str:
    """
    🎯 목적: 질문에 답변 추가

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - question_id (str): 질문 ID
    - content (str): 답변 내용

    📤 출력:
    - str: 생성된 답변 ID
    """

    try:
        # 사용자 정보 확인
        user = get_current_user()
        if not user:
            logger.warning("답변 등록 실패: 사용자 정보 없음")
            return ""

        # 답변 ID 생성
        answer_id = f"a_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # 답변 데이터 구조화
        answer_data = {
            "id": answer_id,
            "question_id": question_id,
            "content": content,
            "author": user.get("nickname", "알 수 없음"),
            "author_id": user.get("user_id", ""),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "likes": 0,
            "helpful": False  # 채택 여부 (향후 기능)
        }

        # 데이터에 추가
        if "answers" not in data:
            data["answers"] = []

        data["answers"].append(answer_data)

        # 포인트 적립
        from utils import add_user_points
        username = user.get("knox_id") or user.get("username", "")
        if username:
            add_user_points(data, username, 100, "답변 작성")
            logger.info(f"포인트 적립: {username} +100P (답변 작성)")

        # 데이터 저장
        save_data(data)

        logger.info(f"답변 등록 완료: {answer_id} for {question_id}")
        return answer_id

    except Exception as e:
        logger.error(f"답변 등록 중 오류 발생: {e}")
        return ""

def toggle_like(data: Dict, answer_id: str) -> bool:
    """
    🎯 목적: 답변 좋아요 토글

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - answer_id (str): 답변 ID

    📤 출력:
    - bool: 좋아요 추가됨(True) / 제거됨(False)
    """

    try:
        user = get_current_user()
        if not user:
            logger.warning("좋아요 처리 실패: 사용자 정보 없음")
            return False

        username = user.get("username", "")

        # 좋아요 데이터 초기화
        if "likes" not in data:
            data["likes"] = {}

        like_key = f"answer_{answer_id}"
        if like_key not in data["likes"]:
            data["likes"][like_key] = []

        # 좋아요 토글
        if username in data["likes"][like_key]:
            # 좋아요 제거
            data["likes"][like_key].remove(username)
            liked = False
        else:
            # 좋아요 추가
            data["likes"][like_key].append(username)
            liked = True

            # 좋아요 추가 시 포인트 적립 (답변 작성자에게)
            # 답변 작성자 찾기
            answer = next((a for a in data.get("answers", []) if a["id"] == answer_id), None)
            if answer:
                answer_author_id = answer.get("author_id", "")
                # 답변 작성자의 username(knox_id) 찾기
                from utils import get_all_users
                users = get_all_users()
                answer_author = next((u for u in users if u.get("user_id") == answer_author_id), None)
                if answer_author:
                    answer_author_username = answer_author.get("knox_id") or answer_author.get("username", "")
                    if answer_author_username:
                        from utils import add_user_points
                        add_user_points(data, answer_author_username, 10, "답변 좋아요 받음")
                        logger.info(f"포인트 적립: {answer_author_username} +10P (좋아요 받음)")

        # 데이터 저장
        save_data(data)

        logger.info(f"좋아요 토글: {answer_id} by {username} -> {liked}")
        return liked

    except Exception as e:
        logger.error(f"좋아요 토글 중 오류 발생: {e}")
        return False

def delete_question(data: Dict, question_id: str) -> None:
    """
    🎯 목적: 질문 삭제

    📊 입력:
    - data (Dict): 메인 데이터 저장소
    - question_id (str): 삭제할 질문 ID
    """

    try:
        # 질문 삭제
        if "questions" in data:
            data["questions"] = [
                q for q in data["questions"]
                if q.get("id") != question_id
            ]

        # 관련 답변 삭제
        if "answers" in data:
            data["answers"] = [
                a for a in data["answers"]
                if a.get("question_id") != question_id
            ]

        # 관련 좋아요 삭제
        if "likes" in data:
            # 해당 질문의 답변들의 좋아요 삭제
            keys_to_remove = [
                key for key in data["likes"].keys()
                if key.startswith("answer_") and
                any(a.get("question_id") == question_id for a in data.get("answers", [])
                    if key == f"answer_{a.get('id')}")
            ]
            for key in keys_to_remove:
                del data["likes"][key]

        # 데이터 저장
        save_data(data)

        logger.info(f"질문 삭제 완료: {question_id}")

    except Exception as e:
        logger.error(f"질문 삭제 중 오류 발생: {e}")

def get_answer_ranking(data: Dict) -> List[tuple]:
    """
    🎯 목적: 답변 기반 사용자 랭킹 조회

    📊 입력:
    - data (Dict): 메인 데이터 저장소

    📤 출력:
    - List[tuple]: (사용자명, 답변수) 순으로 정렬된 리스트
    """

    try:
        answers = data.get("answers", [])
        user_counts = {}

        for answer in answers:
            author = answer.get("author", "알 수 없음")
            if author != "알 수 없음" and author != "익명":
                user_counts[author] = user_counts.get(author, 0) + 1

        # 답변 수 기준 내림차순 정렬
        ranking = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        return ranking

    except Exception as e:
        logger.error(f"답변 랭킹 조회 중 오류 발생: {e}")
        return []

def get_question_statistics(data: Dict) -> Dict[str, Any]:
    """
    🎯 목적: 질문 통계 조회

    📊 입력:
    - data (Dict): 메인 데이터 저장소

    📤 출력:
    - Dict: 질문 관련 통계 정보
    """

    try:
        questions = data.get("questions", [])
        answers = data.get("answers", [])

        # 기본 통계
        total_questions = len(questions)
        total_answers = len(answers)

        # 카테고리별 분포
        category_counts = {}
        for question in questions:
            category = question.get("category", "기타")
            category_counts[category] = category_counts.get(category, 0) + 1

        # 답변 수별 질문 분포
        answer_distribution = {
            "no_answer": 0,
            "one_answer": 0,
            "multiple_answers": 0
        }

        for question in questions:
            question_id = question.get("id", "")
            question_answers = [a for a in answers if a.get("question_id") == question_id]
            answer_count = len(question_answers)

            if answer_count == 0:
                answer_distribution["no_answer"] += 1
            elif answer_count == 1:
                answer_distribution["one_answer"] += 1
            else:
                answer_distribution["multiple_answers"] += 1

        # 활발한 사용자 (질문 + 답변)
        user_activity = {}
        for question in questions:
            author = question.get("author", "")
            if author and author != "익명":
                user_activity[author] = user_activity.get(author, {"questions": 0, "answers": 0})
                user_activity[author]["questions"] += 1

        for answer in answers:
            author = answer.get("author", "")
            if author and author != "익명":
                user_activity[author] = user_activity.get(author, {"questions": 0, "answers": 0})
                user_activity[author]["answers"] += 1

        # 총 활동 기준 정렬
        top_users = sorted(
            user_activity.items(),
            key=lambda x: x[1]["questions"] + x[1]["answers"],
            reverse=True
        )[:10]

        return {
            "total_questions": total_questions,
            "total_answers": total_answers,
            "category_distribution": category_counts,
            "answer_distribution": answer_distribution,
            "top_users": top_users,
            "avg_answers_per_question": total_answers / total_questions if total_questions > 0 else 0
        }

    except Exception as e:
        logger.error(f"질문 통계 조회 중 오류 발생: {e}")
        return {}

def submit_registration_request(username: str, name: str, department: str, password: str) -> Tuple[bool, str]:
    """
    🎯 목적: 사용자 등록 요청 제출 (새로운 user_manager.py 시스템 사용)

    📊 입력:
    - username (str): Knox ID (녹스아이디)
    - name (str): 실명
    - department (str): 부서
    - password (str): 비밀번호

    📤 출력:
    - Tuple[bool, str]: (성공여부, 메시지)
    """

    try:
        # user_manager.py의 add_registration_request 함수 사용
        from user_manager import add_registration_request

        # knox_id = username으로 전달 (Knox ID)
        success, message = add_registration_request(
            knox_id=username,
            name=name,
            department=department,
            password=password
        )

        logger.info(f"등록 요청 제출: {username} - {message}")
        return success, message

    except Exception as e:
        logger.error(f"등록 요청 제출 중 오류 발생: {e}")
        return False, f"등록 요청 처리 중 오류가 발생했습니다: {str(e)}"

def get_pending_registration_requests(data: Dict) -> List[Dict]:
    """
    🎯 목적: 대기 중인 등록 요청 조회 (user_manager.py 사용)

    📊 입력:
    - data (Dict): 메인 데이터 저장소 (하위 호환성을 위해 유지)

    📤 출력:
    - List[Dict]: 대기 중인 등록 요청 리스트
    """

    try:
        from user_manager import get_pending_requests
        return get_pending_requests()

    except Exception as e:
        logger.error(f"대기 중인 등록 요청 조회 중 오류 발생: {e}")
        return []

def approve_registration_request(data: Dict, request_id: str, admin_username: str) -> Tuple[bool, str]:
    """
    🎯 목적: 등록 요청 승인 (user_manager.py 사용)

    📊 입력:
    - data (Dict): 메인 데이터 저장소 (하위 호환성을 위해 유지)
    - request_id (str): 요청 ID
    - admin_username (str): 승인 관리자

    📤 출력:
    - Tuple[bool, str]: (성공여부, 메시지)
    """

    try:
        from user_manager import approve_registration_request as approve_req
        success, message = approve_req(request_id, admin_username)

        logger.info(f"등록 요청 승인: request_id={request_id} by {admin_username} - {message}")
        return success, message

    except Exception as e:
        logger.error(f"등록 요청 승인 중 오류 발생: {e}")
        return False, f"등록 요청 승인 중 오류가 발생했습니다: {str(e)}"

def reject_registration_request(data: Dict, request_id: str, admin_username: str, reason: str = "") -> Tuple[bool, str]:
    """
    🎯 목적: 등록 요청 거부 (user_manager.py 사용)

    📊 입력:
    - data (Dict): 메인 데이터 저장소 (하위 호환성을 위해 유지)
    - request_id (str): 요청 ID
    - admin_username (str): 거부 관리자
    - reason (str): 거부 사유

    📤 출력:
    - Tuple[bool, str]: (성공여부, 메시지)
    """

    try:
        from user_manager import reject_registration_request as reject_req
        success, message = reject_req(request_id, admin_username, reason)

        logger.info(f"등록 요청 거부: request_id={request_id} by {admin_username} - {message}")
        return success, message

    except Exception as e:
        logger.error(f"등록 요청 거부 중 오류 발생: {e}")
        return False, f"등록 요청 거부 중 오류가 발생했습니다: {str(e)}"

def get_qa_activity_summary(data: Dict) -> Dict[str, Any]:
    """
    🎯 목적: Q&A 활동 요약 통계

    📊 입력:
    - data (Dict): 메인 데이터 저장소

    📤 출력:
    - Dict: Q&A 활동 요약
    """

    try:
        from datetime import datetime, timedelta

        questions = data.get("questions", [])
        answers = data.get("answers", [])
        today = datetime.now()

        # 오늘, 이번 주, 이번 달 통계
        today_str = today.strftime("%Y-%m-%d")
        week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")

        stats = {
            "today": {"questions": 0, "answers": 0},
            "this_week": {"questions": 0, "answers": 0},
            "this_month": {"questions": 0, "answers": 0},
            "total": {"questions": len(questions), "answers": len(answers)}
        }

        # 질문 통계
        for question in questions:
            q_date = question.get("timestamp", "").split()[0]
            if q_date == today_str:
                stats["today"]["questions"] += 1
            if q_date >= week_ago:
                stats["this_week"]["questions"] += 1
            if q_date >= month_ago:
                stats["this_month"]["questions"] += 1

        # 답변 통계
        for answer in answers:
            a_date = answer.get("timestamp", "").split()[0]
            if a_date == today_str:
                stats["today"]["answers"] += 1
            if a_date >= week_ago:
                stats["this_week"]["answers"] += 1
            if a_date >= month_ago:
                stats["this_month"]["answers"] += 1

        # 추가 지표
        stats["unanswered_questions"] = len([
            q for q in questions
            if not any(a.get("question_id") == q.get("id") for a in answers)
        ])

        stats["most_active_users"] = get_answer_ranking(data)[:5]

        return stats

    except Exception as e:
        logger.error(f"Q&A 활동 요약 조회 중 오류 발생: {e}")
        return {}