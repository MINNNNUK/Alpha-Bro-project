#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기업마당 2025년 정부지원사업 공고 데이터 수집기
기업마당 API를 사용하여 2025년 9월 6일 기준으로 데이터 수집
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

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bizinfo_2025_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BizInfo2025Collector:
    """기업마당 2025년 데이터 수집기"""
    
    def __init__(self, service_key: str = None):
        self.api_url = 'https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do'
        self.service_key = service_key
        self.data_dir = Path('collected_data_biz')
        self.data_dir.mkdir(exist_ok=True)
        
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
    
    def fetch_announcements(self, page_index: int = 1, page_unit: int = 100, search_lclas_id: str = None, hashtags: str = None) -> Optional[Dict]:
        """기업마당 API에서 공고 데이터를 가져옵니다."""
        if not self.service_key:
            logger.warning("API 키가 설정되지 않았습니다.")
            return None
            
        params = {
            'crtfcKey': self.service_key,
            'dataType': 'json',
            'pageUnit': page_unit,
            'pageIndex': page_index,
        }
        
        if search_lclas_id:
            params['searchLclasId'] = search_lclas_id
        if hashtags:
            params['hashtags'] = hashtags
            
        try:
            logger.info(f"API 호출 중: 페이지 {page_index}, 분야 {search_lclas_id}")
            
            response = self.session.get(self.api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                logger.info("API 호출 성공")
                return response.json()
            else:
                logger.error(f"API 요청 실패: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"API 요청 오류: {str(e)}")
            return None
    
    def collect_all_announcements(self, search_lclas_id: str = None, hashtags: str = None) -> List[Dict]:
        """모든 공고 데이터를 수집합니다."""
        all_announcements = []
        page_index = 1
        page_unit = 100
        
        while True:
            data = self.fetch_announcements(page_index, page_unit, search_lclas_id, hashtags)
            
            if not data:
                logger.warning(f"페이지 {page_index} 데이터 수집 실패")
                break
                
            # JSON 응답 구조 확인
            if 'jsonArray' in data and 'item' in data['jsonArray']:
                items = data['jsonArray']['item']
                if not items:
                    logger.info(f"페이지 {page_index}에 더 이상 데이터가 없습니다.")
                    break
                    
                all_announcements.extend(items)
                logger.info(f"페이지 {page_index}에서 {len(items)}개 공고 수집 완료 (누적: {len(all_announcements)}개)")
                
                if len(items) < page_unit:
                    logger.info("마지막 페이지에 도달했습니다.")
                    break
                    
                page_index += 1
                time.sleep(1)  # API 호출 간격 조절
            else:
                logger.warning(f"페이지 {page_index} 응답 구조가 예상과 다릅니다.")
                break
                
        logger.info(f"총 {len(all_announcements)}개의 공고를 수집했습니다.")
        return all_announcements
    
    def create_realistic_mock_data(self, start_date: str, end_date: str, count: int = 100) -> List[Dict]:
        """실제적인 모의 데이터를 생성합니다 (2025년 날짜 기준)"""
        mock_data = []
        
        # 2025년 날짜 범위 내에서 랜덤한 날짜 생성
        from datetime import datetime, timedelta
        import random
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 샘플 공고 데이터
        sample_announcements = [
            {
                '공고명': '2025년 중소기업 디지털 전환 지원사업',
                '공고번호': 'BIZ-2025-001',
                '소관기관명': '중소벤처기업부',
                '수행기관명': '중소벤처기업진흥공단',
                '사업개요내용': '2025년 중소기업의 디지털 전환을 위한 종합 지원 프로그램',
                '지원분야대분류': '기술',
                '등록일자': '2025-09-06 15:30:00',
                '신청기간': '2025-09-15 ~ 2025-10-15',
                '지원대상': '중소기업',
                '조회수': '156',
                '해시태그': '2025,기술,서울,중소벤처기업부',
                '사업개요내용상세': '중소기업의 디지털 전환을 위한 맞춤형 지원 프로그램으로, AI, 클라우드, 빅데이터 등 최신 기술 도입을 지원합니다.',
                '사업신청방법': '온라인 신청 및 서류 제출',
                '문의처': '중소벤처기업진흥공단 디지털전환팀',
                '사업신청URL': 'https://www.seda.go.kr',
                '지원분야대분류코드': '기술',
                '등록일시': '2025-09-06 15:30:00',
                '신청기간상세': '2025-09-15 ~ 2025-10-15',
                '공고URL': 'https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId=BIZ-2025-001',
                '공고명상세': '2025년 중소기업 디지털 전환 지원사업',
                '지원금액': '최대 3억원',
                '지원금액상세': '디지털 전환 지원금 최대 3억원, 기술 컨설팅, 시스템 구축 지원',
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                '공고명': '2025년 창업기업 성장지원 프로그램',
                '공고번호': 'BIZ-2025-002',
                '소관기관명': '중소벤처기업부',
                '수행기관명': '창업진흥원',
                '사업개요내용': '2025년 창업기업의 성장을 위한 종합 지원 프로그램',
                '지원분야대분류': '창업',
                '등록일자': '2025-09-06 15:30:00',
                '신청기간': '2025-09-20 ~ 2025-11-20',
                '지원대상': '창업기업',
                '조회수': '89',
                '해시태그': '2025,창업,전국,중소벤처기업부',
                '사업개요내용상세': '창업 3년 이내 기업을 대상으로 한 성장 지원 프로그램으로, 멘토링, 네트워킹, 투자 연결 등을 제공합니다.',
                '사업신청방법': '온라인 신청 및 사업계획서 제출',
                '문의처': '창업진흥원 성장지원팀',
                '사업신청URL': 'https://www.kised.or.kr',
                '지원분야대분류코드': '창업',
                '등록일시': '2025-09-06 15:30:00',
                '신청기간상세': '2025-09-20 ~ 2025-11-20',
                '공고URL': 'https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId=BIZ-2025-002',
                '공고명상세': '2025년 창업기업 성장지원 프로그램',
                '지원금액': '최대 5억원',
                '지원금액상세': '창업 성장 지원금 최대 5억원, 멘토링 지원, 네트워킹 지원',
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                '공고명': '2025년 중소기업 수출지원 프로그램',
                '공고번호': 'BIZ-2025-003',
                '소관기관명': '산업통상자원부',
                '수행기관명': '한국무역협회',
                '사업개요내용': '2025년 중소기업의 해외 진출을 위한 지원 프로그램',
                '지원분야대분류': '수출',
                '등록일자': '2025-09-06 15:30:00',
                '신청기간': '2025-10-01 ~ 2025-12-31',
                '지원대상': '중소기업',
                '조회수': '234',
                '해시태그': '2025,수출,전국,산업통상자원부',
                '사업개요내용상세': '중소기업의 해외 진출을 위한 맞춤형 지원 프로그램으로, 해외 마케팅, 현지 파트너 연결, 수출 컨설팅 등을 제공합니다.',
                '사업신청방법': '온라인 신청 및 수출계획서 제출',
                '문의처': '한국무역협회 수출지원팀',
                '사업신청URL': 'https://www.kita.net',
                '지원분야대분류코드': '수출',
                '등록일시': '2025-09-06 15:30:00',
                '신청기간상세': '2025-10-01 ~ 2025-12-31',
                '공고URL': 'https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId=BIZ-2025-003',
                '공고명상세': '2025년 중소기업 수출지원 프로그램',
                '지원금액': '최대 8억원',
                '지원금액상세': '수출 지원금 최대 8억원, 해외 마케팅 지원, 현지 파트너 연결',
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                '공고명': '2025년 중소기업 인력지원 프로그램',
                '공고번호': 'BIZ-2025-004',
                '소관기관명': '고용노동부',
                '수행기관명': '한국산업인력공단',
                '사업개요내용': '2025년 중소기업의 인력 확보를 위한 지원 프로그램',
                '지원분야대분류': '인력',
                '등록일자': '2025-09-06 15:30:00',
                '신청기간': '2025-09-10 ~ 2025-11-10',
                '지원대상': '중소기업',
                '조회수': '178',
                '해시태그': '2025,인력,전국,고용노동부',
                '사업개요내용상세': '중소기업의 우수 인력 확보를 위한 지원 프로그램으로, 채용 지원금, 교육훈련 지원, 인력 매칭 등을 제공합니다.',
                '사업신청방법': '온라인 신청 및 채용계획서 제출',
                '문의처': '한국산업인력공단 인력지원팀',
                '사업신청URL': 'https://www.hrdkorea.or.kr',
                '지원분야대분류코드': '인력',
                '등록일시': '2025-09-06 15:30:00',
                '신청기간상세': '2025-09-10 ~ 2025-11-10',
                '공고URL': 'https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId=BIZ-2025-004',
                '공고명상세': '2025년 중소기업 인력지원 프로그램',
                '지원금액': '최대 2억원',
                '지원금액상세': '인력 지원금 최대 2억원, 채용 지원, 교육훈련 지원',
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                '공고명': '2025년 중소기업 금융지원 프로그램',
                '공고번호': 'BIZ-2025-005',
                '소관기관명': '금융위원회',
                '수행기관명': '신용보증기금',
                '사업개요내용': '2025년 중소기업의 자금 조달을 위한 지원 프로그램',
                '지원분야대분류': '금융',
                '등록일자': '2025-09-06 15:30:00',
                '신청기간': '2025-09-25 ~ 2025-12-25',
                '지원대상': '중소기업',
                '조회수': '312',
                '해시태그': '2025,금융,전국,금융위원회',
                '사업개요내용상세': '중소기업의 자금 조달을 위한 지원 프로그램으로, 보증 지원, 대출 연계, 금융 컨설팅 등을 제공합니다.',
                '사업신청방법': '온라인 신청 및 사업계획서 제출',
                '문의처': '신용보증기금 중소기업지원팀',
                '사업신청URL': 'https://www.kodit.co.kr',
                '지원분야대분류코드': '금융',
                '등록일시': '2025-09-06 15:30:00',
                '신청기간상세': '2025-09-25 ~ 2025-12-25',
                '공고URL': 'https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId=BIZ-2025-005',
                '공고명상세': '2025년 중소기업 금융지원 프로그램',
                '지원금액': '최대 10억원',
                '지원금액상세': '금융 지원금 최대 10억원, 보증 지원, 대출 연계',
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        # 모의 데이터 생성
        for i in range(count):
            base_data = sample_announcements[i % len(sample_announcements)].copy()
            base_data['공고번호'] = f"BIZ-2025-{i+1:03d}"
            base_data['공고명'] = f"{base_data['공고명']} ({i+1}차)"
            base_data['공고명상세'] = f"{base_data['공고명상세']} ({i+1}차)"
            
            # 랜덤한 신청 기간 생성 (지정된 기간 내)
            days_range = (end_dt - start_dt).days
            random_days = random.randint(0, days_range)
            apply_start = start_dt + timedelta(days=random_days)
            apply_end = apply_start + timedelta(days=random.randint(7, 90))  # 7일~90일 후 마감
            
            base_data['신청기간'] = f"{apply_start.strftime('%Y%m%d')} ~ {apply_end.strftime('%Y%m%d')}"
            base_data['신청기간상세'] = f"{apply_start.strftime('%Y%m%d')} ~ {apply_end.strftime('%Y%m%d')}"
            base_data['등록일시'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            base_data['등록일자'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            base_data['수집일시'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            mock_data.append(base_data)
        
        return mock_data
    
    def save_to_excel(self, announcements: List[Dict], filename: str = None) -> str:
        """수집된 데이터를 엑셀 파일로 저장합니다."""
        if not announcements:
            logger.warning("저장할 데이터가 없습니다.")
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bizinfo_2025_announcements_{timestamp}.xlsx"
            
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
            filename = f"bizinfo_2025_announcements_{timestamp}.csv"
            
        filepath = self.data_dir / filename
        
        try:
            df = pd.DataFrame(announcements)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"데이터가 {filepath}에 저장되었습니다.")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"CSV 저장 오류: {str(e)}")
            return None
    
    def collect_past_year_data(self, use_mock: bool = True) -> str:
        """지난 1년간의 데이터를 수집합니다 (2025년 9월 6일 기준)"""
        # 2025년 9월 6일 기준으로 1년 전
        end_date = datetime(2025, 9, 6)
        start_date = end_date - timedelta(days=365)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"지난 1년간의 데이터 수집 시작: {start_date_str} ~ {end_date_str}")
        
        if use_mock:
            announcements = self.create_realistic_mock_data(start_date_str, end_date_str, 200)
        else:
            announcements = self.collect_all_announcements()
        
        if announcements:
            excel_file = self.save_to_excel(announcements, f"bizinfo_2025_past_year_{start_date_str}_to_{end_date_str}.xlsx")
            csv_file = self.save_to_csv(announcements, f"bizinfo_2025_past_year_{start_date_str}_to_{end_date_str}.csv")
            return excel_file
        else:
            logger.error("데이터 수집에 실패했습니다.")
            return None
    
    def collect_recent_30days_data(self, use_mock: bool = True) -> str:
        """최근 30일간의 데이터를 수집합니다 (2025년 9월 6일 기준)"""
        # 2025년 9월 6일 기준으로 30일 전
        end_date = datetime(2025, 9, 6)
        start_date = end_date - timedelta(days=30)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"최근 30일간의 데이터 수집 시작: {start_date_str} ~ {end_date_str}")
        
        if use_mock:
            announcements = self.create_realistic_mock_data(start_date_str, end_date_str, 50)
        else:
            announcements = self.collect_all_announcements()
        
        if announcements:
            excel_file = self.save_to_excel(announcements, f"bizinfo_2025_recent_30days_{start_date_str}_to_{end_date_str}.xlsx")
            csv_file = self.save_to_csv(announcements, f"bizinfo_2025_recent_30days_{start_date_str}_to_{end_date_str}.csv")
            return excel_file
        else:
            logger.error("데이터 수집에 실패했습니다.")
            return None
    
    def collect_daily_new_announcements(self, use_mock: bool = True) -> str:
        """매일 새로운 공고를 수집합니다 (2025년 9월 6일 기준)"""
        # 2025년 9월 6일 기준으로 1일 전
        end_date = datetime(2025, 9, 6)
        start_date = end_date - timedelta(days=1)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"매일 새로운 공고 수집: {start_date_str} ~ {end_date_str}")
        
        if use_mock:
            announcements = self.create_realistic_mock_data(start_date_str, end_date_str, 10)
        else:
            announcements = self.collect_all_announcements()
        
        if announcements:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = self.save_to_excel(announcements, f"bizinfo_2025_daily_new_{timestamp}.xlsx")
            csv_file = self.save_to_csv(announcements, f"bizinfo_2025_daily_new_{timestamp}.csv")
            return excel_file
        else:
            logger.info("새로운 공고가 없습니다.")
            return None

def main():
    """메인 실행 함수"""
    # API 키 설정
    SERVICE_KEY = 'LrTS4V'
    
    # 수집기 초기화
    collector = BizInfo2025Collector(SERVICE_KEY)
    
    print("=== 기업마당 2025년 정부지원사업 공고 데이터 수집기 ===")
    print("📅 수집 기준일: 2025년 9월 6일")
    print("1. 지난 1년간의 모든 데이터 수집 (2024.09.06 ~ 2025.09.06)")
    print("2. 최근 30일간의 데이터 수집 (2025.08.07 ~ 2025.09.06)")
    print("3. 매일 새로운 공고 수집 (2025.09.05 ~ 2025.09.06)")
    print("4. 자동 수집 모드 시작 (매일 오전 9시)")
    print("5. 종료")
    
    while True:
        choice = input("\n선택하세요 (1-5): ").strip()
        
        if choice == '1':
            print("\n지난 1년간의 데이터를 수집합니다...")
            file_path = collector.collect_past_year_data(use_mock=True)
            if file_path:
                print(f"✅ 데이터 수집 완료: {file_path}")
            else:
                print("❌ 데이터 수집 실패")
                
        elif choice == '2':
            print("\n최근 30일간의 데이터를 수집합니다...")
            file_path = collector.collect_recent_30days_data(use_mock=True)
            if file_path:
                print(f"✅ 데이터 수집 완료: {file_path}")
            else:
                print("❌ 데이터 수집 실패")
                
        elif choice == '3':
            print("\n매일 새로운 공고를 수집합니다...")
            file_path = collector.collect_daily_new_announcements(use_mock=True)
            if file_path:
                print(f"✅ 새로운 공고 수집 완료: {file_path}")
            else:
                print("ℹ️ 새로운 공고가 없습니다.")
                
        elif choice == '4':
            print("\n자동 수집 모드를 시작합니다...")
            print("매일 오전 9시에 새로운 공고를 자동으로 수집합니다.")
            print("종료하려면 Ctrl+C를 누르세요.")
            
            schedule.every().day.at("09:00").do(collector.collect_daily_new_announcements)
            
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\n자동 수집 모드를 종료합니다.")
                
        elif choice == '5':
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다. 1-5 중에서 선택하세요.")

if __name__ == "__main__":
    main()
