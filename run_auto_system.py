#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동화 시스템 실행 스크립트
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """메인 실행 함수"""
    print("=== 정부지원사업 자동화 시스템 ===")
    print("1. Streamlit 앱 실행 (웹 인터페이스)")
    print("2. 통합 자동화 시스템 실행 (콘솔)")
    print("3. 데이터 수집만 실행")
    print("4. 추천 생성만 실행")
    print("5. 종료")
    
    while True:
        choice = input("\n선택하세요 (1-5): ").strip()
        
        if choice == '1':
            print("\nStreamlit 앱을 실행합니다...")
            try:
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run", 
                    "auto_streamlit_app.py",
                    "--server.port", "8501",
                    "--server.address", "localhost"
                ])
            except KeyboardInterrupt:
                print("\nStreamlit 앱을 종료합니다.")
            break
            
        elif choice == '2':
            print("\n통합 자동화 시스템을 실행합니다...")
            try:
                from integrated_auto_system import IntegratedAutoSystem
                system = IntegratedAutoSystem()
                system.start_scheduler()
            except KeyboardInterrupt:
                print("\n자동화 시스템을 종료합니다.")
            break
            
        elif choice == '3':
            print("\n데이터 수집을 실행합니다...")
            try:
                from integrated_auto_system import IntegratedAutoSystem
                system = IntegratedAutoSystem()
                collection_result = system.collect_daily_announcements()
                
                if collection_result['kstartup'] or collection_result['bizinfo']:
                    # Supabase에 저장
                    if collection_result['kstartup']:
                        system.save_announcements_to_supabase(collection_result['kstartup'], 'kstartup')
                    if collection_result['bizinfo']:
                        system.save_announcements_to_supabase(collection_result['bizinfo'], 'bizinfo')
                    
                    print(f"✅ 데이터 수집 완료!")
                    print(f"K-스타트업: {len(collection_result['kstartup'])}개")
                    print(f"기업마당: {len(collection_result['bizinfo'])}개")
                else:
                    print("새로운 공고가 없습니다.")
            except Exception as e:
                print(f"데이터 수집 실패: {e}")
            break
            
        elif choice == '4':
            print("\n추천 생성을 실행합니다...")
            try:
                from integrated_auto_system import IntegratedAutoSystem
                system = IntegratedAutoSystem()
                collection_result = system.collect_daily_announcements()
                all_announcements = collection_result['kstartup'] + collection_result['bizinfo']
                
                if all_announcements:
                    recommendations = system.generate_all_recommendations(all_announcements)
                    if recommendations:
                        system.save_recommendations_to_supabase(recommendations, collection_result['timestamp'])
                        system.save_recommendations_to_file(recommendations, collection_result['timestamp'])
                        print(f"✅ 추천 생성 완료! {len(recommendations)}개 기업")
                    else:
                        print("추천 생성에 실패했습니다.")
                else:
                    print("추천할 공고가 없습니다.")
            except Exception as e:
                print(f"추천 생성 실패: {e}")
            break
            
        elif choice == '5':
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다. 1-5 중에서 선택하세요.")

if __name__ == "__main__":
    main()

