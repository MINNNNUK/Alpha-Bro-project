#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-스타트업 API를 활용한 정부지원사업 공고 데이터 수집기 (curl 기반)
"""

import subprocess
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

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kstartup_curl_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KStartupCurlCollector:
    """K-스타트업 API curl 기반 데이터 수집기"""
    
    def __init__(self, service_key: str):
        self.api_url = 'https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01'
        self.service_key = service_key
        self.data_dir = Path('collected_data')
        self.data_dir.mkdir(exist_ok=True)
        
    def fetch_announcements_curl(self, start_date: str, end_date: str, page_no: int = 1, num_of_rows: int = 100) -> Optional[Dict]:
        """
        curl을 사용하여 API에서 공고 데이터를 가져옵니다.
        
        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            page_no: 페이지 번호
            num_of_rows: 페이지당 행 수
            
        Returns:
            파싱된 데이터 딕셔너리 또는 None
        """
        params = {
            'serviceKey': self.service_key,
            'startDate': start_date,
            'endDate': end_date,
            'pageNo': page_no,
            'numOfRows': num_of_rows,
            'resultType': 'xml'
        }
        
        # URL 구성
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.api_url}?{param_string}"
        
        try:
            logger.info(f"API 호출 중: {start_date} ~ {end_date}, 페이지 {page_no}")
            
            # curl 명령어 실행
            cmd = ['curl', '-k', '-s', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("API 호출 성공")
                
                # XML 파싱
                root = ET.fromstring(result.stdout)
                
                # 결과 정보 추출
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
                        # 데이터 아이템들 파싱
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
                
        except subprocess.TimeoutExpired:
            logger.error("curl 실행 시간 초과")
            return None
        except ET.ParseError as e:
            logger.error(f"XML 파싱 오류: {str(e)}")
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
            data = self.fetch_announcements_curl(start_date, end_date, page_no, num_of_rows)
            
            if not data:
                logger.warning(f"페이지 {page_no} 데이터 수집 실패")
                break
                
            # 총 개수 확인
            total_count = data.get('totalCount', 0)
            current_count = data.get('currentCount', 0)
            
            if page_no == 1:
                logger.info(f"총 {total_count}개의 공고가 있습니다.")
            
            # 아이템 추출
            items = data.get('items', [])
            if not items:
                logger.info(f"페이지 {page_no}에 더 이상 데이터가 없습니다.")
                break
                
            all_announcements.extend(items)
            logger.info(f"페이지 {page_no}에서 {len(items)}개 공고 수집 완료 (누적: {len(all_announcements)}개)")
            
            # 다음 페이지 확인
            if len(items) < num_of_rows or len(all_announcements) >= total_count:
                logger.info("마지막 페이지에 도달했습니다.")
                break
                
            page_no += 1
            time.sleep(1)  # API 호출 간격 조절
                
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
            
            # 컬럼명을 한국어로 정리
            column_mapping = {
                'id': 'ID',
                'pbanc_sn': '공고번호',
                'biz_pbanc_nm': '사업공고명',
                'intg_pbanc_biz_nm': '통합사업명',
                'pbanc_ntrp_nm': '공고기관명',
                'biz_prch_dprt_nm': '사업담당부서',
                'pbanc_ctnt': '공고내용',
                'pbanc_rcpt_bgng_dt': '접수시작일',
                'pbanc_rcpt_end_dt': '접수종료일',
                'aply_trgt': '신청대상',
                'aply_trgt_ctnt': '신청대상내용',
                'supt_regin': '지원지역',
                'supt_biz_clsfc': '지원사업분류',
                'biz_enyy': '사업경력',
                'biz_trgt_age': '사업대상연령',
                'sprv_inst': '감독기관',
                'aply_mthd_onli_rcpt_istc': '온라인신청방법',
                'aply_mthd_eml_rcpt_istc': '이메일신청방법',
                'aply_mthd_fax_rcpt_istc': '팩스신청방법',
                'aply_mthd_pssr_rcpt_istc': '우편신청방법',
                'aply_mthd_vst_rcpt_istc': '방문신청방법',
                'aply_mthd_etc_istc': '기타신청방법',
                'biz_aply_url': '사업신청URL',
                'detl_pg_url': '상세페이지URL',
                'biz_gdnc_url': '사업안내URL',
                'prch_cnpl_no': '담당연락처',
                'aply_excl_trgt_ctnt': '신청제외대상내용',
                'rcrt_prgs_yn': '모집진행여부',
                'intg_pbanc_yn': '통합공고여부',
                'prfn_matr': '우대사항'
            }
            
            # 컬럼명 변경
            df = df.rename(columns=column_mapping)
            
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
            filename = f"kstartup_announcements_{timestamp}.csv"
            
        filepath = self.data_dir / filename
        
        try:
            df = pd.DataFrame(announcements)
            
            # 컬럼명을 한국어로 정리
            column_mapping = {
                'id': 'ID',
                'pbanc_sn': '공고번호',
                'biz_pbanc_nm': '사업공고명',
                'intg_pbanc_biz_nm': '통합사업명',
                'pbanc_ntrp_nm': '공고기관명',
                'biz_prch_dprt_nm': '사업담당부서',
                'pbanc_ctnt': '공고내용',
                'pbanc_rcpt_bgng_dt': '접수시작일',
                'pbanc_rcpt_end_dt': '접수종료일',
                'aply_trgt': '신청대상',
                'aply_trgt_ctnt': '신청대상내용',
                'supt_regin': '지원지역',
                'supt_biz_clsfc': '지원사업분류',
                'biz_enyy': '사업경력',
                'biz_trgt_age': '사업대상연령',
                'sprv_inst': '감독기관',
                'aply_mthd_onli_rcpt_istc': '온라인신청방법',
                'aply_mthd_eml_rcpt_istc': '이메일신청방법',
                'aply_mthd_fax_rcpt_istc': '팩스신청방법',
                'aply_mthd_pssr_rcpt_istc': '우편신청방법',
                'aply_mthd_vst_rcpt_istc': '방문신청방법',
                'aply_mthd_etc_istc': '기타신청방법',
                'biz_aply_url': '사업신청URL',
                'detl_pg_url': '상세페이지URL',
                'biz_gdnc_url': '사업안내URL',
                'prch_cnpl_no': '담당연락처',
                'aply_excl_trgt_ctnt': '신청제외대상내용',
                'rcrt_prgs_yn': '모집진행여부',
                'intg_pbanc_yn': '통합공고여부',
                'prfn_matr': '우대사항'
            }
            
            # 컬럼명 변경
            df = df.rename(columns=column_mapping)
            
            # CSV 파일로 저장
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
    collector = KStartupCurlCollector(SERVICE_KEY)
    
    print("=== K-스타트업 정부지원사업 공고 데이터 수집기 (curl 버전) ===")
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
