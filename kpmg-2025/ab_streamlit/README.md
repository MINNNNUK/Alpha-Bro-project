# Alpha Advisors – Streamlit MVP (Auto-Load)

## Auto-Load 우선순위
1) `./data/` 폴더의 CSV/XLSX 자동 탐색 (파일명에 `companies`, `Companies`, `ann`, `bizinfo`, `KS_` 등 포함)
2) (로컬 개발) `ABS_CANDIDATES` 경로의 엑셀 파일
3) (선택) `st.secrets["gsheets"]` 설정 시 Google Sheets에서 로드
4) 업로드 위젯은 선택 사항 (없어도 동작)

## 배포 팁
- 공유 URL에서 즉시 동작하려면 `data/` 폴더에 운영용 CSV/XLSX를 커밋해 두세요.
- Google Sheets 사용 시, Streamlit Cloud → Secrets에 서비스계정 JSON을 넣고
  ```toml
  [gsheets]
  type = "service_account"
  project_id = "..."
  private_key_id = "..."
  private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
  client_email = "xxx@xxx.iam.gserviceaccount.com"
  client_id = "..."
  token_uri = "https://oauth2.googleapis.com/token"
  companies_url = "https://docs.google.com/spreadsheets/d/..."
  announcements_url = "https://docs.google.com/spreadsheets/d/..."
  ```
