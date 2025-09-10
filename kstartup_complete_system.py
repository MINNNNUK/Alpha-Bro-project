#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-스타트업 정부지원사업 공고 데이터 수집 시스템 (완전 통합 버전)
API, 웹 스크래핑, 구글 스프레드시트 연동, 자동화 기능 포함
"""

import requests
import pandas as pd
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
import os
import logging
from typing import List, Dict, Optional
import schedule
import threading
from pathlib import Path
import urllib3
import subprocess

# 구글 스프레드시트 연동 (선택사항)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("구글 스프레드시트 연동을 위해 gspread와 google-auth를 설치하세요.")

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kstartup_complete_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KStartupCompleteSystem:
    """K-스타트업 완전 통합 데이터 수집 시스템"""
    
    def __init__(self, service_key: str = None, google_credentials_path: str = None):
        self.api_url = 'https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01'
        self.service_key = service_key
        self.data_dir = Path('collected_data')
        self.data_dir.mkdir(exist_ok=True)
        
        # 구글 스프레드시트 설정
        self.google_credentials_path = google_credentials_path
        self.gc = None
        self.worksheet = None
        
        # 세션 생성
        self.session = requests.Session()
        self.session.verify = False
        
        # 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # 구글 스프레드시트 초기화
        if google_credentials_path and os.path.exists(google_credentials_path) and GOOGLE_AVAILABLE:
            self.init_google_sheets()
    
    def init_google_sheets(self):
        """구글 스프레드시트 초기화"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                self.google_credentials_path, 
                scopes=scope
            )
            
            self.gc = gspread.authorize(creds)
            logger.info("구글 스프레드시트 연결 성공")
            
        except Exception as e:
            logger.error(f"구글 스프레드시트 연결 실패: {str(e)}")
            self.gc = None
    
    def create_or_get_worksheet(self, spreadsheet_name: str, worksheet_name: str = "공고데이터"):
        """스프레드시트 및 워크시트 생성 또는 가져오기"""
        if not self.gc:
            logger.warning("구글 스프레드시트가 연결되지 않았습니다.")
            return None
            
        try:
            # 스프레드시트 찾기 또는 생성
            try:
                spreadsheet = self.gc.open(spreadsheet_name)
            except gspread.SpreadsheetNotFound:
                spreadsheet = self.gc.create(spreadsheet_name)
                logger.info(f"새 스프레드시트 생성: {spreadsheet_name}")
            
            # 워크시트 찾기 또는 생성
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
                logger.info(f"새 워크시트 생성: {worksheet_name}")
            
            self.worksheet = worksheet
            return worksheet
            
        except Exception as e:
            logger.error(f"워크시트 생성/가져오기 실패: {str(e)}")
            return None
    
    def upload_to_google_sheets(self, announcements: List[Dict], spreadsheet_name: str = "K-스타트업 공고 데이터"):
        """데이터를 구글 스프레드시트에 업로드"""
        if not announcements:
            logger.warning("업로드할 데이터가 없습니다.")
            return False
            
        worksheet = self.create_or_get_worksheet(spreadsheet_name)
        if not worksheet:
            return False
            
        try:
            # 데이터프레임 생성
            df = pd.DataFrame(announcements)
            
            # 기존 데이터와 중복 제거 (공고번호 기준)
            if '공고번호' in df.columns:
                existing_data = worksheet.get_all_records()
                if existing_data:
                    existing_df = pd.DataFrame(existing_data)
                    existing_ids = set(existing_df['공고번호'].astype(str))
                    new_df = df[~df['공고번호'].astype(str).isin(existing_ids)]
                else:
                    new_df = df
            else:
                new_df = df
            
            if new_df.empty:
                logger.info("새로운 데이터가 없습니다.")
                return True
            
            # 헤더 추가 (첫 번째 행이 비어있는 경우)
            if not worksheet.get('A1'):
                headers = list(new_df.columns)
                worksheet.insert_row(headers, 1)
                logger.info("헤더 추가 완료")
            
            # 데이터 추가
            for idx, row in new_df.iterrows():
                values = [str(val) if pd.notna(val) else '' for val in row.values]
                worksheet.append_row(values)
            
            logger.info(f"구글 스프레드시트에 {len(new_df)}개 행 추가 완료")
            return True
            
        except Exception as e:
            logger.error(f"구글 스프레드시트 업로드 실패: {str(e)}")
            return False
    
    def fetch_announcements_api(self, start_date: str, end_date: str, page_no: int = 1, num_of_rows: int = 100) -> Optional[Dict]:
        """API를 사용하여 공고 데이터를 가져옵니다."""
        if not self.service_key:
            logger.warning("API 키가 설정되지 않았습니다.")
            return None
            
        params = {
            'serviceKey': self.service_key,
            'startDate': start_date,
            'endDate': end_date,
            'pageNo': page_no,
            'numOfRows': num_of_rows,
            'resultType': 'json'
        }
        
        try:
            logger.info(f"API 호출 중: {start_date} ~ {end_date}, 페이지 {page_no}")
            
            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            if response.status_code == 200:
                logger.info("API 호출 성공")
                
                data = response.json()
                
                if 'response' in data and 'body' in data['response']:
                    body = data['response']['body']
                    items = body.get('items', [])
                    
                    result_info = {
                        'totalCount': body.get('totalCount', 0),
                        'currentCount': len(items),
                        'items': items
                    }
                    
                    return result_info
                else:
                    logger.error("API 응답 구조가 예상과 다릅니다.")
                    return None
                    
        except Exception as e:
            logger.error(f"API 요청 오류: {str(e)}")
            return None
    
    def fetch_announcements_curl(self, start_date: str, end_date: str, page_no: int = 1, num_of_rows: int = 100) -> Optional[Dict]:
        """curl을 사용하여 API에서 공고 데이터를 가져옵니다."""
        if not self.service_key:
            logger.warning("API 키가 설정되지 않았습니다.")
            return None
            
        params = {
            'serviceKey': self.service_key,
            'startDate': start_date,
            'endDate': end_date,
            'pageNo': page_no,
            'numOfRows': num_of_rows,
            'resultType': 'xml'
        }
        
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.api_url}?{param_string}"
        
        try:
            logger.info(f"curl API 호출 중: {start_date} ~ {end_date}, 페이지 {page_no}")
            
            cmd = ['curl', '-k', '-s', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("curl API 호출 성공")
                
                root = ET.fromstring(result.stdout)
                
                if root.tag == 'OpenAPI_ServiceResponse':
                    error_msg = root.find('.//errMsg')
                    if error_msg is not None:
                        logger.error(f"API 오류: {error_msg.text}")
                        return None
                
                result_info = {}
                for child in root:
                    if child.tag == 'currentCount':
                        result_info['currentCount'] = int(child.text)
                    elif child.tag == 'matchCount':
                        result_info['matchCount'] = int(child.text)
                    elif child.tag == 'page':
                        result_info['page'] = int(child.text)
                    elif child.tag == 'perPage':
                        result_info['perPage'] = int(child.text)
                    elif child.tag == 'totalCount':
                        result_info['totalCount'] = int(child.text)
                    elif child.tag == 'data':
                        items = []
                        for item in child.findall('item'):
                            item_data = {}
                            for col in item.findall('col'):
                                name = col.get('name')
                                value = col.text if col.text else ''
                                item_data[name] = value
                            items.append(item_data)
                        result_info['items'] = items
                
                return result_info
            else:
                logger.error(f"curl 실행 실패: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"curl API 요청 오류: {str(e)}")
            return None
    
    def create_mock_data(self, count: int = 100) -> List[Dict]:
        """테스트용 모의 데이터를 생성합니다."""
        mock_data = []
        
        sample_announcements = [
            {
                '공고번호': 'KS-001',
                '사업공고명': 'K-스타트업 스케일업 프로그램',
                '통합사업명': 'K-스타트업 스케일업 프로그램',
                '공고기관명': '중소벤처기업부',
                '사업담당부서': '창업정책과',
                '공고내용': '성장단계 스타트업을 위한 맞춤형 지원 프로그램',
                '접수시작일': '2024-01-15',
                '접수종료일': '2024-03-15',
                '신청대상': '스타트업',
                '신청대상내용': '창업 3년 이상 7년 미만 스타트업',
                '지원지역': '전국',
                '지원사업분류': '사업화',
                '사업경력': '3년미만,5년미만,7년미만',
                '사업대상연령': '만 20세 이상 ~ 만 39세 이하',
                '감독기관': '중소벤처기업부',
                '온라인신청방법': 'https://www.k-startup.go.kr',
                '상세페이지URL': 'https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do',
                '담당연락처': '02-1234-5678',
                '모집진행여부': 'Y',
                '통합공고여부': 'N',
                '우대사항': 'AI, 빅데이터 분야 우대',
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                '공고번호': 'KS-002',
                '사업공고명': '기업마당 창업지원 프로그램',
                '통합사업명': '기업마당 창업지원 프로그램',
                '공고기관명': '중소벤처기업부',
                '사업담당부서': '창업정책과',
                '공고내용': '초기 창업자를 위한 종합 지원 프로그램',
                '접수시작일': '2024-02-01',
                '접수종료일': '2024-04-30',
                '신청대상': '예비창업자, 창업자',
                '신청대상내용': '창업 1년 미만 예비창업자 및 창업자',
                '지원지역': '서울',
                '지원사업분류': '창업',
                '사업경력': '예비창업자,1년미만',
                '사업대상연령': '만 20세 이상 ~ 만 39세 이하',
                '감독기관': '중소벤처기업부',
                '온라인신청방법': 'https://www.bizinfo.go.kr',
                '상세페이지URL': 'https://www.bizinfo.go.kr/web/contents/bizpbanc-ongoing.do',
                '담당연락처': '02-2345-6789',
                '모집진행여부': 'Y',
                '통합공고여부': 'N',
                '우대사항': '여성창업자 우대',
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                '공고번호': 'KS-003',
                '사업공고명': '글로벌 진출 지원 프로그램',
                '통합사업명': '글로벌 진출 지원 프로그램',
                '공고기관명': '산업통상자원부',
                '사업담당부서': '무역투자정책과',
                '공고내용': '해외 진출을 위한 맞춤형 지원 프로그램',
                '접수시작일': '2024-03-01',
                '접수종료일': '2024-05-31',
                '신청대상': '중소기업',
                '신청대상내용': '해외 진출 의지가 있는 중소기업',
                '지원지역': '전국',
                '지원사업분류': '글로벌',
                '사업경력': '1년미만,2년미만,3년미만,5년미만',
                '사업대상연령': '만 20세 이상',
                '감독기관': '산업통상자원부',
                '온라인신청방법': 'https://www.motie.go.kr',
                '상세페이지URL': 'https://www.motie.go.kr/web/contents/bizpbanc-ongoing.do',
                '담당연락처': '02-3456-7890',
                '모집진행여부': 'Y',
                '통합공고여부': 'N',
                '우대사항': '수출 경험이 있는 기업 우대',
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        for i in range(count):
            base_data = sample_announcements[i % len(sample_announcements)].copy()
            base_data['공고번호'] = f"KS-{i+1:03d}"
            base_data['사업공고명'] = f"{base_data['사업공고명']} ({i+1}차)"
            base_data['수집일시'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            mock_data.append(base_data)
        
        return mock_data
    
    def collect_all_announcements(self, start_date: str, end_date: str, use_mock: bool = False) -> List[Dict]:
        """지정된 기간의 모든 공고 데이터를 수집합니다."""
        if use_mock:
            logger.info("모의 데이터를 사용합니다.")
            return self.create_mock_data(50)
        
        all_announcements = []
        page_no = 1
        num_of_rows = 100
        
        while True:
            data = self.fetch_announcements_api(start_date, end_date, page_no, num_of_rows)
            
            if not data:
                data = self.fetch_announcements_curl(start_date, end_date, page_no, num_of_rows)
            
            if not data:
                logger.warning(f"페이지 {page_no} 데이터 수집 실패")
                break
                
            total_count = data.get('totalCount', 0)
            
            if page_no == 1:
                logger.info(f"총 {total_count}개의 공고가 있습니다.")
            
            items = data.get('items', [])
            if not items:
                logger.info(f"페이지 {page_no}에 더 이상 데이터가 없습니다.")
                break
                
            all_announcements.extend(items)
            logger.info(f"페이지 {page_no}에서 {len(items)}개 공고 수집 완료 (누적: {len(all_announcements)}개)")
            
            if len(items) < num_of_rows or len(all_announcements) >= total_count:
                logger.info("마지막 페이지에 도달했습니다.")
                break
                
            page_no += 1
            time.sleep(1)
                
        logger.info(f"총 {len(all_announcements)}개의 공고를 수집했습니다.")
        return all_announcements
    
    def save_to_excel(self, announcements: List[Dict], filename: str = None) -> str:
        """수집된 데이터를 엑셀 파일로 저장합니다."""
        if not announcements:
            logger.warning("저장할 데이터가 없습니다.")
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kstartup_announcements_{timestamp}.xlsx"
            
        filepath = self.data_dir / filename
        
        try:
            df = pd.DataFrame(announcements)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='공고데이터', index=False)
                
                worksheet = writer.sheets['공고데이터']
                
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"데이터가 {filepath}에 저장되었습니다.")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"엑셀 저장 오류: {str(e)}")
            return None
    
    def save_to_csv(self, announcements: List[Dict], filename: str = None) -> str:
        """수집된 데이터를 CSV 파일로 저장합니다."""
        if not announcements:
            logger.warning("저장할 데이터가 없습니다.")
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kstartup_announcements_{timestamp}.csv"
            
        filepath = self.data_dir / filename
        
        try:
            df = pd.DataFrame(announcements)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"데이터가 {filepath}에 저장되었습니다.")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"CSV 저장 오류: {str(e)}")
            return None
    
    def collect_and_sync(self, start_date: str, end_date: str, use_mock: bool = False, spreadsheet_name: str = "K-스타트업 공고 데이터"):
        """데이터 수집 및 구글 스프레드시트 동기화"""
        logger.info(f"데이터 수집 및 동기화 시작: {start_date} ~ {end_date}")
        
        if use_mock:
            announcements = self.create_mock_data(50)
        else:
            announcements = self.collect_all_announcements(start_date, end_date, use_mock)
        
        if not announcements:
            logger.warning("수집된 데이터가 없습니다.")
            return False
        
        # 로컬 엑셀 저장
        excel_file = self.save_to_excel(announcements)
        
        # 로컬 CSV 저장
        csv_file = self.save_to_csv(announcements)
        
        # 구글 스프레드시트 업로드
        google_success = False
        if self.gc:
            google_success = self.upload_to_google_sheets(announcements, spreadsheet_name)
        else:
            logger.info("구글 스프레드시트 연동이 설정되지 않았습니다.")
        
        return True
    
    def collect_past_year_data(self, use_mock: bool = False) -> str:
        """지난 1년간의 데이터를 수집합니다."""
        if use_mock:
            logger.info("모의 데이터로 지난 1년간의 데이터를 생성합니다.")
            announcements = self.create_mock_data(200)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"지난 1년간의 데이터 수집 시작: {start_date_str} ~ {end_date_str}")
            
            announcements = self.collect_all_announcements(start_date_str, end_date_str, use_mock)
        
        if announcements:
            excel_file = self.save_to_excel(announcements, f"kstartup_past_year_{datetime.now().strftime('%Y%m%d')}.xlsx")
            csv_file = self.save_to_csv(announcements, f"kstartup_past_year_{datetime.now().strftime('%Y%m%d')}.csv")
            
            # 구글 스프레드시트 업로드
            if self.gc:
                self.upload_to_google_sheets(announcements, "K-스타트업 공고 데이터 (1년)")
            
            return excel_file
        else:
            logger.error("데이터 수집에 실패했습니다.")
            return None
    
    def collect_new_announcements(self, use_mock: bool = False) -> str:
        """최근 7일간의 새로운 공고를 수집합니다."""
        if use_mock:
            logger.info("모의 데이터로 최근 7일간의 새로운 공고를 생성합니다.")
            announcements = self.create_mock_data(20)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"최근 7일간의 새로운 공고 수집: {start_date_str} ~ {end_date_str}")
            
            announcements = self.collect_all_announcements(start_date_str, end_date_str, use_mock)
        
        if announcements:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = self.save_to_excel(announcements, f"kstartup_new_announcements_{timestamp}.xlsx")
            csv_file = self.save_to_csv(announcements, f"kstartup_new_announcements_{timestamp}.csv")
            
            # 구글 스프레드시트 업로드
            if self.gc:
                self.upload_to_google_sheets(announcements, "K-스타트업 공고 데이터 (신규)")
            
            return excel_file
        else:
            logger.info("새로운 공고가 없습니다.")
            return None

def main():
    """메인 실행 함수"""
    # 설정
    SERVICE_KEY = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
    GOOGLE_CREDENTIALS_PATH = 'google_credentials.json'  # 구글 서비스 계정 키 파일
    
    # 시스템 초기화
    system = KStartupCompleteSystem(
        service_key=SERVICE_KEY,
        google_credentials_path=GOOGLE_CREDENTIALS_PATH if os.path.exists(GOOGLE_CREDENTIALS_PATH) else None
    )
    
    print("=== K-스타트업 정부지원사업 공고 데이터 수집 시스템 (완전 통합 버전) ===")
    print("1. 지난 1년간의 모든 데이터 수집 (실제 API)")
    print("2. 최근 7일간의 새로운 공고 수집 (실제 API)")
    print("3. 지난 1년간의 모든 데이터 수집 (모의 데이터)")
    print("4. 최근 7일간의 새로운 공고 수집 (모의 데이터)")
    print("5. 자동 수집 모드 시작 (매일 오전 9시, 모의 데이터)")
    print("6. 구글 스프레드시트 연동 테스트")
    print("7. 종료")
    
    while True:
        choice = input("\n선택하세요 (1-7): ").strip()
        
        if choice == '1':
            print("\n지난 1년간의 데이터를 수집합니다...")
            file_path = system.collect_past_year_data(use_mock=False)
            if file_path:
                print(f"✅ 데이터 수집 완료: {file_path}")
            else:
                print("❌ 데이터 수집 실패")
                
        elif choice == '2':
            print("\n최근 7일간의 새로운 공고를 수집합니다...")
            file_path = system.collect_new_announcements(use_mock=False)
            if file_path:
                print(f"✅ 새로운 공고 수집 완료: {file_path}")
            else:
                print("ℹ️ 새로운 공고가 없거나 수집 실패")
                
        elif choice == '3':
            print("\n지난 1년간의 데이터를 모의 데이터로 생성합니다...")
            file_path = system.collect_past_year_data(use_mock=True)
            if file_path:
                print(f"✅ 모의 데이터 생성 완료: {file_path}")
            else:
                print("❌ 모의 데이터 생성 실패")
                
        elif choice == '4':
            print("\n최근 7일간의 새로운 공고를 모의 데이터로 생성합니다...")
            file_path = system.collect_new_announcements(use_mock=True)
            if file_path:
                print(f"✅ 모의 데이터 생성 완료: {file_path}")
            else:
                print("❌ 모의 데이터 생성 실패")
                
        elif choice == '5':
            print("\n자동 수집 모드를 시작합니다...")
            print("매일 오전 9시에 새로운 공고를 자동으로 수집합니다. (모의 데이터)")
            print("종료하려면 Ctrl+C를 누르세요.")
            
            schedule.every().day.at("09:00").do(lambda: system.collect_new_announcements(use_mock=True))
            
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\n자동 수집 모드를 종료합니다.")
                
        elif choice == '6':
            print("\n구글 스프레드시트 연동을 테스트합니다...")
            if system.gc:
                print("✅ 구글 스프레드시트 연결됨")
                test_data = system.create_mock_data(5)
                success = system.upload_to_google_sheets(test_data, "K-스타트업 테스트")
                if success:
                    print("✅ 구글 스프레드시트 업로드 성공")
                else:
                    print("❌ 구글 스프레드시트 업로드 실패")
            else:
                print("❌ 구글 스프레드시트 연결되지 않음")
                print("google_credentials.json 파일을 확인하세요.")
                
        elif choice == '7':
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다. 1-7 중에서 선택하세요.")

if __name__ == "__main__":
    main()
