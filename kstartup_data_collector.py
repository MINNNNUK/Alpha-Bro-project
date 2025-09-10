#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-스타트업 API를 활용한 정부지원사업 공고 데이터 수집기
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

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kstartup_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KStartupDataCollector:
    """K-스타트업 API 데이터 수집기"""
    
    def __init__(self, service_key: str):
        self.api_url = 'https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01'
        self.service_key = service_key
        self.data_dir = Path('collected_data')
        self.data_dir.mkdir(exist_ok=True)
        
    def fetch_announcements(self, start_date: str, end_date: str, page_no: int = 1, num_of_rows: int = 100) -> Optional[Dict]:
        """
        API에서 공고 데이터를 가져옵니다.
        
        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            page_no: 페이지 번호
            num_of_rows: 페이지당 행 수
            
        Returns:
            API 응답 데이터 또는 None
        """
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
            
            # API 응답 상태 확인
            if 'response' in data and 'header' in data['response']:
                result_code = data['response']['header'].get('resultCode', '')
                if result_code != '00':
                    logger.error(f"API 오류: {data['response']['header'].get('resultMsg', '알 수 없는 오류')}")
                    return None
                    
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 오류: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"예상치 못한 오류: {str(e)}")
            return None
    
    def collect_all_announcements(self, start_date: str, end_date: str) -> List[Dict]:
        """
        지정된 기간의 모든 공고 데이터를 수집합니다.
        
        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            
        Returns:
            수집된 공고 데이터 리스트
        """
        all_announcements = []
        page_no = 1
        num_of_rows = 100
        
        while True:
            data = self.fetch_announcements(start_date, end_date, page_no, num_of_rows)
            
            if not data:
                logger.warning(f"페이지 {page_no} 데이터 수집 실패")
                break
                
            # 데이터 추출
            if 'response' in data and 'body' in data['response']:
                body = data['response']['body']
                
                # 총 개수 확인
                total_count = body.get('totalCount', 0)
                logger.info(f"총 {total_count}개의 공고가 있습니다.")
                
                # 아이템 추출
                items = body.get('items', [])
                if not items:
                    logger.info(f"페이지 {page_no}에 더 이상 데이터가 없습니다.")
                    break
                    
                all_announcements.extend(items)
                logger.info(f"페이지 {page_no}에서 {len(items)}개 공고 수집 완료")
                
                # 다음 페이지 확인
                if len(items) < num_of_rows:
                    logger.info("마지막 페이지에 도달했습니다.")
                    break
                    
                page_no += 1
                time.sleep(1)  # API 호출 간격 조절
            else:
                logger.warning(f"페이지 {page_no} 응답 구조가 예상과 다릅니다.")
                break
                
        logger.info(f"총 {len(all_announcements)}개의 공고를 수집했습니다.")
        return all_announcements
    
    def save_to_excel(self, announcements: List[Dict], filename: str = None) -> str:
        """
        수집된 데이터를 엑셀 파일로 저장합니다.
        
        Args:
            announcements: 공고 데이터 리스트
            filename: 저장할 파일명 (없으면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if not announcements:
            logger.warning("저장할 데이터가 없습니다.")
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
    
    def save_to_csv(self, announcements: List[Dict], filename: str = None) -> str:
        """
        수집된 데이터를 CSV 파일로 저장합니다.
        
        Args:
            announcements: 공고 데이터 리스트
            filename: 저장할 파일명 (없으면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
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
    
    def collect_past_year_data(self) -> str:
        """
        지난 1년간의 데이터를 수집합니다.
        
        Returns:
            저장된 파일 경로
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"지난 1년간의 데이터 수집 시작: {start_date_str} ~ {end_date_str}")
        
        announcements = self.collect_all_announcements(start_date_str, end_date_str)
        
        if announcements:
            # 엑셀과 CSV 모두 저장
            excel_file = self.save_to_excel(announcements, f"kstartup_past_year_{start_date_str}_to_{end_date_str}.xlsx")
            csv_file = self.save_to_csv(announcements, f"kstartup_past_year_{start_date_str}_to_{end_date_str}.csv")
            return excel_file
        else:
            logger.error("데이터 수집에 실패했습니다.")
            return None
    
    def collect_new_announcements(self) -> str:
        """
        최근 7일간의 새로운 공고를 수집합니다.
        
        Returns:
            저장된 파일 경로
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"최근 7일간의 새로운 공고 수집: {start_date_str} ~ {end_date_str}")
        
        announcements = self.collect_all_announcements(start_date_str, end_date_str)
        
        if announcements:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = self.save_to_excel(announcements, f"kstartup_new_announcements_{timestamp}.xlsx")
            csv_file = self.save_to_csv(announcements, f"kstartup_new_announcements_{timestamp}.csv")
            return excel_file
        else:
            logger.info("새로운 공고가 없습니다.")
            return None

def main():
    """메인 실행 함수"""
    # API 키 설정
    SERVICE_KEY = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
    
    # 수집기 초기화
    collector = KStartupDataCollector(SERVICE_KEY)
    
    print("=== K-스타트업 정부지원사업 공고 데이터 수집기 ===")
    print("1. 지난 1년간의 모든 데이터 수집")
    print("2. 최근 7일간의 새로운 공고 수집")
    print("3. 자동 수집 모드 시작 (매일 오전 9시)")
    print("4. 종료")
    
    while True:
        choice = input("\n선택하세요 (1-4): ").strip()
        
        if choice == '1':
            print("\n지난 1년간의 데이터를 수집합니다...")
            file_path = collector.collect_past_year_data()
            if file_path:
                print(f"✅ 데이터 수집 완료: {file_path}")
            else:
                print("❌ 데이터 수집 실패")
                
        elif choice == '2':
            print("\n최근 7일간의 새로운 공고를 수집합니다...")
            file_path = collector.collect_new_announcements()
            if file_path:
                print(f"✅ 새로운 공고 수집 완료: {file_path}")
            else:
                print("ℹ️ 새로운 공고가 없거나 수집 실패")
                
        elif choice == '3':
            print("\n자동 수집 모드를 시작합니다...")
            print("매일 오전 9시에 새로운 공고를 자동으로 수집합니다.")
            print("종료하려면 Ctrl+C를 누르세요.")
            
            # 스케줄 설정
            schedule.every().day.at("09:00").do(collector.collect_new_announcements)
            
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # 1분마다 스케줄 확인
            except KeyboardInterrupt:
                print("\n자동 수집 모드를 종료합니다.")
                
        elif choice == '4':
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다. 1-4 중에서 선택하세요.")

if __name__ == "__main__":
    main()
