#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
신규 회사 추가 및 자동 추천 시스템
Supabase companies 테이블과 연동하여 신규 회사에 대한 맞춤 추천 생성
"""

import pandas as pd
import openai
import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import warnings
import sys
sys.path.append('/Users/minkim/git_test/kpmg-2025/data2/supabase1')
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client, Client

warnings.filterwarnings('ignore')

class NewCompanyRecommendationSystem:
    def __init__(self):
        # OpenAI API 설정
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not self.openai_api_key:
            print("⚠️ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            self.openai_client = None
        else:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Supabase 클라이언트 초기화
        try:
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✅ Supabase 연결 성공")
        except Exception as e:
            print(f"❌ Supabase 연결 실패: {e}")
            self.supabase = None
        
        # 데이터 경로 설정
        self.data_path = "/Users/minkim/git_test/kpmg-2025/data2"
        self.kstartup_data_path = f"{self.data_path}/collected_data"
        self.bizinfo_data_path = f"{self.data_path}/collected_data_biz"
        
        # 데이터 로드
        self.load_all_data()
    
    def load_all_data(self):
        """모든 공고 데이터를 로드합니다."""
        print("📊 공고 데이터 로딩 중...")
        
        # Supabase에서 공고 데이터 로드
        if self.supabase:
            try:
                announcements_result = self.supabase.table('announcements').select('*').execute()
                self.announcements = pd.DataFrame(announcements_result.data)
                print(f"✅ Supabase 공고 데이터 로드: {len(self.announcements)}개")
            except Exception as e:
                print(f"❌ Supabase 공고 데이터 로드 실패: {e}")
                self.announcements = pd.DataFrame()
        else:
            self.announcements = pd.DataFrame()
        
        # 2025, 2024 지원사업 데이터 로드 (CSV 파일에서)
        self.load_apply_data()
    
    def load_apply_data(self):
        """2025, 2024 지원사업 데이터를 로드합니다."""
        try:
            # 2025 지원사업 데이터
            apply_2025_path = f"{self.data_path}/2025_total_apply.csv"
            if os.path.exists(apply_2025_path):
                self.apply_2025 = pd.read_csv(apply_2025_path)
                print(f"✅ 2025 지원사업 데이터 로드: {len(self.apply_2025)}개")
            else:
                self.apply_2025 = pd.DataFrame()
                print("⚠️ 2025 지원사업 데이터 파일이 없습니다.")
            
            # 2024 지원사업 데이터
            apply_2024_path = f"{self.data_path}/2024_total_apply.csv"
            if os.path.exists(apply_2024_path):
                self.apply_2024 = pd.read_csv(apply_2024_path)
                print(f"✅ 2024 지원사업 데이터 로드: {len(self.apply_2024)}개")
            else:
                self.apply_2024 = pd.DataFrame()
                print("⚠️ 2024 지원사업 데이터 파일이 없습니다.")
                
        except Exception as e:
            print(f"❌ 지원사업 데이터 로드 실패: {e}")
            self.apply_2025 = pd.DataFrame()
            self.apply_2024 = pd.DataFrame()
    
    def get_company_info(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Supabase에서 회사 정보를 가져옵니다."""
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table('companies').select('*').eq('id', company_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"❌ 회사 정보 조회 실패: {e}")
            return None
    
    def create_recommendation_prompt(self, company_info: Dict[str, Any]) -> str:
        """회사 정보를 바탕으로 추천 프롬프트를 생성합니다."""
        
        # 공고 데이터 정리
        announcements_text = "=== 현재 지원 가능한 공고 목록 ===\n"
        if not self.announcements.empty:
            for i, ann in enumerate(self.announcements.head(50).to_dict('records'), 1):
                title = ann.get('title', 'N/A')
                agency = ann.get('agency', 'N/A')
                amount = ann.get('amount_text', 'N/A')
                due_date = ann.get('due_date', 'N/A')
                announcements_text += f"{i}. {title}\n"
                announcements_text += f"   - 기관: {agency}\n"
                announcements_text += f"   - 지원금액: {amount}\n"
                announcements_text += f"   - 마감일: {due_date}\n\n"
        
        # 2025, 2024 지원사업 데이터 정리
        apply_data_text = ""
        if not self.apply_2025.empty:
            apply_data_text += "\n=== 2025년 지원사업 데이터 ===\n"
            for i, apply in enumerate(self.apply_2025.head(20).to_dict('records'), 1):
                title = apply.get('사업명', 'N/A')
                agency = apply.get('주관기관', 'N/A')
                amount = apply.get('지원금액', 'N/A')
                apply_data_text += f"{i}. {title} ({agency}) - {amount}\n"
        
        if not self.apply_2024.empty:
            apply_data_text += "\n=== 2024년 지원사업 데이터 ===\n"
            for i, apply in enumerate(self.apply_2024.head(20).to_dict('records'), 1):
                title = apply.get('사업명', 'N/A')
                agency = apply.get('주관기관', 'N/A')
                amount = apply.get('지원금액', 'N/A')
                apply_data_text += f"{i}. {title} ({agency}) - {amount}\n"
        
        prompt = f"""
{announcements_text}
{apply_data_text}

다음은 추천을 받을 신규 기업의 정보입니다:

기업 정보:
- 기업명: {company_info.get('name', 'N/A')}
- 사업자 유형: {company_info.get('business_type', 'N/A')}
- 지역: {company_info.get('region', 'N/A')}
- 업력: {company_info.get('years', 0)}년
- 성장단계: {company_info.get('stage', 'N/A')}
- 업종: {company_info.get('industry', 'N/A')}
- 키워드: {', '.join(company_info.get('keywords', []))}
- 선호 지원용도: {', '.join(company_info.get('preferred_uses', []))}
- 선호 예산규모: {company_info.get('preferred_budget', 'N/A')}

위 공고들 중에서 이 기업에 가장 적합한 공고들을 추천해주세요.
중요: 
1. 추천 개수에 제한이 없습니다. 가능한 한 많은 공고를 추천해주세요.
2. 오직 기업의 특성과 공고의 내용이 얼마나 잘 맞는지만 고려해주세요.
3. 현재 지원 가능한 공고와 과거 지원사업 데이터를 모두 고려해주세요.

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
    
    def call_openai_api(self, prompt: str) -> Optional[str]:
        """OpenAI API를 호출하여 추천을 받습니다."""
        if not self.openai_client:
            print("⚠️ OpenAI API 키가 설정되지 않았습니다.")
            return None
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "당신은 정부 지원사업 추천 전문가입니다. 기업의 특성과 요구사항을 분석하여 가장 적합한 지원사업을 추천해주세요. 추천 개수에 제한이 없으므로 가능한 한 많은 공고를 추천해주세요. 반드시 JSON 형식으로 응답해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ OpenAI API 호출 실패: {e}")
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
            print(f"❌ 추천 파싱 실패: {e}")
            return []
    
    def generate_recommendations_for_company(self, company_id: int) -> Optional[Dict[str, Any]]:
        """특정 회사에 대한 추천을 생성합니다."""
        company_info = self.get_company_info(company_id)
        if not company_info:
            print(f"❌ 회사 ID {company_id} 정보를 찾을 수 없습니다.")
            return None
        
        print(f"🤖 {company_info['name']} 기업에 대한 추천 생성 중...")
        
        # 프롬프트 생성
        prompt = self.create_recommendation_prompt(company_info)
        
        # LLM 호출
        response = self.call_openai_api(prompt)
        if not response:
            print("❌ LLM 호출 실패")
            return None
        
        recommendations = self.parse_recommendations(response)
        
        if not recommendations:
            print("❌ 추천 파싱 실패")
            return None
        
        print(f"✅ {len(recommendations)}개 추천 생성 완료")
        
        return {
            'company_info': company_info,
            'recommendations': recommendations,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def save_recommendations_to_supabase(self, company_id: int, recommendations_data: Dict[str, Any]) -> bool:
        """추천 결과를 Supabase에 저장합니다."""
        if not self.supabase or not recommendations_data:
            return False
        
        try:
            company_info = recommendations_data['company_info']
            recs = recommendations_data['recommendations']
            
            # recommendations2 테이블에 저장 (전체 추천)
            recommendations2_data = []
            for i, rec in enumerate(recs):
                recommendations2_data.append({
                    '기업번호': company_id,
                    '기업명': company_info['name'],
                    '추천순위': i + 1,
                    '추천점수': rec.get('추천점수', 0),
                    '공고이름': rec.get('공고이름', ''),
                    '추천이유': rec.get('추천이유', ''),
                    '모집일': rec.get('모집일', ''),
                    '마감일': rec.get('마감일', ''),
                    '남은기간/마감여부': rec.get('남은기간', ''),
                    '투자금액': rec.get('투자금액', ''),
                    '투자금액사용처': rec.get('투자금액사용처', ''),
                    '공고상태': rec.get('공고상태', ''),
                    '공고연도': rec.get('공고연도', '2025'),
                    '공고월': rec.get('공고월', '9'),
                    '생성일시': recommendations_data['generated_at']
                })
            
            # Supabase에 저장
            result2 = self.supabase.table('recommendations2').insert(recommendations2_data).execute()
            print(f"✅ recommendations2에 {len(recommendations2_data)}개 추천 저장 완료")
            
            # recommendations3_active 테이블에 저장 (활성 공고만)
            active_recommendations = [rec for rec in recs if rec.get('공고상태', '').find('현재 지원 가능') != -1]
            recommendations3_data = []
            for i, rec in enumerate(active_recommendations):
                recommendations3_data.append({
                    '기업번호': company_id,
                    '기업명': company_info['name'],
                    '추천순위': i + 1,
                    '추천점수': rec.get('추천점수', 0),
                    '공고이름': rec.get('공고이름', ''),
                    '추천이유': rec.get('추천이유', ''),
                    '모집일': rec.get('모집일', ''),
                    '마감일': rec.get('마감일', ''),
                    '남은기간/마감여부': rec.get('남은기간', ''),
                    '투자금액': rec.get('투자금액', ''),
                    '투자금액사용처': rec.get('투자금액사용처', ''),
                    '공고상태': rec.get('공고상태', ''),
                    '공고연도': rec.get('공고연도', '2025'),
                    '공고월': rec.get('공고월', '9'),
                    '생성일시': recommendations_data['generated_at']
                })
            
            if recommendations3_data:
                result3 = self.supabase.table('recommendations3_active').insert(recommendations3_data).execute()
                print(f"✅ recommendations3_active에 {len(recommendations3_data)}개 활성 추천 저장 완료")
            
            return True
            
        except Exception as e:
            print(f"❌ Supabase 저장 실패: {e}")
            return False
    
    def process_new_company(self, company_id: int) -> bool:
        """신규 회사에 대한 전체 추천 프로세스를 실행합니다."""
        print(f"\n🚀 신규 회사 ID {company_id} 추천 프로세스 시작")
        
        # 1. 추천 생성
        recommendations_data = self.generate_recommendations_for_company(company_id)
        if not recommendations_data:
            print("❌ 추천 생성 실패")
            return False
        
        # 2. Supabase에 저장
        success = self.save_recommendations_to_supabase(company_id, recommendations_data)
        if success:
            print(f"✅ 신규 회사 ID {company_id} 추천 프로세스 완료")
            return True
        else:
            print(f"❌ 신규 회사 ID {company_id} 추천 프로세스 실패")
            return False
    
    def get_new_companies(self) -> List[Dict[str, Any]]:
        """추천이 없는 신규 회사 목록을 반환합니다."""
        if not self.supabase:
            return []
        
        try:
            # companies 테이블에서 모든 회사 조회
            companies_result = self.supabase.table('companies').select('*').execute()
            companies = companies_result.data
            
            # recommendations2에서 이미 추천이 있는 회사들 조회
            recommendations_result = self.supabase.table('recommendations2').select('기업번호').execute()
            existing_company_ids = set(rec['기업번호'] for rec in recommendations_result.data)
            
            # 추천이 없는 신규 회사들 필터링
            new_companies = [company for company in companies if company['id'] not in existing_company_ids]
            
            return new_companies
            
        except Exception as e:
            print(f"❌ 신규 회사 조회 실패: {e}")
            return []
    
    def process_all_new_companies(self) -> Dict[str, Any]:
        """모든 신규 회사에 대한 추천을 생성합니다."""
        print("\n🎯 모든 신규 회사 추천 프로세스 시작")
        
        new_companies = self.get_new_companies()
        if not new_companies:
            print("✅ 처리할 신규 회사가 없습니다.")
            return {"success": True, "processed": 0}
        
        print(f"📋 {len(new_companies)}개의 신규 회사 발견")
        
        results = {
            "success": True,
            "processed": 0,
            "failed": 0,
            "details": []
        }
        
        for company in new_companies:
            company_id = company['id']
            company_name = company['name']
            
            print(f"\n📝 처리 중: {company_name} (ID: {company_id})")
            
            success = self.process_new_company(company_id)
            
            if success:
                results["processed"] += 1
                results["details"].append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "status": "success"
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "status": "failed"
                })
        
        print(f"\n📊 처리 결과: 성공 {results['processed']}개, 실패 {results['failed']}개")
        return results

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='신규 회사 추천 시스템')
    parser.add_argument('--company-id', type=int, help='특정 회사 ID에 대한 추천 생성')
    parser.add_argument('--all', action='store_true', help='모든 신규 회사에 대한 추천 생성')
    parser.add_argument('--list', action='store_true', help='신규 회사 목록 확인')
    
    args = parser.parse_args()
    
    print("=== 신규 회사 추천 시스템 ===")
    
    system = NewCompanyRecommendationSystem()
    
    if args.company_id:
        # 특정 회사 추천 생성
        print(f"회사 ID {args.company_id}에 대한 추천 생성 중...")
        success = system.process_new_company(args.company_id)
        if success:
            print("✅ 추천 생성 완료")
        else:
            print("❌ 추천 생성 실패")
            sys.exit(1)
    
    elif args.all:
        # 모든 신규 회사 추천 생성
        print("모든 신규 회사에 대한 추천 생성 중...")
        results = system.process_all_new_companies()
        print(f"처리 결과: {results}")
        if results['failed'] > 0:
            sys.exit(1)
    
    elif args.list:
        # 신규 회사 목록 확인
        new_companies = system.get_new_companies()
        print(f"신규 회사 목록 ({len(new_companies)}개):")
        for company in new_companies:
            print(f"  ID: {company['id']}, 이름: {company['name']}")
    
    else:
        # 대화형 모드
        print("\n1. 특정 회사 추천 생성")
        print("2. 모든 신규 회사 추천 생성")
        print("3. 신규 회사 목록 확인")
        print("4. 종료")
        
        while True:
            choice = input("\n선택하세요 (1-4): ").strip()
            
            if choice == '1':
                company_id = input("회사 ID를 입력하세요: ").strip()
                try:
                    company_id = int(company_id)
                    system.process_new_company(company_id)
                except ValueError:
                    print("올바른 회사 ID를 입력하세요.")
            
            elif choice == '2':
                results = system.process_all_new_companies()
                print(f"\n처리 결과: {results}")
            
            elif choice == '3':
                new_companies = system.get_new_companies()
                print(f"\n신규 회사 목록 ({len(new_companies)}개):")
                for company in new_companies:
                    print(f"  ID: {company['id']}, 이름: {company['name']}")
            
            elif choice == '4':
                print("프로그램을 종료합니다.")
                break
            
            else:
                print("잘못된 선택입니다. 1-4 중에서 선택하세요.")

if __name__ == "__main__":
    main()
