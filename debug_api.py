#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 디버깅 스크립트
"""

import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def debug_api():
    """API 응답 디버깅"""
    
    # API 설정
    api_url = 'https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01'
    service_key = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
    
    # 테스트 날짜 (최근 7일)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    params = {
        'serviceKey': service_key,
        'startDate': start_date_str,
        'endDate': end_date_str,
        'pageNo': 1,
        'numOfRows': 5,
        'resultType': 'xml'
    }
    
    # URL 구성
    param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    url = f"{api_url}?{param_string}"
    
    print(f"=== API 디버깅 ===")
    print(f"URL: {url}")
    print()
    
    try:
        # curl 명령어 실행
        cmd = ['curl', '-k', '-s', url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print(f"curl 실행 결과:")
        print(f"returncode: {result.returncode}")
        print(f"stdout 길이: {len(result.stdout)}")
        print(f"stderr: {result.stderr}")
        print()
        
        if result.returncode == 0:
            print("=== XML 응답 (처음 1000자) ===")
            print(result.stdout[:1000])
            print("...")
            print()
            
            # XML 파싱 시도
            try:
                root = ET.fromstring(result.stdout)
                print("=== XML 파싱 성공 ===")
                print(f"루트 태그: {root.tag}")
                print(f"자식 요소들: {[child.tag for child in root]}")
                print()
                
                # 각 요소별 내용 확인
                for child in root:
                    print(f"=== {child.tag} ===")
                    if child.text:
                        print(f"텍스트: {child.text}")
                    else:
                        print(f"자식 요소들: {[subchild.tag for subchild in child]}")
                        
                        # data 요소의 경우 아이템 확인
                        if child.tag == 'data':
                            items = child.findall('item')
                            print(f"아이템 수: {len(items)}")
                            if items:
                                print("첫 번째 아이템:")
                                first_item = items[0]
                                for col in first_item.findall('col'):
                                    name = col.get('name')
                                    value = col.text if col.text else ''
                                    print(f"  {name}: {value}")
                    print()
                    
            except ET.ParseError as e:
                print(f"XML 파싱 오류: {str(e)}")
                
        else:
            print("curl 실행 실패")
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    debug_api()
