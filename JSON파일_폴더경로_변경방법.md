# JSON 파일 폴더 경로 변경 방법 가이드

## 🎯 개요
현재 모든 JSON 파일은 `datalog/` 폴더에 저장되고 있습니다. 다른 경로로 변경하고 싶다면 **config.py 파일 1개만** 수정하면 됩니다.

## 📝 현재 설정 위치

### **변경해야 하는 파일: `config.py` (25~27번째 줄)**
```python
# 프로젝트 루트 디렉토리 및 데이터 저장 폴더 설정
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(PROJECT_ROOT, "datalog")  # ← 이 부분만 변경!
```

## 🔧 폴더 경로 변경 방법

### **방법 1: 프로젝트 내부 다른 폴더로 변경**
```python
# 예시 1: data 폴더로 변경
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")

# 예시 2: storage 폴더로 변경
DATA_FOLDER = os.path.join(PROJECT_ROOT, "storage")

# 예시 3: json_files 폴더로 변경
DATA_FOLDER = os.path.join(PROJECT_ROOT, "json_files")

# 예시 4: 하위 폴더 depth 추가
DATA_FOLDER = os.path.join(PROJECT_ROOT, "database", "json")
```

### **방법 2: 절대 경로로 변경 (프로젝트 외부)**
```python
# 예시 1: C 드라이브의 특정 폴더
DATA_FOLDER = r"C:\AE_WIKI_Data"

# 예시 2: 사용자 문서 폴더
import os
DATA_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "AE_WIKI_Data")

# 예시 3: 네트워크 드라이브 (주의: 권한 필요)
DATA_FOLDER = r"\\server\shared\AE_WIKI_Data"
```

### **방법 3: 환경변수 사용 (운영환경 권장)**
```python
# 환경변수에서 경로 읽기 (없으면 기본값 사용)
DATA_FOLDER = os.getenv("AE_WIKI_DATA_PATH", os.path.join(PROJECT_ROOT, "datalog"))
```

## 📋 구체적인 변경 절차

### **1단계: config.py 수정**
```python
# config.py의 27번째 줄을 원하는 경로로 변경
# 현재:
DATA_FOLDER = os.path.join(PROJECT_ROOT, "datalog")

# 변경 예시 (data 폴더로 변경):
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")
```

### **2단계: 기존 JSON 파일 이동 (선택사항)**
```bash
# 기존 JSON 파일들을 새 경로로 이동
cd "프로젝트폴더"
mkdir data                    # 새 폴더 생성
mv datalog/*.json data/       # 기존 파일 이동
rmdir datalog                 # 빈 폴더 제거
```

### **3단계: 애플리케이션 재시작**
- 실행 중인 Streamlit 앱 종료
- 새로 시작하면 자동으로 새 경로 사용

## 🔄 변경 후 자동으로 적용되는 파일들

**config.py만 수정하면 다음 모든 파일에서 자동으로 새 경로 사용:**

### **주요 JSON 파일들**
- ✅ `knowledge_data.json` - 메인 데이터
- ✅ `users_data.json` - 사용자 프로필
- ✅ `learning_requests.json` - 학습 요청
- ✅ `voc_data.json` - VOC 데이터
- ✅ `user_conversations.json` - 대화 기록
- ✅ `users_management.json` - 사용자 관리

### **연동되는 Python 파일들**
- ✅ `user_manager.py` - 자동으로 새 경로 사용
- ✅ `pages/5_✨WIKI_학습시키기.py` - 자동으로 새 경로 사용
- ✅ `pages/8_📝_VOC.py` - 자동으로 새 경로 사용
- ✅ `pages/9_⚙️_관리자.py` - 자동으로 새 경로 사용
- ✅ `conversation_manager.py` - 자동으로 새 경로 사용

## ⚠️ 주의사항

### **권한 관리**
```python
# 새 폴더에 쓰기 권한이 있는지 확인
import os
new_path = r"C:\새로운경로"
if not os.access(new_path, os.W_OK):
    print("쓰기 권한 없음!")
```

### **네트워크 경로 사용 시**
```python
# 네트워크 연결 상태 확인
if not os.path.exists(DATA_FOLDER):
    print(f"경로에 접근할 수 없음: {DATA_FOLDER}")
```

### **백업 권장**
기존 JSON 파일들을 백업해두는 것을 권장합니다:
```bash
# 백업 생성
cp -r datalog datalog_backup_20250915
```

## 🚀 실제 변경 예시

### **예시 1: `database` 폴더로 변경**

**config.py 수정:**
```python
# 수정 전
DATA_FOLDER = os.path.join(PROJECT_ROOT, "datalog")

# 수정 후
DATA_FOLDER = os.path.join(PROJECT_ROOT, "database")
```

**결과:**
```
프로젝트폴더/
├── database/              # ← 새 위치
│   ├── knowledge_data.json
│   ├── users_management.json
│   └── 기타 JSON 파일들...
└── 기타 파일들...
```

### **예시 2: 절대경로로 변경**

**config.py 수정:**
```python
# 수정 전
DATA_FOLDER = os.path.join(PROJECT_ROOT, "datalog")

# 수정 후
DATA_FOLDER = r"D:\AE_WIKI_Storage"
```

**결과:**
```
D:\AE_WIKI_Storage\
├── knowledge_data.json
├── users_management.json
└── 기타 JSON 파일들...
```

## ✅ 핵심 포인트

### **🎯 수정할 파일: 단 1개**
- **`config.py`의 27번째 줄만 변경**
- 다른 파일은 건드릴 필요 없음

### **🔄 자동 연동**
- 모든 Python 파일이 config.py를 참조
- 경로 변경 시 자동으로 새 위치 사용

### **⚡ 즉시 적용**
- 앱 재시작 시 바로 적용
- 폴더가 없으면 자동 생성

이 방식으로 **config.py 1줄만 수정**하면 모든 JSON 파일의 저장 위치를 쉽게 변경할 수 있습니다!