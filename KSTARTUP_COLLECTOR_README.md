# K-스타트업 정부지원사업 공고 데이터 수집기

K-스타트업 API를 활용하여 정부지원사업 공고 데이터를 자동으로 수집하고 구글 스프레드시트에 동기화하는 시스템입니다.

## 🚀 주요 기능

### 1. 데이터 수집
- **과거 1년간의 모든 공고 데이터 수집**
- **최근 7일간의 새로운 공고 자동 수집**
- **실시간 API 호출을 통한 최신 데이터 확보**

### 2. 데이터 저장
- **엑셀 파일 (.xlsx) 저장**
- **CSV 파일 (.csv) 저장**
- **구글 스프레드시트 자동 동기화**

### 3. 자동화 기능
- **매일 오전 9시 자동 수집**
- **이메일 알림 발송**
- **중복 데이터 자동 제거**

## 📋 설치 및 설정

### 1. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
```python
SERVICE_KEY = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
```

### 3. 구글 스프레드시트 연동 (선택사항)
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Google Sheets API 및 Google Drive API 활성화
3. 서비스 계정 생성 및 JSON 키 파일 다운로드
4. `google_credentials.json` 파일을 프로젝트 루트에 저장

### 4. 이메일 알림 설정 (선택사항)
```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'from_email': 'your_email@gmail.com',
    'password': 'your_app_password',
    'to_email': 'recipient@gmail.com'
}
```

## 🎯 사용법

### 1. 기본 수집기 사용
```bash
python kstartup_data_collector.py
```

**메뉴 옵션:**
- `1`: 지난 1년간의 모든 데이터 수집
- `2`: 최근 7일간의 새로운 공고 수집
- `3`: 자동 수집 모드 시작 (매일 오전 9시)
- `4`: 종료

### 2. 고급 수집기 사용 (구글 스프레드시트 연동)
```bash
python kstartup_advanced_collector.py
```

**추가 기능:**
- 구글 스프레드시트 자동 동기화
- 이메일 알림 발송
- 중복 데이터 자동 제거

### 3. API 테스트
```bash
python test_kstartup_api.py
```

## 📊 수집되는 데이터

### API 응답 데이터 구조
```json
{
  "response": {
    "header": {
      "resultCode": "00",
      "resultMsg": "NORMAL_SERVICE"
    },
    "body": {
      "totalCount": 100,
      "items": [
        {
          "announcementId": "공고ID",
          "title": "공고명",
          "agency": "기관명",
          "startDate": "신청시작일",
          "endDate": "신청종료일",
          "amount": "지원금액",
          "stage": "단계",
          "region": "지역",
          "url": "공고링크"
        }
      ]
    }
  }
}
```

## 📁 파일 구조

```
kpmg-2025/
├── kstartup_data_collector.py          # 기본 수집기
├── kstartup_advanced_collector.py      # 고급 수집기 (구글 연동)
├── test_kstartup_api.py               # API 테스트 스크립트
├── requirements.txt                   # 필요한 패키지 목록
├── collected_data/                    # 수집된 데이터 저장 폴더
│   ├── kstartup_announcements_*.xlsx
│   └── kstartup_announcements_*.csv
├── google_credentials.json            # 구글 인증 파일 (선택사항)
└── *.log                             # 로그 파일
```

## 🔧 설정 옵션

### 1. 수집 기간 설정
```python
# 1년간 데이터 수집
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# 7일간 데이터 수집
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
```

### 2. 페이지 크기 설정
```python
num_of_rows = 100  # 페이지당 가져올 데이터 수
```

### 3. API 호출 간격 설정
```python
time.sleep(1)  # API 호출 간 1초 대기
```

## 📈 자동화 설정

### 1. 스케줄링
```python
# 매일 오전 9시 실행
schedule.every().day.at("09:00").do(collector.auto_collect_new_announcements)

# 매주 월요일 오전 9시 실행
schedule.every().monday.at("09:00").do(collector.collect_weekly_data)
```

### 2. 시스템 서비스로 등록 (Linux)
```bash
# systemd 서비스 파일 생성
sudo nano /etc/systemd/system/kstartup-collector.service

# 서비스 내용
[Unit]
Description=K-Startup Data Collector
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 /path/to/project/kstartup_advanced_collector.py
Restart=always

[Install]
WantedBy=multi-user.target

# 서비스 활성화
sudo systemctl enable kstartup-collector
sudo systemctl start kstartup-collector
```

## 🚨 주의사항

### 1. API 사용량 제한
- API 호출 횟수에 제한이 있을 수 있습니다
- 적절한 호출 간격을 유지하세요 (1초 이상)

### 2. 데이터 크기
- 대량의 데이터 수집 시 메모리 사용량을 고려하세요
- 필요시 배치 처리로 나누어 수집하세요

### 3. 에러 처리
- 네트워크 오류, API 오류 등에 대한 적절한 처리가 필요합니다
- 로그 파일을 정기적으로 확인하세요

## 📞 지원

문제가 발생하거나 추가 기능이 필요한 경우:
1. 로그 파일 확인
2. API 테스트 스크립트 실행
3. 네트워크 연결 상태 확인

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
