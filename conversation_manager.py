"""
=================================================================
💬 AE WIKI - 대화 관리자 (conversation_manager.py) 
=================================================================

📋 파일 역할:
- 챗봇별 대화 맥락을 슬라이딩 윈도우 방식으로 관리
- 사용자별/챗봇별 최근 N개 대화만 유지하여 메모리 효율성과 응답 품질 동시 향상
- LLM API 호출 시 적절한 대화 맥락 제공으로 연속 대화 품질 보장

🔗 주요 컴포넌트:
- ConversationManager: 메인 대화 관리 클래스
- 슬라이딩 윈도우: 최신 5~10개 대화만 메모리에 유지
- 자동 정리: 오래된 대화 데이터 주기적 정리
- 사용자별 격리: 각 사용자의 대화 맥락 독립 관리

📊 입출력 데이터:
- 입력: 사용자 질문, 챗봇 응답, 사용자 ID, 챗봇 타입
- 출력: 최근 대화 맥락 리스트 (LLM API 전달용)
- 저장: conversations.json 파일에 영구 보관

🔄 연동 관계:
- utils.py: get_chatbot_response() 에서 대화 맥락 조회/저장
- 3개 챗봇 페이지: 각 챗봇별 독립적인 대화 맥락 관리
- config.py: MISC_CONFIG["conversation_window_size"] 설정 참조

⚡ 처리 흐름:
질문 입력 -> 사용자별 최근 대화 조회 -> LLM 호출 시 맥락 전달 
-> 응답 생성 -> 새 대화 저장 -> 윈도우 크기 초과시 오래된 대화 제거
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import deque
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    🎯 슬라이딩 윈도우 기반 대화 맥락 관리자
    
    핵심 기능:
    - 사용자별/챗봇별 대화 맥락을 슬라이딩 윈도우로 관리
    - 최신 N개 대화만 메모리 유지로 성능 최적화
    - LLM API 호출 시 적절한 대화 맥락 제공
    - 자동 정리로 디스크 공간 효율적 관리
    
    사용 패턴:
    - utils.get_chatbot_response() 에서 인스턴스 생성 후 활용
    - add_conversation() -> get_recent_conversations() -> LLM 호출
    """
    
    def __init__(self, 
                 window_size: int = 5,
                 storage_file: str = "conversations.json",
                 auto_cleanup: bool = True,
                 cleanup_interval_hours: int = 24):
        """
        🚀 대화 관리자 초기화
        
        슬라이딩 윈도우 크기와 저장 정책을 설정하고 기존 대화 데이터를 복원합니다.
        시스템 시작 시 한 번 호출되어 전체 대화 관리 인프라를 준비합니다.
        
        Args:
            window_size (int): 사용자별 유지할 최대 대화 수 (기본값: 5)
                             - 메모리 사용량과 대화 품질의 균형점
                             - config.py의 conversation_window_size 와 연동
            storage_file (str): 대화 영구 저장용 JSON 파일명
                              - 앱 재시작 후에도 대화 맥락 복원 가능
            auto_cleanup (bool): 자동 정리 기능 활성화 여부
                               - True: 주기적으로 오래된 대화 데이터 삭제
            cleanup_interval_hours (int): 자동 정리 주기 (시간 단위)
                                        - 24시간마다 오래된 대화 정리 권장
        
        초기화 작업:
        1. 설정값 저장 및 변환 (시간 -> 초)
        2. 메모리 구조 준비 (사용자별 deque 딕셔너리)
        3. 디스크 저장소 초기화 또는 기존 데이터 복원
        4. 자동 정리 타이머 시작
        """
        self.window_size = window_size
        self.storage_file = storage_file
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval_hours * 3600  # 초 단위로 변환
        
        # 사용자별 대화 윈도우 저장 (메모리)
        self._conversations = {}  # user_id -> deque of conversations
        
        # 마지막 정리 시간 추적
        self._last_cleanup = time.time()
        
        # 저장소 초기화
        self._init_storage()
    
    def _init_storage(self):
        """저장소 초기화"""
        if not os.path.exists(self.storage_file):
            self._save_to_storage({
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "conversations": {},
                "metadata": {
                    "window_size": self.window_size,
                    "auto_cleanup": self.auto_cleanup
                }
            })
        else:
            self._load_from_storage()
    
    def _save_to_storage(self, data: Dict):
        """데이터를 저장소에 저장"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversations: {e}")
    
    def _load_from_storage(self):
        """저장소에서 데이터 로드"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 저장된 대화들을 메모리로 로드 (윈도우 크기만큼만)
            conversations = data.get("conversations", {})
            for user_id, user_conversations in conversations.items():
                # 최신 순으로 정렬하고 윈도우 크기만큼만 유지
                sorted_convs = sorted(user_conversations, 
                                    key=lambda x: x.get("timestamp", ""), 
                                    reverse=True)
                self._conversations[user_id] = deque(
                    sorted_convs[:self.window_size], 
                    maxlen=self.window_size
                )
            
            logger.info(f"Loaded conversations for {len(self._conversations)} users")
            
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")
            self._conversations = {}
    
    def _sync_to_storage(self):
        """메모리의 대화들을 저장소에 동기화"""
        try:
            # 현재 저장소 데이터 로드
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "conversations": {},
                    "metadata": {}
                }
            
            # 메모리 데이터로 업데이트
            data["conversations"] = {}
            for user_id, conversations in self._conversations.items():
                data["conversations"][user_id] = list(conversations)
            
            data["last_updated"] = datetime.now().isoformat()
            data["metadata"]["window_size"] = self.window_size
            
            self._save_to_storage(data)
            
        except Exception as e:
            logger.error(f"Failed to sync to storage: {e}")
    
    def add_conversation(self, user_id: str, user_message: str, bot_response: str, 
                        conversation_type: str = "general", metadata: Optional[Dict] = None):
        """
        새 대화 추가 (슬라이딩 윈도우 방식)
        
        Args:
            user_id: 사용자 ID
            user_message: 사용자 메시지
            bot_response: 봇 응답
            conversation_type: 대화 유형 ("ae_wiki", "glossary", "jedec")
            metadata: 추가 메타데이터
        """
        if user_id not in self._conversations:
            self._conversations[user_id] = deque(maxlen=self.window_size)
        
        conversation = {
            "id": self._generate_conversation_id(),
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "conversation_type": conversation_type,
            "metadata": metadata or {},
            "message_count": 2  # 사용자 + 봇 = 2개 메시지
        }
        
        # 슬라이딩 윈도우에 추가 (자동으로 가장 오래된 것 제거)
        self._conversations[user_id].append(conversation)
        
        # 저장소에 동기화
        self._sync_to_storage()
        
        # 자동 정리 실행 (필요시)
        if self.auto_cleanup:
            self._auto_cleanup_if_needed()
        
        logger.info(f"Added conversation for user {user_id}, window size: {len(self._conversations[user_id])}")
    
    def get_recent_conversations(self, user_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        사용자의 최근 대화 반환
        
        Args:
            user_id: 사용자 ID  
            limit: 반환할 최대 대화 수 (None이면 윈도우 크기만큼)
        
        Returns:
            최신 순으로 정렬된 대화 리스트
        """
        if user_id not in self._conversations:
            return []
        
        conversations = list(self._conversations[user_id])
        conversations.reverse()  # 최신 순으로 정렬
        
        if limit:
            conversations = conversations[:limit]
        
        return conversations
    
    def get_conversation_context(self, user_id: str, include_metadata: bool = False) -> List[Dict]:
        """
        LLM에 전달할 대화 맥락 반환 (role 기반 포맷)
        
        Args:
            user_id: 사용자 ID
            include_metadata: 메타데이터 포함 여부
        
        Returns:
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}] 형식
        """
        conversations = self.get_recent_conversations(user_id)
        context = []
        
        for conv in reversed(conversations):  # 시간순으로 정렬
            # 사용자 메시지 추가
            user_msg = {"role": "user", "content": conv["user_message"]}
            if include_metadata:
                user_msg["metadata"] = {
                    "timestamp": conv["timestamp"],
                    "conversation_type": conv["conversation_type"]
                }
            context.append(user_msg)
            
            # 봇 응답 추가
            bot_msg = {"role": "assistant", "content": conv["bot_response"]}
            if include_metadata:
                bot_msg["metadata"] = conv.get("metadata", {})
            context.append(bot_msg)
        
        return context
    
    def get_user_stats(self, user_id: str) -> Dict:
        """사용자 대화 통계 반환"""
        if user_id not in self._conversations:
            return {"conversation_count": 0, "window_size": self.window_size, "is_full": False}
        
        conversations = self._conversations[user_id]
        return {
            "conversation_count": len(conversations),
            "window_size": self.window_size,
            "is_full": len(conversations) == self.window_size,
            "oldest_conversation": conversations[0]["timestamp"] if conversations else None,
            "newest_conversation": conversations[-1]["timestamp"] if conversations else None,
            "conversation_types": list(set(conv["conversation_type"] for conv in conversations))
        }
    
    def clear_user_conversations(self, user_id: str) -> bool:
        """사용자의 모든 대화 삭제"""
        if user_id in self._conversations:
            del self._conversations[user_id]
            self._sync_to_storage()
            logger.info(f"Cleared all conversations for user {user_id}")
            return True
        return False
    
    def get_all_users_stats(self) -> Dict:
        """전체 사용자 통계"""
        total_conversations = sum(len(convs) for convs in self._conversations.values())
        active_users = len([uid for uid, convs in self._conversations.items() if len(convs) > 0])
        
        return {
            "total_users": len(self._conversations),
            "active_users": active_users,
            "total_conversations": total_conversations,
            "window_size": self.window_size,
            "average_conversations_per_user": total_conversations / len(self._conversations) if self._conversations else 0
        }
    
    def _generate_conversation_id(self) -> str:
        """고유한 대화 ID 생성"""
        import uuid
        return f"conv_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    
    def _auto_cleanup_if_needed(self):
        """필요시 자동 정리 실행"""
        current_time = time.time()
        if current_time - self._last_cleanup > self.cleanup_interval:
            self._cleanup_old_data()
            self._last_cleanup = current_time
    
    def _cleanup_old_data(self):
        """오래된 데이터 정리 (메모리 최적화)"""
        # 비활성 사용자 정리 (30일 이상 대화 없음)
        cutoff_time = datetime.now() - timedelta(days=30)
        cutoff_iso = cutoff_time.isoformat()
        
        users_to_remove = []
        for user_id, conversations in self._conversations.items():
            if conversations and conversations[-1]["timestamp"] < cutoff_iso:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self._conversations[user_id]
            logger.info(f"Removed inactive user conversations: {user_id}")
        
        if users_to_remove:
            self._sync_to_storage()
            logger.info(f"Cleaned up {len(users_to_remove)} inactive users")
    
    def update_window_size(self, new_size: int):
        """윈도우 크기 업데이트"""
        old_size = self.window_size
        self.window_size = new_size
        
        # 기존 대화 윈도우들 크기 조정
        for user_id in self._conversations:
            old_conversations = list(self._conversations[user_id])
            self._conversations[user_id] = deque(
                old_conversations[-new_size:] if len(old_conversations) > new_size else old_conversations,
                maxlen=new_size
            )
        
        self._sync_to_storage()
        logger.info(f"Updated window size from {old_size} to {new_size}")
    
    def export_conversations(self, user_id: Optional[str] = None) -> Dict:
        """대화 내보내기"""
        if user_id:
            return {
                "user_id": user_id,
                "conversations": list(self._conversations.get(user_id, [])),
                "exported_at": datetime.now().isoformat()
            }
        else:
            return {
                "all_users": {uid: list(convs) for uid, convs in self._conversations.items()},
                "exported_at": datetime.now().isoformat(),
                "stats": self.get_all_users_stats()
            }


# ====================================
# 🔧 Streamlit 통합 헬퍼 함수들
# ====================================

def get_conversation_manager() -> ConversationManager:
    """전역 대화 관리자 인스턴스 반환 (싱글톤 패턴)"""
    if 'conversation_manager' not in st.session_state:
        try:
            from config import MISC_CONFIG
            window_size = MISC_CONFIG.get("conversation_window_size", 5)
            cleanup_hours = MISC_CONFIG.get("auto_cleanup_hours", 24)
        except ImportError:
            window_size = 5
            cleanup_hours = 24
        
        from config import DATA_CONFIG
        st.session_state.conversation_manager = ConversationManager(
            window_size=window_size,  # 설정에서 읽은 윈도우 크기
            storage_file=DATA_CONFIG["user_conversations_file"],
            auto_cleanup=True,
            cleanup_interval_hours=cleanup_hours
        )
    return st.session_state.conversation_manager

def add_conversation_to_memory(user_id: str, user_message: str, bot_response: str, 
                              conversation_type: str = "general", metadata: Optional[Dict] = None):
    """대화를 메모리에 추가 (영구 저장소만, 세션 저장은 각 페이지에서 직접 관리)"""
    manager = get_conversation_manager()
    manager.add_conversation(user_id, user_message, bot_response, conversation_type, metadata)
    
    # 중복 저장 방지를 위해 세션 저장 부분 제거
    # 각 챗봇 페이지에서 직접 st.session_state 관리

def get_conversation_context_for_llm(user_id: str) -> List[Dict]:
    """LLM에 전달할 대화 맥락 반환"""
    manager = get_conversation_manager()
    return manager.get_conversation_context(user_id, include_metadata=False)

def get_recent_conversations_for_display(user_id: str, limit: int = 5) -> List[Dict]:
    """화면 표시용 최근 대화 반환"""
    manager = get_conversation_manager()
    return manager.get_recent_conversations(user_id, limit=limit)

def clear_user_conversation_memory(user_id: str) -> bool:
    """사용자 대화 기록 삭제"""
    manager = get_conversation_manager()
    success = manager.clear_user_conversations(user_id)
    
    # Streamlit 세션에서도 삭제
    keys_to_clear = ["ae_wiki_chat_messages", "admin_chat_messages", "general_chat_messages"]
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = []
    
    return success

def get_conversation_stats(user_id: str) -> Dict:
    """사용자 대화 통계 반환"""
    manager = get_conversation_manager()
    return manager.get_user_stats(user_id)

def show_conversation_manager_widget():
    """관리자용 대화 관리 위젯 표시"""
    manager = get_conversation_manager()
    
    st.markdown("### 🧠 대화 메모리 관리")
    
    # 전체 통계
    stats = manager.get_all_users_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 사용자", stats["total_users"])
    with col2:
        st.metric("활성 사용자", stats["active_users"])
    with col3:
        st.metric("총 대화 수", stats["total_conversations"])
    with col4:
        st.metric("윈도우 크기", stats["window_size"])
    
    # 설정 조정
    st.markdown("#### ⚙️ 설정")
    
    col1, col2 = st.columns(2)
    with col1:
        new_window_size = st.slider(
            "대화 윈도우 크기", 
            min_value=1, 
            max_value=20, 
            value=manager.window_size,
            help="각 사용자별로 기억할 최대 대화 수"
        )
        
        if st.button("윈도우 크기 업데이트"):
            manager.update_window_size(new_window_size)
            st.success(f"윈도우 크기를 {new_window_size}로 변경했습니다.")
            st.rerun()
    
    with col2:
        if st.button("모든 대화 기록 내보내기"):
            export_data = manager.export_conversations()
            st.download_button(
                "📥 JSON 다운로드",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"conversations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # 사용자별 상세 정보
    st.markdown("#### 👤 사용자별 대화 현황")
    
    if manager._conversations:
        for user_id, conversations in manager._conversations.items():
            if conversations:
                with st.expander(f"사용자: {user_id} ({len(conversations)}개 대화)"):
                    user_stats = manager.get_user_stats(user_id)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**대화 수**: {user_stats['conversation_count']}")
                        st.write(f"**윈도우 상태**: {'가득참' if user_stats['is_full'] else '여유있음'}")
                    
                    with col2:
                        st.write(f"**대화 유형**: {', '.join(user_stats['conversation_types'])}")
                        if st.button(f"🗑️ 삭제", key=f"clear_{user_id}"):
                            manager.clear_user_conversations(user_id)
                            st.success(f"{user_id}의 대화를 삭제했습니다.")
                            st.rerun()
    else:
        st.info("저장된 대화가 없습니다.")