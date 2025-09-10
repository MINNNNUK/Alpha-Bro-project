#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-스타트업 API 테스트 스크립트
"""

import requests
import json
from datetime import datetime, timedelta
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_kstartup_api():
    """K-스타트업 API 테스트"""
    
    # API 설정
    api_url = 'https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01'
    service_key = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
    
    # 테스트 날짜 (최근 7일)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f"=== K-스타트업 API 테스트 ===")
    print(f"테스트 기간: {start_date_str} ~ {end_date_str}")
    print(f"API URL: {api_url}")
    print()
    
    # API 요청 파라미터
    params = {
        'serviceKey': service_key,
        'startDate': start_date_str,
        'endDate': end_date_str,
        'pageNo': 1,
        'numOfRows': 10,  # 테스트용으로 10개만
        'resultType': 'json'
    }
    
    try:
        print("API 요청 중...")
        response = requests.get(api_url, params=params, timeout=30, verify=False)
        response.raise_for_status()
        
        print(f"응답 상태 코드: {response.status_code}")
        print()
        
        # JSON 응답 파싱
        data = response.json()
        
        print("=== API 응답 구조 ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
        
        # 응답 분석
        if 'response' in data:
            response_data = data['response']
            
            if 'header' in response_data:
                header = response_data['header']
                result_code = header.get('resultCode', '')
                result_msg = header.get('resultMsg', '')
                
                print(f"=== 응답 헤더 ===")
                print(f"결과 코드: {result_code}")
                print(f"결과 메시지: {result_msg}")
                print()
                
                if result_code == '00':
                    print("✅ API 호출 성공!")
                    
                    if 'body' in response_data:
                        body = response_data['body']
                        total_count = body.get('totalCount', 0)
                        items = body.get('items', [])
                        
                        print(f"=== 데이터 정보 ===")
                        print(f"총 공고 수: {total_count}")
                        print(f"현재 페이지 아이템 수: {len(items)}")
                        print()
                        
                        if items:
                            print("=== 첫 번째 공고 데이터 예시 ===")
                            first_item = items[0]
                            for key, value in first_item.items():
                                print(f"{key}: {value}")
                            print()
                            
                            # 데이터프레임으로 변환하여 표시
                            import pandas as pd
                            df = pd.DataFrame(items)
                            print("=== 데이터프레임 형태 ===")
                            print(df.head())
                            print()
                            print("=== 컬럼 정보 ===")
                            print(df.columns.tolist())
                            
                        else:
                            print("⚠️ 해당 기간에 공고가 없습니다.")
                    else:
                        print("⚠️ 응답에 body가 없습니다.")
                else:
                    print(f"❌ API 오류: {result_msg}")
            else:
                print("⚠️ 응답에 header가 없습니다.")
        else:
            print("⚠️ 응답 구조가 예상과 다릅니다.")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {str(e)}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    test_kstartup_api()
