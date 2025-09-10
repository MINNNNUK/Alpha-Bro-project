#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-스타트업 웹사이트 구조 디버깅
"""

import requests
from bs4 import BeautifulSoup
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def debug_website():
    """웹사이트 구조 디버깅"""
    
    base_url = 'https://www.k-startup.go.kr'
    search_url = 'https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do'
    
    # 세션 생성
    session = requests.Session()
    session.verify = False
    
    # 헤더 설정
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    try:
        print("=== K-스타트업 웹사이트 구조 분석 ===")
        print(f"URL: {search_url}")
        print()
        
        # 검색 파라미터
        params = {
            'schM': 'list',
            'page': 1,
            'perPage': 20,
            'sort': 'rcptEndDt',
            'order': 'asc'
        }
        
        response = session.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        print()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("=== HTML 구조 분석 ===")
        print(f"페이지 제목: {soup.title.string if soup.title else '없음'}")
        print()
        
        # 모든 테이블 찾기
        tables = soup.find_all('table')
        print(f"테이블 개수: {len(tables)}")
        
        for i, table in enumerate(tables):
            print(f"\n=== 테이블 {i+1} ===")
            print(f"클래스: {table.get('class', [])}")
            print(f"ID: {table.get('id', '없음')}")
            
            # 테이블 내용 일부 출력
            table_text = table.get_text(strip=True)[:200]
            print(f"내용 (처음 200자): {table_text}...")
        
        print("\n=== div 요소들 ===")
        divs = soup.find_all('div', class_=True)
        print(f"클래스가 있는 div 개수: {len(divs)}")
        
        for div in divs[:10]:  # 처음 10개만
            print(f"div 클래스: {div.get('class')}")
        
        print("\n=== 스크립트 태그 확인 ===")
        scripts = soup.find_all('script')
        print(f"스크립트 개수: {len(scripts)}")
        
        # AJAX 요청이 있는지 확인
        for script in scripts:
            if script.string and 'ajax' in script.string.lower():
                print("AJAX 요청이 감지되었습니다.")
                break
        
        print("\n=== 폼 요소 확인 ===")
        forms = soup.find_all('form')
        print(f"폼 개수: {len(forms)}")
        
        for form in forms:
            print(f"폼 액션: {form.get('action', '없음')}")
            print(f"폼 메소드: {form.get('method', '없음')}")
        
        # 페이지 소스 일부 저장
        with open('kstartup_page_source.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\n페이지 소스가 'kstartup_page_source.html'에 저장되었습니다.")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    debug_website()
