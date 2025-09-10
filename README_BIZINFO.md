# 기업마당 2025년 정부지원사업 공고 데이터 수집 시스템

## 🎯 시스템 개요

**2025년 9월 6일 기준**으로 기업마당 API를 활용하여 정부지원사업 공고 데이터를 자동으로 수집하고, 엑셀 파일과 CSV 파일로 저장하는 시스템입니다.

## 📅 수집 기준일 및 범위

- **수집 기준일**: 2025년 9월 6일
- **1년간 데이터**: 2024년 9월 6일 ~ 2025년 9월 6일
- **30일간 데이터**: 2025년 8월 7일 ~ 2025년 9월 6일
- **매일 신규 데이터**: 2025년 9월 5일 ~ 2025년 9월 6일

## 🚀 빠른 시작

### 1. 패키지 설치
```bash
pip3 install -r requirements.txt
```

### 2. 메인 시스템 실행
```bash
python3 bizinfo_2025_collector.py
```

### 3. 매일 자동 수집 실행
```bash
python3 daily_auto_collector_biz.py
```

## 📁 파일 설명

### 🎯 메인 시스템
- **`bizinfo_2025_collector.py`** - 2025년 기업마당 데이터 수집 메인 시스템

### 🔧 자동화 시스템
- **`daily_auto_collector_biz.py`** - 매일 자동 수집 스크립트

### 📊 수집된 데이터
- **`collected_data_biz/bizinfo_2025_past_year_*.xlsx`** - 1년간 데이터 (엑셀)
- **`collected_data_biz/bizinfo_2025_past_year_*.csv`** - 1년간 데이터 (CSV)
- **`collected_data_biz/bizinfo_2025_recent_30days_*.xlsx`** - 30일간 데이터 (엑셀)
- **`collected_data_biz/bizinfo_2025_recent_30days_*.csv`** - 30일간 데이터 (CSV)
- **`collected_data_biz/bizinfo_2025_daily_new_*.xlsx`** - 매일 신규 데이터 (엑셀)
- **`collected_data_biz/bizinfo_2025_daily_new_*.csv`** - 매일 신규 데이터 (CSV)

## 🎮 사용법

### 메인 시스템 실행
```bash
python3 bizinfo_2025_collector.py
```

### 메뉴 옵션
1. **지난 1년간의 모든 데이터 수집** (2024.09.06 ~ 2025.09.06)
2. **최근 30일간의 데이터 수집** (2025.08.07 ~ 2025.09.06)
3. **매일 새로운 공고 수집** (2025.09.05 ~ 2025.09.06)
4. **자동 수집 모드 시작** (매일 오전 9시)
5. **종료**

### 매일 자동 수집 실행
```bash
python3 daily_auto_collector_biz.py
```

**자동 실행 스케줄:**
- 🕘 **매일 오전 9시**: 새로운 공고 수집
- 🕘 **매주 월요일 오전 9시**: 30일간 데이터 수집
- 🕘 **매월 1일**: 1년간 데이터 수집 (수동 실행)

## 📊 수집되는 데이터

### 데이터 필드
- **공고명**: 공고명
- **공고번호**: 공고번호 (BIZ-2025-XXX 형식)
- **소관기관명**: 소관기관명
- **수행기관명**: 수행기관명
- **사업개요내용**: 사업개요내용
- **지원분야대분류**: 지원분야대분류 (금융, 기술, 인력, 수출, 내수, 창업, 경영, 기타)
- **등록일자**: 등록일자
- **신청기간**: 신청기간
- **지원대상**: 지원대상
- **조회수**: 조회수
- **해시태그**: 해시태그
- **사업개요내용상세**: 사업개요내용상세
- **사업신청방법**: 사업신청방법
- **문의처**: 문의처
- **사업신청URL**: 사업신청URL
- **지원분야대분류코드**: 지원분야대분류코드
- **등록일시**: 등록일시
- **신청기간상세**: 신청기간상세
- **공고URL**: 공고URL
- **공고명상세**: 공고명상세
- **지원금액**: 지원 가능한 최대 금액 (예: 최대 3억원)
- **지원금액상세**: 지원금액의 상세 내용 (예: 디지털 전환 지원금 최대 3억원, 기술 컨설팅, 시스템 구축 지원)
- **수집일시**: 데이터 수집 시점

## 🔧 설정

### API 키 설정
`bizinfo_2025_collector.py` 파일에서 API 키를 수정하세요:
```python
SERVICE_KEY = 'LrTS4V'
```

### 날짜 범위 수정
현재 2025년 9월 6일 기준으로 설정되어 있습니다. 다른 날짜로 변경하려면:
```python
# 2025년 9월 6일 기준
end_date = datetime(2025, 9, 6)
start_date = end_date - timedelta(days=365)  # 1년 전
```

## 🚨 문제 해결

### 패키지 설치 오류
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

### 권한 오류
```bash
chmod +x *.py
```

### 로그 확인
```bash
tail -f bizinfo_2025_collector.log
tail -f daily_auto_collector_biz.log
```

## 🔄 자동화 설정

### 1. 시스템 서비스로 등록 (Linux)
```bash
# systemd 서비스 파일 생성
sudo nano /etc/systemd/system/bizinfo-2025-collector.service

# 서비스 내용
[Unit]
Description=BizInfo 2025 Data Collector
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/data2
ExecStart=/usr/bin/python3 /path/to/data2/daily_auto_collector_biz.py
Restart=always

[Install]
WantedBy=multi-user.target

# 서비스 활성화
sudo systemctl enable bizinfo-2025-collector
sudo systemctl start bizinfo-2025-collector
```

### 2. cron 작업 설정 (Linux/Mac)
```bash
# crontab 편집
crontab -e

# 매일 오전 9시 실행
0 9 * * * cd /path/to/data2 && python3 daily_auto_collector_biz.py

# 매월 1일 오전 9시에 1년간 데이터 수집
0 9 1 * * cd /path/to/data2 && python3 bizinfo_2025_collector.py
```

### 3. Windows 작업 스케줄러
1. 작업 스케줄러 열기
2. 기본 작업 만들기
3. 트리거: 매일 오전 9시
4. 동작: Python 스크립트 실행

## 📈 성능 최적화

### 1. API 호출 간격 조절
```python
time.sleep(1)  # 1초 대기
```

### 2. 배치 처리
```python
# 대량 데이터 수집 시 페이지 단위로 처리
for page in range(1, max_pages + 1):
    data = fetch_page(page)
    process_data(data)
    time.sleep(1)
```

## 🎯 사용 시나리오

### 시나리오 1: 일일 자동 수집
```bash
# 매일 자동 수집 시작
python3 daily_auto_collector_biz.py
```

### 시나리오 2: 1년간 데이터 일괄 수집
```bash
# 1년간 데이터 수집
python3 bizinfo_2025_collector.py
# 메뉴에서 1번 선택
```

### 시나리오 3: 30일간 데이터 수집
```bash
# 30일간 데이터 수집
python3 bizinfo_2025_collector.py
# 메뉴에서 2번 선택
```

## 🎉 완성된 기능

✅ **2025년 기준 데이터 수집** - 2025년 9월 6일 기준  
✅ **1년간 데이터 수집** - 2024년 9월 6일 ~ 2025년 9월 6일  
✅ **30일간 데이터 수집** - 2025년 8월 7일 ~ 2025년 9월 6일  
✅ **매일 신규 공고 수집** - 2025년 9월 5일 ~ 2025년 9월 6일  
✅ **자동 수집 시스템** - 매일 오전 9시 자동 실행  
✅ **다양한 저장 형식** - 엑셀, CSV 지원  
✅ **로깅 시스템** - 상세한 실행 로그  
✅ **에러 처리** - 안정적인 오류 복구  
✅ **지원금액 정보** - 지원 가능한 최대 금액 및 상세 내용 포함  

이제 2025년 기준으로 기업마당 정부지원사업 공고 데이터를 효율적으로 수집하고 관리할 수 있습니다! 🚀

## 📞 지원

### 로그 파일 위치
- `bizinfo_2025_collector.log` - 메인 시스템 로그
- `daily_auto_collector_biz.log` - 자동 수집 로그

### 문제 발생 시 확인사항
1. 로그 파일에서 오류 메시지 확인
2. 네트워크 연결 상태 확인
3. API 키 유효성 확인
4. 날짜 범위 설정 확인

## 🔗 관련 링크

- [기업마당 지원사업정보 API](https://www.bizinfo.go.kr/web/lay1/program/S1T175C174/apiDetail.do?id=bizinfoApi)
- [기업마당 홈페이지](https://www.bizinfo.go.kr)
