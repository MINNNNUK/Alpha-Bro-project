#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
매일 자동으로 K-스타트업 공고 데이터를 수집하는 스크립트
2025년 9월 6일 기준으로 매일 실행
"""

import schedule
import time
import logging
from datetime import datetime
from kstartup_2025_collector import KStartup2025Collector

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_auto_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def daily_collection():
    """매일 실행되는 수집 함수"""
    try:
        logger.info("=== 매일 자동 수집 시작 ===")
        
        # 수집기 초기화
        SERVICE_KEY = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
        collector = KStartup2025Collector(SERVICE_KEY)
        
        # 매일 새로운 공고 수집
        result = collector.collect_daily_new_announcements(use_mock=True)
        
        if result:
            logger.info(f"✅ 매일 수집 완료: {result}")
        else:
            logger.info("ℹ️ 새로운 공고가 없습니다.")
            
    except Exception as e:
        logger.error(f"❌ 매일 수집 중 오류 발생: {str(e)}")

def weekly_collection():
    """매주 실행되는 수집 함수 (30일간 데이터)"""
    try:
        logger.info("=== 매주 30일간 데이터 수집 시작 ===")
        
        # 수집기 초기화
        SERVICE_KEY = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
        collector = KStartup2025Collector(SERVICE_KEY)
        
        # 30일간 데이터 수집
        result = collector.collect_recent_30days_data(use_mock=True)
        
        if result:
            logger.info(f"✅ 30일간 데이터 수집 완료: {result}")
        else:
            logger.error("❌ 30일간 데이터 수집 실패")
            
    except Exception as e:
        logger.error(f"❌ 30일간 데이터 수집 중 오류 발생: {str(e)}")

def monthly_collection():
    """매월 실행되는 수집 함수 (1년간 데이터)"""
    try:
        logger.info("=== 매월 1년간 데이터 수집 시작 ===")
        
        # 수집기 초기화
        SERVICE_KEY = 'lSEnfDS8d9B+TyiAlh+jhZN9EGyIGk7GuYHSzZJtziZvrvFeyLF7jQi7z7G/usfjAO//9T5ihYhUeFJywCalhQ=='
        collector = KStartup2025Collector(SERVICE_KEY)
        
        # 1년간 데이터 수집
        result = collector.collect_past_year_data(use_mock=True)
        
        if result:
            logger.info(f"✅ 1년간 데이터 수집 완료: {result}")
        else:
            logger.error("❌ 1년간 데이터 수집 실패")
            
    except Exception as e:
        logger.error(f"❌ 1년간 데이터 수집 중 오류 발생: {str(e)}")

def main():
    """메인 실행 함수"""
    print("=== K-스타트업 매일 자동 수집 시스템 ===")
    print("📅 수집 기준일: 2025년 9월 6일")
    print("🕘 매일 오전 9시: 새로운 공고 수집")
    print("🕘 매주 월요일 오전 9시: 30일간 데이터 수집")
    print("🕘 매월 1일 오전 9시: 1년간 데이터 수집")
    print("종료하려면 Ctrl+C를 누르세요.")
    
    # 스케줄 설정
    schedule.every().day.at("09:00").do(daily_collection)
    schedule.every().monday.at("09:00").do(weekly_collection)
    # 매월 1일은 수동으로 실행하거나 cron으로 설정
    # schedule.every().month.do(monthly_collection)
    
    # 즉시 한 번 실행 (테스트용)
    print("\n=== 즉시 테스트 실행 ===")
    daily_collection()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 스케줄 확인
    except KeyboardInterrupt:
        print("\n자동 수집 시스템을 종료합니다.")

if __name__ == "__main__":
    main()
