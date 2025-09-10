#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-스타트업 API를 활용한 정부지원사업 공고 데이터 수집기 (고급 버전)
구글 스프레드시트 연동 및 자동화 기능 포함
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import os
import logging
from typing import List, Dict, Optional
import schedule
import threading
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kstartup_advanced_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KStartupAdvancedCollector:
    """K-스타트업 API 고급 데이터 수집기"""
    
    def __init__(self, service_key: str, google_credentials_path: str = None, email_config: Dict = None):
        self.api_url = 'https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01'
        self.service_key = service_key
        self.data_dir = Path('collected_data')
        self.data_dir.mkdir(exist_ok=True)
        
        # 구글 스프레드시트 설정
        self.google_credentials_path = google_credentials_path
        self.gc = None
        self.worksheet = None
        
        # 이메일 설정
        self.email_config = email_config
        
        # 구글 스프레드시트 초기화
        if google_credentials_path and os.path.exists(google_credentials_path):
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
            
            # 기존 데이터와 중복 제거 (공고 ID 기준)
            if 'announcementId' in df.columns:
                existing_data = worksheet.get_all_records()
                if existing_data:
                    existing_df = pd.DataFrame(existing_data)
                    existing_ids = set(existing_df['announcementId'].astype(str))
                    new_df = df[~df['announcementId'].astype(str).isin(existing_ids)]
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
    
    def send_email_notification(self, subject: str, body: str, attachment_path: str = None):
        """이메일 알림 발송"""
        if not self.email_config:
            logger.warning("이메일 설정이 없습니다.")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = self.email_config['to_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # 첨부파일 추가
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
            
            # 이메일 발송
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['from_email'], self.email_config['password'])
            text = msg.as_string()
            server.sendmail(self.email_config['from_email'], self.email_config['to_email'], text)
            server.quit()
            
            logger.info("이메일 알림 발송 완료")
            return True
            
        except Exception as e:
            logger.error(f"이메일 발송 실패: {str(e)}")
            return False
    
    def fetch_announcements(self, start_date: str, end_date: str, page_no: int = 1, num_of_rows: int = 100) -> Optional[Dict]:
        """API에서 공고 데이터를 가져옵니다."""
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
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'response' in data and 'header' in data['response']:
                result_code = data['response']['header'].get('resultCode', '')
                if result_code != '00':
                    logger.error(f"API 오류: {data['response']['header'].get('resultMsg', '알 수 없는 오류')}")
                    return None
                    
            return data
            
        except Exception as e:
            logger.error(f"API 요청 오류: {str(e)}")
            return None
    
    def collect_all_announcements(self, start_date: str, end_date: str) -> List[Dict]:
        """지정된 기간의 모든 공고 데이터를 수집합니다."""
        all_announcements = []
        page_no = 1
        num_of_rows = 100
        
        while True:
            data = self.fetch_announcements(start_date, end_date, page_no, num_of_rows)
            
            if not data:
                break
                
            if 'response' in data and 'body' in data['response']:
                body = data['response']['body']
                total_count = body.get('totalCount', 0)
                logger.info(f"총 {total_count}개의 공고가 있습니다.")
                
                items = body.get('items', [])
                if not items:
                    break
                    
                all_announcements.extend(items)
                logger.info(f"페이지 {page_no}에서 {len(items)}개 공고 수집 완료")
                
                if len(items) < num_of_rows:
                    break
                    
                page_no += 1
                time.sleep(1)
            else:
                break
                
        logger.info(f"총 {len(all_announcements)}개의 공고를 수집했습니다.")
        return all_announcements
    
    def save_to_excel(self, announcements: List[Dict], filename: str = None) -> str:
        """수집된 데이터를 엑셀 파일로 저장합니다."""
        if not announcements:
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kstartup_announcements_{timestamp}.xlsx"
            
        filepath = self.data_dir / filename
        
        try:
            df = pd.DataFrame(announcements)
            df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"데이터가 {filepath}에 저장되었습니다.")
            return str(filepath)
        except Exception as e:
            logger.error(f"엑셀 저장 오류: {str(e)}")
            return None
    
    def collect_and_sync(self, start_date: str, end_date: str, spreadsheet_name: str = "K-스타트업 공고 데이터"):
        """데이터 수집 및 구글 스프레드시트 동기화"""
        logger.info(f"데이터 수집 및 동기화 시작: {start_date} ~ {end_date}")
        
        # 데이터 수집
        announcements = self.collect_all_announcements(start_date, end_date)
        
        if not announcements:
            logger.warning("수집된 데이터가 없습니다.")
            return False
        
        # 로컬 엑셀 저장
        excel_file = self.save_to_excel(announcements)
        
        # 구글 스프레드시트 업로드
        google_success = self.upload_to_google_sheets(announcements, spreadsheet_name)
        
        # 이메일 알림
        if self.email_config:
            subject = f"K-스타트업 공고 데이터 수집 완료 ({len(announcements)}개)"
            body = f"""
            <h3>K-스타트업 공고 데이터 수집 완료</h3>
            <p><strong>수집 기간:</strong> {start_date} ~ {end_date}</p>
            <p><strong>수집된 공고 수:</strong> {len(announcements)}개</p>
            <p><strong>구글 스프레드시트 동기화:</strong> {'성공' if google_success else '실패'}</p>
            <p><strong>수집 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """
            
            self.send_email_notification(subject, body, excel_file)
        
        return True
    
    def auto_collect_new_announcements(self):
        """자동으로 새로운 공고를 수집합니다."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)  # 어제부터 오늘까지
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"자동 수집 시작: {start_date_str} ~ {end_date_str}")
        
        success = self.collect_and_sync(start_date_str, end_date_str)
        
        if success:
            logger.info("자동 수집 완료")
        else:
            logger.error("자동 수집 실패")

def main():
    """메인 실행 함수"""
    # 설정
    SERVICE_KEY = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
    
    # 구글 스프레드시트 인증 파일 경로 (선택사항)
    GOOGLE_CREDENTIALS_PATH = 'google_credentials.json'  # 구글 서비스 계정 키 파일
    
    # 이메일 설정 (선택사항)
    EMAIL_CONFIG = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'from_email': 'your_email@gmail.com',
        'password': 'your_app_password',
        'to_email': 'recipient@gmail.com'
    }
    
    # 수집기 초기화
    collector = KStartupAdvancedCollector(
        service_key=SERVICE_KEY,
        google_credentials_path=GOOGLE_CREDENTIALS_PATH if os.path.exists(GOOGLE_CREDENTIALS_PATH) else None,
        email_config=EMAIL_CONFIG
    )
    
    print("=== K-스타트업 정부지원사업 공고 데이터 수집기 (고급 버전) ===")
    print("1. 지난 1년간의 모든 데이터 수집 및 동기화")
    print("2. 최근 7일간의 새로운 공고 수집 및 동기화")
    print("3. 자동 수집 모드 시작 (매일 오전 9시)")
    print("4. 종료")
    
    while True:
        choice = input("\n선택하세요 (1-4): ").strip()
        
        if choice == '1':
            print("\n지난 1년간의 데이터를 수집하고 동기화합니다...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            success = collector.collect_and_sync(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if success:
                print("✅ 데이터 수집 및 동기화 완료")
            else:
                print("❌ 데이터 수집 또는 동기화 실패")
                
        elif choice == '2':
            print("\n최근 7일간의 새로운 공고를 수집하고 동기화합니다...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            success = collector.collect_and_sync(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if success:
                print("✅ 새로운 공고 수집 및 동기화 완료")
            else:
                print("ℹ️ 새로운 공고가 없거나 수집 실패")
                
        elif choice == '3':
            print("\n자동 수집 모드를 시작합니다...")
            print("매일 오전 9시에 새로운 공고를 자동으로 수집합니다.")
            print("종료하려면 Ctrl+C를 누르세요.")
            
            # 스케줄 설정
            schedule.every().day.at("09:00").do(collector.auto_collect_new_announcements)
            
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\n자동 수집 모드를 종료합니다.")
                
        elif choice == '4':
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다. 1-4 중에서 선택하세요.")

if __name__ == "__main__":
    main()
