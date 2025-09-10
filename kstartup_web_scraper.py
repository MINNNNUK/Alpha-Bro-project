#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-스타트업 웹사이트 스크래핑을 통한 정부지원사업 공고 데이터 수집기
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import os
import logging
from typing import List, Dict, Optional
import schedule
import threading
from pathlib import Path
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kstartup_web_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KStartupWebScraper:
    """K-스타트업 웹사이트 스크래핑 데이터 수집기"""
    
    def __init__(self):
        self.base_url = 'https://www.k-startup.go.kr'
        self.search_url = 'https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do'
        self.data_dir = Path('collected_data')
        self.data_dir.mkdir(exist_ok=True)
        
        # 세션 생성
        self.session = requests.Session()
        self.session.verify = False
        
        # 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def search_announcements(self, page: int = 1, per_page: int = 20) -> List[Dict]:
        """
        K-스타트업 웹사이트에서 공고를 검색합니다.
        
        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수
            
        Returns:
            공고 데이터 리스트
        """
        try:
            # 검색 파라미터
            params = {
                'schM': 'list',
                'page': page,
                'perPage': per_page,
                'sort': 'rcptEndDt',
                'order': 'asc'
            }
            
            logger.info(f"웹사이트 스크래핑 중: 페이지 {page}")
            
            response = self.session.get(self.search_url, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 공고 목록 추출
            announcements = []
            
            # 공고 테이블 찾기
            table = soup.find('table', class_='tbl_list')
            if not table:
                logger.warning("공고 테이블을 찾을 수 없습니다.")
                return announcements
            
            rows = table.find('tbody').find_all('tr')
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 6:
                        continue
                    
                    # 공고 정보 추출
                    announcement = {
                        '공고번호': cells[0].get_text(strip=True),
                        '사업명': cells[1].find('a').get_text(strip=True) if cells[1].find('a') else cells[1].get_text(strip=True),
                        '공고링크': self.base_url + cells[1].find('a')['href'] if cells[1].find('a') else '',
                        '기관명': cells[2].get_text(strip=True),
                        '접수시작일': cells[3].get_text(strip=True),
                        '접수종료일': cells[4].get_text(strip=True),
                        '상태': cells[5].get_text(strip=True),
                        '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    announcements.append(announcement)
                    
                except Exception as e:
                    logger.warning(f"행 파싱 오류: {str(e)}")
                    continue
            
            logger.info(f"페이지 {page}에서 {len(announcements)}개 공고 수집 완료")
            return announcements
            
        except Exception as e:
            logger.error(f"웹 스크래핑 오류: {str(e)}")
            return []
    
    def get_announcement_detail(self, announcement_url: str) -> Dict:
        """
        공고 상세 정보를 가져옵니다.
        
        Args:
            announcement_url: 공고 상세 페이지 URL
            
        Returns:
            상세 정보 딕셔너리
        """
        try:
            response = self.session.get(announcement_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            detail_info = {}
            
            # 상세 정보 테이블 찾기
            detail_table = soup.find('table', class_='tbl_view')
            if detail_table:
                rows = detail_table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        detail_info[key] = value
            
            return detail_info
            
        except Exception as e:
            logger.error(f"상세 정보 수집 오류: {str(e)}")
            return {}
    
    def collect_all_announcements(self, max_pages: int = 10) -> List[Dict]:
        """
        모든 공고 데이터를 수집합니다.
        
        Args:
            max_pages: 최대 수집할 페이지 수
            
        Returns:
            수집된 공고 데이터 리스트
        """
        all_announcements = []
        
        for page in range(1, max_pages + 1):
            announcements = self.search_announcements(page)
            
            if not announcements:
                logger.info(f"페이지 {page}에 더 이상 데이터가 없습니다.")
                break
            
            all_announcements.extend(announcements)
            logger.info(f"누적 수집: {len(all_announcements)}개")
            
            # 요청 간격 조절
            time.sleep(2)
        
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
            filename = f"kstartup_web_scraped_{timestamp}.xlsx"
            
        filepath = self.data_dir / filename
        
        try:
            df = pd.DataFrame(announcements)
            
            # 엑셀 파일로 저장
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='공고데이터', index=False)
                
                # 워크시트 스타일링
                worksheet = writer.sheets['공고데이터']
                
                # 컬럼 너비 자동 조정
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
            filename = f"kstartup_web_scraped_{timestamp}.csv"
            
        filepath = self.data_dir / filename
        
        try:
            df = pd.DataFrame(announcements)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"데이터가 {filepath}에 저장되었습니다.")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"CSV 저장 오류: {str(e)}")
            return None
    
    def collect_recent_announcements(self) -> str:
        """
        최근 공고를 수집합니다.
        
        Returns:
            저장된 파일 경로
        """
        logger.info("최근 공고 수집 시작")
        
        announcements = self.collect_all_announcements(max_pages=5)
        
        if announcements:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = self.save_to_excel(announcements, f"kstartup_recent_{timestamp}.xlsx")
            csv_file = self.save_to_csv(announcements, f"kstartup_recent_{timestamp}.csv")
            return excel_file
        else:
            logger.error("데이터 수집에 실패했습니다.")
            return None

def main():
    """메인 실행 함수"""
    # 스크래퍼 초기화
    scraper = KStartupWebScraper()
    
    print("=== K-스타트업 웹 스크래핑 데이터 수집기 ===")
    print("1. 최근 공고 수집 (5페이지)")
    print("2. 자동 수집 모드 시작 (매일 오전 9시)")
    print("3. 종료")
    
    while True:
        choice = input("\n선택하세요 (1-3): ").strip()
        
        if choice == '1':
            print("\n최근 공고를 수집합니다...")
            file_path = scraper.collect_recent_announcements()
            if file_path:
                print(f"✅ 데이터 수집 완료: {file_path}")
            else:
                print("❌ 데이터 수집 실패")
                
        elif choice == '2':
            print("\n자동 수집 모드를 시작합니다...")
            print("매일 오전 9시에 새로운 공고를 자동으로 수집합니다.")
            print("종료하려면 Ctrl+C를 누르세요.")
            
            # 스케줄 설정
            schedule.every().day.at("09:00").do(scraper.collect_recent_announcements)
            
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # 1분마다 스케줄 확인
            except KeyboardInterrupt:
                print("\n자동 수집 모드를 종료합니다.")
                
        elif choice == '3':
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다. 1-3 중에서 선택하세요.")

if __name__ == "__main__":
    main()
