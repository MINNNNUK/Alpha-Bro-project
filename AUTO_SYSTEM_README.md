# 정부지원사업 자동화 시스템

매일 K-스타트업과 기업마당에서 데이터를 수집하고, Supabase에 저장하며, 등록된 기업에 맞춤 추천을 생성하는 통합 자동화 시스템입니다.

## 🚀 주요 기능

### 1. 자동 데이터 수집
- **K-스타트업 API**: 정부지원사업 공고 데이터 수집
- **기업마당 API**: 중소기업 지원사업 공고 데이터 수집
- **매일 자동 실행**: 오전 9시에 자동으로 신규 공고 수집

### 2. Supabase 연동
- 수집된 공고 데이터를 Supabase에 자동 저장
- 추천 결과를 Supabase에 저장하여 실시간 조회 가능
- 기업 정보와 추천 데이터 연동

### 3. AI 기반 맞춤 추천
- OpenAI GPT 모델을 활용한 지능형 추천 시스템
- 기업 특성과 공고 내용을 분석하여 최적의 매칭
- 추천 개수 제한 없이 모든 적합한 공고 추천

### 4. Streamlit 웹 인터페이스
- 실시간 대시보드
- 기업별 맞춤 추천 조회
- 수동 데이터 수집 및 추천 생성
- 자동화 시스템 제어

## 📁 파일 구조

```
data2/
├── integrated_auto_system.py      # 통합 자동화 시스템 메인
├── auto_streamlit_app.py          # Streamlit 웹 앱
├── run_auto_system.py             # 실행 스크립트
├── config.py                      # Supabase 설정
├── env_example.txt                # 환경변수 예시
├── alpha_companies.csv            # 기업 정보 데이터
├── collected_data/                # K-스타트업 수집 데이터
├── collected_data_biz/            # 기업마당 수집 데이터
└── supabase1/                     # Supabase 관련 파일들
```

## 🛠️ 설치 및 설정

### 1. 필요한 패키지 설치
```bash
pip install streamlit pandas requests openai supabase python-dotenv schedule altair openpyxl
```

### 2. 환경변수 설정
`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

### 3. Supabase 데이터베이스 설정
다음 테이블들이 필요합니다:

#### announcements 테이블
```sql
CREATE TABLE announcements (
    id SERIAL PRIMARY KEY,
    title TEXT,
    agency TEXT,
    content TEXT,
    target TEXT,
    target_detail TEXT,
    region TEXT,
    category TEXT,
    experience TEXT,
    age_range TEXT,
    supervisor TEXT,
    application_url TEXT,
    detail_url TEXT,
    contact TEXT,
    is_active BOOLEAN,
    is_integrated BOOLEAN,
    preference TEXT,
    amount_text TEXT,
    amount_detail TEXT,
    start_date DATE,
    end_date DATE,
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

#### recommendations 테이블
```sql
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER,
    company_name TEXT,
    announcement_title TEXT,
    recommendation_score INTEGER,
    recommendation_reason TEXT,
    start_date DATE,
    end_date DATE,
    remaining_days TEXT,
    amount_text TEXT,
    amount_usage TEXT,
    status TEXT,
    year TEXT,
    month TEXT,
    rank INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## 🚀 실행 방법

### 1. Streamlit 웹 앱 실행
```bash
python run_auto_system.py
# 옵션 1 선택
```

또는 직접 실행:
```bash
streamlit run auto_streamlit_app.py
```

### 2. 통합 자동화 시스템 실행
```bash
python run_auto_system.py
# 옵션 2 선택
```

### 3. 개별 기능 실행
```bash
python run_auto_system.py
# 옵션 3 (데이터 수집만) 또는 4 (추천 생성만) 선택
```

## 📊 사용법

### 웹 인터페이스 사용법

1. **대시보드**: 시스템 현황 및 최근 수집된 공고 확인
2. **맞춤 추천**: 기업 선택 후 개인화된 추천 조회
3. **공고 목록**: 수집된 모든 공고 필터링 및 검색
4. **자동화 설정**: 수동 실행 및 스케줄러 제어

### 자동화 시스템 사용법

1. **매일 자동 실행**: 오전 9시에 자동으로 데이터 수집 및 추천 생성
2. **수동 실행**: 웹 인터페이스에서 언제든지 수동 실행 가능
3. **스케줄러 제어**: 웹 인터페이스에서 스케줄러 시작/중지

## 🔧 주요 설정

### API 키 설정
- K-스타트업 API 키: 코드에 하드코딩됨
- 기업마당 API 키: 코드에 하드코딩됨
- OpenAI API 키: 환경변수로 설정

### 추천 시스템 설정
- 추천 개수 제한 없음 (모든 적합한 공고 추천)
- GPT-4o-mini 모델 사용
- 기업 특성 기반 매칭 알고리즘

### 데이터 저장
- CSV 및 Excel 파일로 로컬 저장
- Supabase 데이터베이스에 실시간 저장
- 수집일시별 파일명 자동 생성

## 📈 모니터링

### 로그 파일
- `integrated_auto_system.log`: 자동화 시스템 로그
- `daily_new_announcement_collector.log`: 데이터 수집 로그

### 웹 대시보드
- 실시간 통계 정보
- 최근 수집된 공고 목록
- 시스템 상태 모니터링

## 🚨 주의사항

1. **API 제한**: K-스타트업과 기업마당 API의 호출 제한을 고려하여 적절한 간격으로 요청
2. **OpenAI API 비용**: 추천 생성 시 OpenAI API 사용으로 인한 비용 발생
3. **데이터 저장**: Supabase 저장 공간 및 요청 제한 고려
4. **스케줄러**: 백그라운드 실행 시 시스템 리소스 사용

## 🔄 업데이트 및 유지보수

### 정기 점검사항
- API 키 유효성 확인
- Supabase 연결 상태 확인
- 로그 파일 정리
- 데이터 백업

### 문제 해결
- 로그 파일 확인으로 오류 원인 파악
- API 응답 상태 확인
- 데이터베이스 연결 상태 확인

## 📞 지원

시스템 사용 중 문제가 발생하면 로그 파일을 확인하고, 필요시 개발팀에 문의하세요.

---

**개발일**: 2025년 1월
**버전**: 1.0.0
**개발자**: KPMG 데이터팀

