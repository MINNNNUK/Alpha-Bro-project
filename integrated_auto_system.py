#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 자동화 시스템
매일 K-스타트업과 기업마당에서 데이터를 수집하고 Supabase에 저장하며 맞춤 추천을 생성
"""

import requests
import pandas as pd
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
import os
import logging
from typing import List, Dict, Optional, Any
import schedule
import threading
from pathlib import Path
import urllib3
import subprocess
import openai
import warnings
from supabase import create_client, Client
import sys
sys.path.append('/Users/minkim/git_test/kpmg-2025/data2/supabase1')
from config import SUPABASE_URL, SUPABASE_KEY

warnings.filterwarnings('ignore')

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integrated_auto_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegratedAutoSystem:
    """통합 자동화 시스템"""
    
    def __init__(self):
        # API 키 설정
        self.kstartup_service_key = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
        self.bizinfo_service_key = 'LrTS4V'
        
        # OpenAI API 설정
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        # Supabase 클라이언트 초기화
        try:
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase 연결 성공")
        except Exception as e:
            logger.error(f"Supabase 연결 실패: {e}")
            self.supabase = None
        
        # 경로 설정
        self.data_dir = Path('/Users/minkim/git_test/kpmg-2025/data2')
        self.kstartup_data_dir = self.data_dir / 'collected_data'
        self.bizinfo_data_dir = self.data_dir / 'collected_data_biz'
        self.alpha_companies_path = self.data_dir / 'alpha_companies.csv'
        
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
        
        # 고객사 정보 로드
        try:
            self.alpha_companies = pd.read_csv(self.alpha_companies_path)
            logger.info(f"고객사 정보 로드 완료: {len(self.alpha_companies)}개 기업")
        except Exception as e:
            logger.error(f"고객사 정보 로드 실패: {e}")
            self.alpha_companies = pd.DataFrame()
    
    def fetch_kstartup_announcements(self, start_date: str = "", end_date: str = "") -> List[Dict]:
        """K-스타트업 API에서 공고 데이터를 가져옵니다."""
        api_url = 'https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01'
        
        params = {
            'serviceKey': self.kstartup_service_key,
            'pageNo': 1,
            'numOfRows': 1000,
            'resultType': 'xml'
        }
        
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        
        try:
            logger.info(f"K-스타트업 API 호출 중: {start_date} ~ {end_date}")
            
            response = self.session.get(api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                
                # 오류 확인
                if root.tag == 'OpenAPI_ServiceResponse':
                    error_msg = root.find('.//errMsg')
                    if error_msg is not None:
                        logger.error(f"K-스타트업 API 오류: {error_msg.text}")
                        return []
                
                # 결과 추출
                items = []
                for item in root.findall('.//item'):
                    item_data = {}
                    for col in item.findall('col'):
                        name = col.get('name')
                        value = col.text if col.text else ''
                        item_data[name] = value
                    items.append(item_data)
                
                logger.info(f"K-스타트업에서 {len(items)}개 공고 수집")
                return items
            else:
                logger.error(f"K-스타트업 API 호출 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"K-스타트업 API 요청 오류: {str(e)}")
            return []
    
    def fetch_bizinfo_announcements(self, page_index: int = 1, page_unit: int = 100) -> List[Dict]:
        """기업마당 API에서 공고 데이터를 가져옵니다."""
        api_url = 'https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do'
        
        params = {
            'crtfcKey': self.bizinfo_service_key,
            'dataType': 'json',
            'pageUnit': page_unit,
            'pageIndex': page_index,
        }
        
        try:
            logger.info(f"기업마당 API 호출 중: 페이지 {page_index}")
            
            response = self.session.get(api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # 다양한 응답 구조 처리
                items = []
                if 'jsonArray' in data and 'item' in data['jsonArray']:
                    items = data['jsonArray']['item']
                elif 'item' in data:
                    items = data['item']
                elif isinstance(data, list):
                    items = data
                
                if items:
                    logger.info(f"기업마당에서 {len(items)}개 공고 수집")
                    return items
                else:
                    logger.warning("기업마당 API에서 공고 데이터를 찾을 수 없습니다.")
                    return []
            else:
                logger.error(f"기업마당 API 요청 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"기업마당 API 요청 오류: {str(e)}")
            return []
    
    def collect_daily_announcements(self) -> Dict[str, List[Dict]]:
        """매일 새로운 공고를 수집합니다."""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        logger.info(f"매일 신규 공고 수집 시작: {start_date} ~ {end_date}")
        
        # K-스타트업 신규 공고 수집
        kstartup_announcements = self.fetch_kstartup_announcements(start_date, end_date)
        
        # 기업마당 신규 공고 수집
        bizinfo_announcements = self.fetch_bizinfo_announcements()
        
        # 수집 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if kstartup_announcements:
            self.save_announcements_to_file(kstartup_announcements, f"kstartup_daily_new_{timestamp}", self.kstartup_data_dir)
        
        if bizinfo_announcements:
            self.save_announcements_to_file(bizinfo_announcements, f"bizinfo_daily_new_{timestamp}", self.bizinfo_data_dir)
        
        return {
            'kstartup': kstartup_announcements,
            'bizinfo': bizinfo_announcements,
            'timestamp': timestamp
        }
    
    def save_announcements_to_file(self, announcements: List[Dict], filename_prefix: str, data_dir: Path):
        """수집된 공고를 파일로 저장합니다."""
        if not announcements:
            return
        
        data_dir.mkdir(exist_ok=True)
        
        # CSV 저장
        df = pd.DataFrame(announcements)
        csv_file = data_dir / f"{filename_prefix}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f"CSV 파일 저장: {csv_file}")
        
        # Excel 저장
        excel_file = data_dir / f"{filename_prefix}.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='공고데이터', index=False)
        logger.info(f"Excel 파일 저장: {excel_file}")
    
    def save_announcements_to_supabase(self, announcements: List[Dict], source: str) -> bool:
        """수집된 공고를 Supabase에 저장합니다."""
        if not self.supabase or not announcements:
            return False
        
        try:
            # 공고 데이터를 Supabase 형식으로 변환
            supabase_data = []
            for announcement in announcements:
                if source == 'kstartup':
                    # K-스타트업 데이터 변환
                    supabase_data.append({
                        'title': announcement.get('사업공고명', ''),
                        'agency': announcement.get('공고기관명', ''),
                        'content': announcement.get('공고내용', ''),
                        'target': announcement.get('신청대상', ''),
                        'target_detail': announcement.get('신청대상내용', ''),
                        'region': announcement.get('지원지역', ''),
                        'category': announcement.get('지원사업분류', ''),
                        'experience': announcement.get('사업경력', ''),
                        'age_range': announcement.get('사업대상연령', ''),
                        'supervisor': announcement.get('감독기관', ''),
                        'application_url': announcement.get('온라인신청방법', ''),
                        'detail_url': announcement.get('상세페이지URL', ''),
                        'contact': announcement.get('담당연락처', ''),
                        'is_active': announcement.get('모집진행여부', 'N') == 'Y',
                        'is_integrated': announcement.get('통합공고여부', 'N') == 'Y',
                        'preference': announcement.get('우대사항', ''),
                        'amount_text': announcement.get('지원금액', ''),
                        'amount_detail': announcement.get('지원금액상세', ''),
                        'start_date': announcement.get('접수시작일', ''),
                        'end_date': announcement.get('접수종료일', ''),
                        'source': 'kstartup',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    })
                elif source == 'bizinfo':
                    # 기업마당 데이터 변환
                    supabase_data.append({
                        'title': announcement.get('pblancNm', ''),
                        'agency': announcement.get('excInsttNm', ''),
                        'content': announcement.get('description', ''),
                        'target': announcement.get('지원대상', ''),
                        'target_detail': announcement.get('사업개요내용', ''),
                        'region': announcement.get('지원지역', ''),
                        'category': announcement.get('지원분야대분류', ''),
                        'experience': announcement.get('사업경력', ''),
                        'age_range': announcement.get('사업대상연령', ''),
                        'supervisor': announcement.get('소관기관명', ''),
                        'application_url': announcement.get('사업신청URL', ''),
                        'detail_url': announcement.get('공고URL', ''),
                        'contact': announcement.get('문의처', ''),
                        'is_active': True,  # 기업마당은 기본적으로 활성
                        'is_integrated': False,
                        'preference': announcement.get('해시태그', ''),
                        'amount_text': announcement.get('지원금액', ''),
                        'amount_detail': announcement.get('지원금액상세', ''),
                        'start_date': announcement.get('신청기간', '').split(' ~ ')[0] if announcement.get('신청기간') else '',
                        'end_date': announcement.get('신청기간', '').split(' ~ ')[1] if announcement.get('신청기간') and ' ~ ' in announcement.get('신청기간') else '',
                        'source': 'bizinfo',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    })
            
            # Supabase에 저장
            result = self.supabase.table('announcements').insert(supabase_data).execute()
            logger.info(f"Supabase에 {len(supabase_data)}개 공고 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"Supabase 저장 실패: {e}")
            return False
    
    def get_company_info(self, company_idx: int) -> Dict[str, Any]:
        """특정 회사의 정보를 반환합니다."""
        if company_idx >= len(self.alpha_companies):
            return None
        
        company = self.alpha_companies.iloc[company_idx]
        return {
            'no': company['No.'],
            'company_type': company['기업형태'],
            'location': company['소재지'],
            'establishment_date': company['설립연월일'],
            'main_business': company['주업종 (사업자등록증 상)'],
            'main_industry': company['주요 산업'],
            'business_description': company['사업아이템 한 줄 소개'],
            'revenue': company['#매출'],
            'employees': company['#고용'],
            'exports': company['#수출'],
            'investment': company['#투자'],
            'patents': company['#기술특허(등록)'],
            'certifications': company['#기업인증'],
            'specialization': company['특화분야']
        }
    
    def create_recommendation_prompt(self, company_info: Dict[str, Any], new_announcements: List[Dict]) -> str:
        """회사 정보와 신규 공고를 바탕으로 추천 프롬프트를 생성합니다."""
        
        # 신규 공고 정보 정리
        announcements_text = "=== 신규 공고 목록 ===\n"
        for i, announcement in enumerate(new_announcements[:30], 1):  # 최대 30개만 표시
            if '사업공고명' in announcement:  # K-스타트업 데이터
                announcements_text += f"{i}. {announcement['사업공고명']}\n"
                announcements_text += f"   - 기관: {announcement.get('공고기관명', 'N/A')}\n"
                announcements_text += f"   - 접수기간: {announcement.get('접수시작일', 'N/A')} ~ {announcement.get('접수종료일', 'N/A')}\n"
                announcements_text += f"   - 내용: {announcement.get('공고내용', 'N/A')[:100]}...\n"
                announcements_text += f"   - 지원금액: {announcement.get('지원금액', 'N/A')}\n\n"
            elif 'pblancNm' in announcement:  # 기업마당 데이터
                announcements_text += f"{i}. {announcement['pblancNm']}\n"
                announcements_text += f"   - 기관: {announcement.get('excInsttNm', 'N/A')}\n"
                announcements_text += f"   - 접수기간: {announcement.get('reqstBeginEndDe', 'N/A')}\n"
                announcements_text += f"   - 내용: {announcement.get('description', 'N/A')[:100]}...\n"
                announcements_text += f"   - 지원금액: {announcement.get('지원금액', 'N/A')}\n\n"
        
        prompt = f"""
{announcements_text}

다음은 추천을 받을 기업의 정보입니다:

기업 정보:
- 기업형태: {company_info['company_type']}
- 소재지: {company_info['location']}
- 설립일: {company_info['establishment_date']}
- 주업종: {company_info['main_business']}
- 주요 산업: {company_info['main_industry']}
- 사업 아이템: {company_info['business_description']}
- 매출: {company_info['revenue']}
- 고용인원: {company_info['employees']}
- 수출: {company_info['exports']}
- 투자: {company_info['investment']}
- 특허: {company_info['patents']}
- 인증: {company_info['certifications']}
- 특화분야: {company_info['specialization']}

위 신규 공고들 중에서 이 기업에 가장 적합한 공고들을 추천해주세요.
중요: 
1. 추천 개수에 제한이 없습니다. 가능한 한 많은 공고를 추천해주세요.
2. 오직 기업의 특성과 공고의 내용이 얼마나 잘 맞는지만 고려해주세요.
3. 신규 공고만 추천해주세요.

반드시 다음 형식의 JSON으로 응답해주세요:
[
  {{
    "추천점수": 85,
    "공고이름": "2025년 디지털 전환 지원사업",
    "추천이유": "추천 이유를 두괄식으로 설명",
    "모집일": "2025-09-05",
    "마감일": "2025-10-04",
    "남은기간": "현재 지원 가능",
    "투자금액": "최대 5천만원",
    "투자금액사용처": "디지털 전환 관련 비용",
    "공고상태": "현재 지원 가능",
    "공고연도": "2025",
    "공고월": "9"
  }}
]

추천 개수에 제한이 없습니다. 가능한 한 많은 공고를 추천해주세요.
"""
        return prompt
    
    def call_openai_api(self, prompt: str) -> str:
        """OpenAI API를 호출하여 추천을 받습니다."""
        if not self.openai_api_key:
            logger.warning("OpenAI API 키가 설정되지 않았습니다.")
            return None
        
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "당신은 정부 지원사업 추천 전문가입니다. 기업의 특성과 요구사항을 분석하여 가장 적합한 지원사업을 추천해주세요. 추천 개수에 제한이 없으므로 가능한 한 많은 공고를 추천해주세요. 신규 공고만 추천해주세요. 반드시 JSON 형식으로 응답해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            return None
    
    def parse_recommendations(self, response: str) -> List[Dict[str, Any]]:
        """LLM 응답을 파싱하여 추천 목록을 반환합니다."""
        try:
            # JSON 코드 블록에서 JSON 추출
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                if json_end != -1:
                    json_str = response[json_start:json_end].strip()
                    try:
                        data = json.loads(json_str)
                        if isinstance(data, list):
                            return data
                    except:
                        pass
            
            # 직접 JSON 파싱 시도
            if response.startswith('[') or response.startswith('{'):
                data = json.loads(response)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
            
            return []
            
        except Exception as e:
            logger.error(f"추천 파싱 실패: {e}")
            return []
    
    def generate_recommendations_for_company(self, company_idx: int, new_announcements: List[Dict]) -> Dict[str, Any]:
        """특정 회사에 대한 신규 공고 추천을 생성합니다."""
        company_info = self.get_company_info(company_idx)
        if not company_info:
            return None
        
        logger.info(f"{company_info['no']}번 기업 신규 공고 추천 생성 중...")
        logger.info(f"기업명: {company_info['business_description']}")
        
        # 프롬프트 생성
        prompt = self.create_recommendation_prompt(company_info, new_announcements)
        
        # LLM 호출
        response = self.call_openai_api(prompt)
        if not response:
            logger.warning("LLM 호출 실패")
            return None
        
        recommendations = self.parse_recommendations(response)
        
        if not recommendations:
            logger.warning("추천 파싱 실패")
            return None
        
        logger.info(f"✓ {len(recommendations)}개 신규 공고 추천 생성됨")
        return {
            'company_info': company_info,
            'recommendations': recommendations,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def generate_all_recommendations(self, new_announcements: List[Dict]) -> Dict[str, Any]:
        """모든 기업에 대한 신규 공고 추천을 생성합니다."""
        logger.info(f"신규 공고 추천 생성 시작 (전체 {len(self.alpha_companies)}개 기업)...")
        
        all_recommendations = {}
        
        for i in range(len(self.alpha_companies)):
            try:
                recommendations = self.generate_recommendations_for_company(i, new_announcements)
                if recommendations:
                    all_recommendations[f"company_{i+1}"] = recommendations
                    logger.info(f"✓ {i+1}번 기업 신규 공고 추천 완료")
                else:
                    logger.warning(f"✗ {i+1}번 기업 신규 공고 추천 실패")
                
                # API 호출 간격 조절
                if i < len(self.alpha_companies) - 1:
                    time.sleep(2)  # 2초 대기
                    
            except Exception as e:
                logger.error(f"✗ {i+1}번 기업 신규 공고 추천 중 오류: {e}")
        
        return all_recommendations
    
    def save_recommendations_to_supabase(self, recommendations: Dict[str, Any], timestamp: str) -> bool:
        """추천 결과를 Supabase에 저장합니다."""
        if not self.supabase or not recommendations:
            return False
        
        try:
            supabase_data = []
            
            for company_key, data in recommendations.items():
                company_info = data['company_info']
                recs = data['recommendations']
                
                for i, rec in enumerate(recs):
                    supabase_data.append({
                        'company_id': company_info['no'],
                        'company_name': company_info['business_description'],
                        'announcement_title': rec.get('공고이름', ''),
                        'recommendation_score': rec.get('추천점수', 0),
                        'recommendation_reason': rec.get('추천이유', ''),
                        'start_date': rec.get('모집일', ''),
                        'end_date': rec.get('마감일', ''),
                        'remaining_days': rec.get('남은기간', ''),
                        'amount_text': rec.get('투자금액', ''),
                        'amount_usage': rec.get('투자금액사용처', ''),
                        'status': rec.get('공고상태', ''),
                        'year': rec.get('공고연도', ''),
                        'month': rec.get('공고월', ''),
                        'rank': i + 1,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    })
            
            # Supabase에 저장
            result = self.supabase.table('recommendations').insert(supabase_data).execute()
            logger.info(f"Supabase에 {len(supabase_data)}개 추천 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"Supabase 추천 저장 실패: {e}")
            return False
    
    def save_recommendations_to_file(self, recommendations: Dict[str, Any], timestamp: str):
        """추천 결과를 파일로 저장합니다."""
        if not recommendations:
            logger.warning("저장할 추천 결과가 없습니다.")
            return
        
        # Excel 파일 저장
        excel_file = self.data_dir / f"신규공고_맞춤추천_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            for company_key, data in recommendations.items():
                company_info = data['company_info']
                recs = data['recommendations']
                
                # 추천 정보를 가로로 배치
                rec_data = {
                    '구분': ['추천점수', '공고이름', '추천이유', '모집일', '마감일', '남은기간/마감여부', '투자금액', '투자금액사용처', '공고상태', '공고연도', '공고월']
                }
                
                # 각 추천별로 열 추가
                for i, rec in enumerate(recs):
                    rec_data[f'추천 {i+1}'] = [
                        rec.get('추천점수', ''),
                        rec.get('공고이름', ''),
                        rec.get('추천이유', ''),
                        rec.get('모집일', ''),
                        rec.get('마감일', ''),
                        rec.get('남은기간', ''),
                        rec.get('투자금액', ''),
                        rec.get('투자금액사용처', ''),
                        rec.get('공고상태', ''),
                        rec.get('공고연도', ''),
                        rec.get('공고월', '')
                    ]
                
                # 추천 정보 DataFrame
                rec_df = pd.DataFrame(rec_data)
                
                # 시트 이름
                sheet_name = f"No.{company_info['no']} company"
                
                # 추천 정보 저장
                rec_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Excel 파일 저장 완료: {excel_file}")
        
        # CSV 파일 저장
        csv_file = self.data_dir / f"신규공고_맞춤추천_{timestamp}.csv"
        all_data = []
        for company_key, data in recommendations.items():
            company_info = data['company_info']
            recs = data['recommendations']
            
            for i, rec in enumerate(recs):
                row = {
                    '기업번호': company_info['no'],
                    '기업명': company_info['business_description'],
                    '추천순위': i + 1,
                    '추천점수': rec.get('추천점수', ''),
                    '공고이름': rec.get('공고이름', ''),
                    '추천이유': rec.get('추천이유', ''),
                    '모집일': rec.get('모집일', ''),
                    '마감일': rec.get('마감일', ''),
                    '남은기간/마감여부': rec.get('남은기간', ''),
                    '투자금액': rec.get('투자금액', ''),
                    '투자금액사용처': rec.get('투자금액사용처', ''),
                    '공고상태': rec.get('공고상태', ''),
                    '공고연도': rec.get('공고연도', ''),
                    '공고월': rec.get('공고월', ''),
                    '생성일시': data['generated_at']
                }
                all_data.append(row)
        
        df = pd.DataFrame(all_data)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f"CSV 파일 저장 완료: {csv_file}")
    
    def daily_job(self):
        """매일 실행되는 작업"""
        logger.info("=== 매일 신규 공고 수집 및 맞춤 추천 작업 시작 ===")
        
        try:
            # 1. 신규 공고 수집
            collection_result = self.collect_daily_announcements()
            
            # 2. 수집된 공고를 Supabase에 저장
            if collection_result['kstartup']:
                self.save_announcements_to_supabase(collection_result['kstartup'], 'kstartup')
            
            if collection_result['bizinfo']:
                self.save_announcements_to_supabase(collection_result['bizinfo'], 'bizinfo')
            
            # 3. 모든 신규 공고 통합
            all_new_announcements = collection_result['kstartup'] + collection_result['bizinfo']
            
            if not all_new_announcements:
                logger.info("오늘 새로운 공고가 없습니다.")
                return
            
            logger.info(f"총 {len(all_new_announcements)}개의 신규 공고를 수집했습니다.")
            
            # 4. 모든 기업에 대한 맞춤 추천 생성
            recommendations = self.generate_all_recommendations(all_new_announcements)
            
            if recommendations:
                # 5. 추천 결과를 Supabase에 저장
                self.save_recommendations_to_supabase(recommendations, collection_result['timestamp'])
                
                # 6. 추천 결과를 파일로 저장
                self.save_recommendations_to_file(recommendations, collection_result['timestamp'])
                
                logger.info(f"총 {len(recommendations)}개 기업에 대한 신규 공고 맞춤 추천이 완료되었습니다.")
            else:
                logger.warning("추천 생성에 실패했습니다.")
                
        except Exception as e:
            logger.error(f"매일 작업 중 오류 발생: {e}")
    
    def start_scheduler(self):
        """스케줄러를 시작합니다."""
        logger.info("매일 아침 9시 신규 공고 수집 및 맞춤 추천 스케줄러 시작")
        
        # 매일 오전 9시에 실행
        schedule.every().day.at("09:00").do(self.daily_job)
        
        # 즉시 한 번 실행 (테스트용)
        logger.info("테스트를 위해 즉시 실행합니다...")
        self.daily_job()
        
        # 스케줄러 실행
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
        except KeyboardInterrupt:
            logger.info("스케줄러를 종료합니다.")

def main():
    """메인 실행 함수"""
    print("=== 통합 자동화 시스템 ===")
    print("1. 즉시 실행 (테스트)")
    print("2. 스케줄러 시작 (매일 오전 9시)")
    print("3. 종료")
    
    system = IntegratedAutoSystem()
    
    while True:
        choice = input("\n선택하세요 (1-3): ").strip()
        
        if choice == '1':
            print("\n즉시 실행합니다...")
            system.daily_job()
            break
        elif choice == '2':
            print("\n스케줄러를 시작합니다...")
            system.start_scheduler()
            break
        elif choice == '3':
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 1-3 중에서 선택하세요.")

if __name__ == "__main__":
    main()
