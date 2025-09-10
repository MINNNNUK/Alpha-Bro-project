#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 API 테스트 스크립트
"""

import requests
import json
from datetime import datetime, timedelta
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def simple_api_test():
    """간단한 API 테스트"""
    
    # API 설정
    api_url = 'https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01'
    service_key = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
    
    # 테스트 날짜 (최근 30일)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f"=== 간단한 API 테스트 ===")
    print(f"테스트 기간: {start_date_str} ~ {end_date_str}")
    print()
    
    # API 요청 파라미터
    params = {
        'serviceKey': service_key,
        'startDate': start_date_str,
        'endDate': end_date_str,
        'pageNo': 1,
        'numOfRows': 5,  # 테스트용으로 5개만
        'resultType': 'json'
    }
    
    # 세션 생성 및 SSL 설정
    session = requests.Session()
    session.verify = False
    
    try:
        print("API 요청 중...")
        response = session.get(api_url, params=params, timeout=30)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            print("✅ API 호출 성공!")
            
            # 응답 텍스트 확인
            print("=== 응답 텍스트 (처음 500자) ===")
            print(response.text[:500])
            print()
            
            try:
                # JSON 파싱 시도
                data = response.json()
                print("=== JSON 파싱 성공 ===")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
                print("...")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 실패: {str(e)}")
                print("응답이 JSON 형식이 아닐 수 있습니다.")
                
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"응답 내용: {response.text}")
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL 오류: {str(e)}")
        print("SSL 인증서 문제가 있습니다.")
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 연결 오류: {str(e)}")
        print("네트워크 연결을 확인하세요.")
        
    except requests.exceptions.Timeout as e:
        print(f"❌ 타임아웃 오류: {str(e)}")
        print("요청 시간이 초과되었습니다.")
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    simple_api_test()
