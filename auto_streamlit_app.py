import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import altair as alt
from supabase import create_client, Client
import json
import subprocess
import threading
import time
from pathlib import Path
import logging

# 통합 자동화 시스템 import
from integrated_auto_system import IntegratedAutoSystem
import sys
sys.path.append('/Users/minkim/git_test/kpmg-2025/data2/supabase1')
from config import SUPABASE_URL, SUPABASE_KEY

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase 설정
@st.cache_resource
def init_supabase():
    """Supabase 클라이언트 초기화"""
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Supabase 연결 실패: {e}")
        st.stop()

supabase: Client = init_supabase()

@st.cache_data(ttl=60)
def load_companies() -> pd.DataFrame:
    """회사 데이터 로드 (alpha_companies 테이블 사용)"""
    try:
        result = supabase.table('alpha_companies').select('*').execute()
        df = pd.DataFrame(result.data)
        
        # 컬럼명을 기존 companies 테이블과 호환되도록 매핑
        if not df.empty:
            # 기본 컬럼 매핑
            df = df.rename(columns={
                'No.': 'id',
                '사업아이템 한 줄 소개': 'name',
                '기업형태': 'business_type',
                '소재지': 'region',
                '주업종 (사업자등록증 상)': 'industry',
                '특화분야': 'keywords'
            })
            
            # 추가 컬럼들을 별도로 추가
            df['설립일'] = df.get('설립연월일', '')
            df['매출'] = df.get('#매출', '')
            df['고용'] = df.get('#고용', '')
            df['특허'] = df.get('#기술특허(등록)', '')
            df['인증'] = df.get('#기업인증', '')
            df['주요산업'] = df.get('주요 산업', '')
            
            # years 컬럼 추가 (기본값)
            df['years'] = 0
                
            # stage 컬럼 추가 (기본값)
            df['stage'] = '예비'
            
            # preferred_uses, preferred_budget 컬럼 추가 (기본값)
            df['preferred_uses'] = ''
            df['preferred_budget'] = '소액'
        
        return df
    except Exception as e:
        st.error(f"회사 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_announcements() -> pd.DataFrame:
    """공고 데이터 로드"""
    try:
        result = supabase.table('announcements').select('*').execute()
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"공고 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_recommendations(company_id: int = None) -> pd.DataFrame:
    """추천 데이터 로드"""
    try:
        query = supabase.table('recommendations').select('*')
        if company_id:
            query = query.eq('company_id', company_id)
        result = query.execute()
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"추천 데이터 로드 실패: {e}")
        return pd.DataFrame()

def calculate_dday(due_date: str) -> Optional[int]:
    """D-Day 계산"""
    if pd.isna(due_date) or due_date == '':
        return None
    
    try:
        due = datetime.strptime(due_date, '%Y-%m-%d').date()
        today = date.today()
        return (due - today).days
    except:
        return None

def format_recommendation_reason(reason: str, score: float) -> str:
    """추천 사유 포맷팅"""
    if pd.isna(reason) or reason == '' or reason is None or str(reason).strip() == '':
        # 기본 추천 사유 생성
        if score >= 80:
            return "높은 적합도 - 키워드 매칭 및 조건 충족"
        elif score >= 60:
            return "적합도 양호 - 주요 조건 충족"
        elif score >= 40:
            return "보통 적합도 - 일부 조건 충족"
        else:
            return "낮은 적합도 - 참고용"
    return str(reason).strip()

def render_sidebar():
    """사이드바 렌더링"""
    st.sidebar.title("🏢 회사 관리")
    
    # 기존 고객사 목록 (alpha_companies 테이블 사용)
    st.sidebar.subheader("기존 고객사")
    companies_df = load_companies()
    
    if not companies_df.empty:
        # 검색 기능
        search_term = st.sidebar.text_input("🔍 회사 검색", key="existing_search")
        if search_term:
            filtered_companies = companies_df[
                companies_df['name'].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_companies = companies_df
        
        # 회사 선택 (사업아이템으로 표시)
        company_names = filtered_companies['name'].tolist()
        if company_names:
            selected_company = st.sidebar.selectbox(
                "회사 선택",
                company_names,
                key="existing_company_select"
            )
            if selected_company:
                selected_company_data = filtered_companies[filtered_companies['name'] == selected_company].iloc[0]
                st.session_state['selected_company'] = selected_company_data.to_dict()
        else:
            st.sidebar.info("검색 결과가 없습니다.")
    else:
        st.sidebar.info("기존 고객사 데이터가 없습니다.")
    
    st.sidebar.divider()
    
    # 자동화 시스템 제어
    st.sidebar.subheader("🤖 자동화 시스템")
    
    if st.sidebar.button("🔄 수동 데이터 수집", type="primary"):
        with st.spinner("데이터 수집 중..."):
            try:
                system = IntegratedAutoSystem()
                collection_result = system.collect_daily_announcements()
                
                if collection_result['kstartup'] or collection_result['bizinfo']:
                    # Supabase에 저장
                    if collection_result['kstartup']:
                        system.save_announcements_to_supabase(collection_result['kstartup'], 'kstartup')
                    if collection_result['bizinfo']:
                        system.save_announcements_to_supabase(collection_result['bizinfo'], 'bizinfo')
                    
                    st.success(f"✅ 데이터 수집 완료! K-스타트업: {len(collection_result['kstartup'])}개, 기업마당: {len(collection_result['bizinfo'])}개")
                    st.rerun()
                else:
                    st.info("새로운 공고가 없습니다.")
            except Exception as e:
                st.error(f"데이터 수집 실패: {e}")
    
    if st.sidebar.button("🎯 수동 추천 생성"):
        with st.spinner("추천 생성 중..."):
            try:
                system = IntegratedAutoSystem()
                collection_result = system.collect_daily_announcements()
                all_announcements = collection_result['kstartup'] + collection_result['bizinfo']
                
                if all_announcements:
                    recommendations = system.generate_all_recommendations(all_announcements)
                    if recommendations:
                        system.save_recommendations_to_supabase(recommendations, collection_result['timestamp'])
                        system.save_recommendations_to_file(recommendations, collection_result['timestamp'])
                        st.success(f"✅ 추천 생성 완료! {len(recommendations)}개 기업")
                        st.rerun()
                    else:
                        st.warning("추천 생성에 실패했습니다.")
                else:
                    st.info("추천할 공고가 없습니다.")
            except Exception as e:
                st.error(f"추천 생성 실패: {e}")
    
    if st.sidebar.button("🚀 전체 자동화 실행"):
        with st.spinner("전체 자동화 실행 중..."):
            try:
                system = IntegratedAutoSystem()
                system.daily_job()
                st.success("✅ 전체 자동화 실행 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"자동화 실행 실패: {e}")

def render_dashboard_tab():
    """대시보드 탭 렌더링"""
    st.subheader("📊 시스템 대시보드")
    
    # 통계 정보
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        companies_df = load_companies()
        st.metric("등록된 기업", len(companies_df))
    
    with col2:
        announcements_df = load_announcements()
        st.metric("수집된 공고", len(announcements_df))
    
    with col3:
        recommendations_df = load_recommendations()
        st.metric("생성된 추천", len(recommendations_df))
    
    with col4:
        # 최근 수집된 공고 수
        recent_announcements = announcements_df[
            pd.to_datetime(announcements_df['created_at']).dt.date == date.today()
        ] if not announcements_df.empty else pd.DataFrame()
        st.metric("오늘 수집", len(recent_announcements))
    
    st.divider()
    
    # 최근 공고 목록
    st.subheader("📋 최근 수집된 공고")
    if not announcements_df.empty:
        # created_at 컬럼을 datetime으로 변환
        announcements_df['created_at'] = pd.to_datetime(announcements_df['created_at'], errors='coerce')
        recent_announcements = announcements_df.nlargest(10, 'created_at')
        display_columns = ['title', 'agency', 'start_date', 'end_date', 'amount_text', 'source', 'created_at']
        available_columns = [col for col in display_columns if col in recent_announcements.columns]
        
        st.dataframe(
            recent_announcements[available_columns],
            width='stretch',
            column_config={
                "title": st.column_config.TextColumn("공고명", width="large"),
                "agency": st.column_config.TextColumn("주관기관", width="medium"),
                "start_date": st.column_config.DateColumn("모집시작", width="small"),
                "end_date": st.column_config.DateColumn("모집종료", width="small"),
                "amount_text": st.column_config.TextColumn("지원금액", width="medium"),
                "source": st.column_config.TextColumn("출처", width="small"),
                "created_at": st.column_config.DatetimeColumn("수집일시", width="small")
            }
        )
    else:
        st.info("수집된 공고가 없습니다.")

def render_recommendations_tab():
    """맞춤 추천 탭 렌더링"""
    if 'selected_company' not in st.session_state:
        st.info("사이드바에서 회사를 선택해주세요.")
        return
    
    company = st.session_state['selected_company']
    st.subheader(f"📋 {company['name']} 맞춤 추천")
    
    # 탭 선택
    tab1, tab2 = st.tabs(["전체 추천", "활성 공고만"])
    
    with tab1:
        recommendations_df = load_recommendations(company['id'])
        if not recommendations_df.empty:
            # 컬럼 선택 및 정렬
            display_columns = ['rank', 'recommendation_score', 'announcement_title', 'recommendation_reason', 'start_date', 'end_date', 'remaining_days', 'amount_text', 'status']
            available_columns = [col for col in display_columns if col in recommendations_df.columns]
            
            # Arrow 직렬화 문제 방지를 위해 데이터 타입 정리
            display_df = recommendations_df[available_columns].copy()
            
            # 추천 사유 포맷팅
            if 'recommendation_reason' in display_df.columns and 'recommendation_score' in display_df.columns:
                display_df['recommendation_reason'] = display_df.apply(
                    lambda row: format_recommendation_reason(row['recommendation_reason'], row['recommendation_score']), 
                    axis=1
                )
            
            for col in display_df.columns:
                if display_df[col].dtype == 'object':
                    display_df[col] = display_df[col].astype(str)
            
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "recommendation_reason": st.column_config.TextColumn("추천 이유", width="large"),
                    "announcement_title": st.column_config.TextColumn("공고명", width="large"),
                    "amount_text": st.column_config.TextColumn("투자금액", width="medium"),
                    "end_date": st.column_config.DateColumn("마감일", width="small"),
                    "status": st.column_config.TextColumn("상태", width="small"),
                    "recommendation_score": st.column_config.NumberColumn("점수", format="%.1f", width="small"),
                    "rank": st.column_config.NumberColumn("순위", width="small")
                }
            )
        else:
            st.info("해당 회사의 추천 결과가 없습니다.")
    
    with tab2:
        # 활성 공고만 필터링 (마감되지 않은 공고)
        recommendations_df = load_recommendations(company['id'])
        if not recommendations_df.empty:
            # 오늘 날짜 기준으로 활성 공고 필터링
            today = date.today()
            active_recommendations = recommendations_df[
                (pd.to_datetime(recommendations_df['end_date'], errors='coerce').dt.date >= today) |
                (recommendations_df['end_date'].isna())
            ]
            
            if not active_recommendations.empty:
                display_columns = ['rank', 'recommendation_score', 'announcement_title', 'recommendation_reason', 'start_date', 'end_date', 'remaining_days', 'amount_text', 'status']
                available_columns = [col for col in display_columns if col in active_recommendations.columns]
                
                # Arrow 직렬화 문제 방지를 위해 데이터 타입 정리
                display_df = active_recommendations[available_columns].copy()
                
                # 추천 사유 포맷팅
                if 'recommendation_reason' in display_df.columns and 'recommendation_score' in display_df.columns:
                    display_df['recommendation_reason'] = display_df.apply(
                        lambda row: format_recommendation_reason(row['recommendation_reason'], row['recommendation_score']), 
                        axis=1
                    )
                
                for col in display_df.columns:
                    if display_df[col].dtype == 'object':
                        display_df[col] = display_df[col].astype(str)
                
                st.dataframe(
                    display_df,
                    width='stretch',
                    column_config={
                        "recommendation_reason": st.column_config.TextColumn("추천 이유", width="large"),
                        "announcement_title": st.column_config.TextColumn("공고명", width="large"),
                        "amount_text": st.column_config.TextColumn("투자금액", width="medium"),
                        "end_date": st.column_config.DateColumn("마감일", width="small"),
                        "status": st.column_config.TextColumn("상태", width="small"),
                        "recommendation_score": st.column_config.NumberColumn("점수", format="%.1f", width="small"),
                        "rank": st.column_config.NumberColumn("순위", width="small")
                    }
                )
            else:
                st.info("활성 추천 결과가 없습니다.")
        else:
            st.info("활성 추천 데이터가 없습니다.")

def render_announcements_tab():
    """공고 목록 탭 렌더링"""
    st.subheader("📋 수집된 공고 목록")
    
    announcements_df = load_announcements()
    
    if not announcements_df.empty:
        # created_at 컬럼을 datetime으로 변환
        announcements_df['created_at'] = pd.to_datetime(announcements_df['created_at'], errors='coerce')
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sources = announcements_df['source'].unique() if 'source' in announcements_df.columns else []
            selected_source = st.selectbox("출처 필터", ["전체"] + list(sources))
        
        with col2:
            agencies = announcements_df['agency'].unique() if 'agency' in announcements_df.columns else []
            selected_agency = st.selectbox("기관 필터", ["전체"] + list(agencies))
        
        with col3:
            search_term = st.text_input("공고명 검색")
        
        # 필터링 적용
        filtered_df = announcements_df.copy()
        
        if selected_source != "전체":
            filtered_df = filtered_df[filtered_df['source'] == selected_source]
        
        if selected_agency != "전체":
            filtered_df = filtered_df[filtered_df['agency'] == selected_agency]
        
        if search_term:
            filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
        
        # 표시할 컬럼 선택
        display_columns = ['title', 'agency', 'start_date', 'end_date', 'amount_text', 'source', 'created_at']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        st.dataframe(
            filtered_df[available_columns],
            width='stretch',
            column_config={
                "title": st.column_config.TextColumn("공고명", width="large"),
                "agency": st.column_config.TextColumn("주관기관", width="medium"),
                "start_date": st.column_config.DateColumn("모집시작", width="small"),
                "end_date": st.column_config.DateColumn("모집종료", width="small"),
                "amount_text": st.column_config.TextColumn("지원금액", width="medium"),
                "source": st.column_config.TextColumn("출처", width="small"),
                "created_at": st.column_config.DatetimeColumn("수집일시", width="small")
            }
        )
        
        st.info(f"총 {len(filtered_df)}개의 공고가 표시됩니다.")
    else:
        st.info("수집된 공고가 없습니다.")

def render_automation_tab():
    """자동화 설정 탭 렌더링"""
    st.subheader("🤖 자동화 시스템 설정")
    
    # 자동화 상태 표시
    st.info("""
    **자동화 시스템 기능:**
    - 매일 오전 9시에 K-스타트업과 기업마당에서 신규 공고 수집
    - 수집된 공고를 Supabase에 자동 저장
    - 모든 등록된 기업에 대해 맞춤 추천 자동 생성
    - 추천 결과를 Supabase와 파일로 저장
    """)
    
    # 수동 실행 버튼들
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 데이터 수집 실행", type="primary", use_container_width=True):
            with st.spinner("데이터 수집 중..."):
                try:
                    system = IntegratedAutoSystem()
                    collection_result = system.collect_daily_announcements()
                    
                    if collection_result['kstartup'] or collection_result['bizinfo']:
                        # Supabase에 저장
                        if collection_result['kstartup']:
                            system.save_announcements_to_supabase(collection_result['kstartup'], 'kstartup')
                        if collection_result['bizinfo']:
                            system.save_announcements_to_supabase(collection_result['bizinfo'], 'bizinfo')
                        
                        st.success(f"✅ 데이터 수집 완료!")
                        st.success(f"K-스타트업: {len(collection_result['kstartup'])}개")
                        st.success(f"기업마당: {len(collection_result['bizinfo'])}개")
                        st.rerun()
                    else:
                        st.info("새로운 공고가 없습니다.")
                except Exception as e:
                    st.error(f"데이터 수집 실패: {e}")
    
    with col2:
        if st.button("🎯 추천 생성 실행", type="primary", use_container_width=True):
            with st.spinner("추천 생성 중..."):
                try:
                    system = IntegratedAutoSystem()
                    collection_result = system.collect_daily_announcements()
                    all_announcements = collection_result['kstartup'] + collection_result['bizinfo']
                    
                    if all_announcements:
                        recommendations = system.generate_all_recommendations(all_announcements)
                        if recommendations:
                            system.save_recommendations_to_supabase(recommendations, collection_result['timestamp'])
                            system.save_recommendations_to_file(recommendations, collection_result['timestamp'])
                            st.success(f"✅ 추천 생성 완료! {len(recommendations)}개 기업")
                            st.rerun()
                        else:
                            st.warning("추천 생성에 실패했습니다.")
                    else:
                        st.info("추천할 공고가 없습니다.")
                except Exception as e:
                    st.error(f"추천 생성 실패: {e}")
    
    # 전체 자동화 실행
    if st.button("🚀 전체 자동화 실행", type="secondary", use_container_width=True):
        with st.spinner("전체 자동화 실행 중..."):
            try:
                system = IntegratedAutoSystem()
                system.daily_job()
                st.success("✅ 전체 자동화 실행 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"자동화 실행 실패: {e}")
    
    # 스케줄러 시작/중지
    st.divider()
    st.subheader("⏰ 스케줄러 제어")
    
    if st.button("▶️ 스케줄러 시작", type="primary"):
        st.info("스케줄러를 시작합니다. 매일 오전 9시에 자동으로 실행됩니다.")
        st.warning("⚠️ 스케줄러는 백그라운드에서 실행됩니다. 중지하려면 앱을 종료하세요.")
        
        # 백그라운드에서 스케줄러 실행
        def run_scheduler():
            system = IntegratedAutoSystem()
            system.start_scheduler()
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        
        st.success("스케줄러가 시작되었습니다!")

def main():
    """메인 함수"""
    st.set_page_config(
        page_title="정부지원사업 자동화 시스템",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏛️ 정부지원사업 자동화 시스템")
    st.markdown("---")
    
    # 사이드바 렌더링
    render_sidebar()
    
    # 메인 컨텐츠
    if 'selected_company' in st.session_state:
        company = st.session_state['selected_company']
        
        # 선택된 회사 헤더
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.subheader(f"🏢 {company['name']}")
        with col2:
            st.metric("성장단계", company.get('stage', 'N/A'))
        with col3:
            st.metric("업력", f"{company.get('years', 0)}년")
        with col4:
            if '매출' in company:
                st.metric("매출", company.get('매출', 'N/A'))
            else:
                st.metric("업종", company.get('industry', 'N/A'))
        
        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs(["📊 대시보드", "📋 맞춤 추천", "📰 공고 목록", "🤖 자동화 설정"])
        
        with tab1:
            render_dashboard_tab()
        
        with tab2:
            render_recommendations_tab()
        
        with tab3:
            render_announcements_tab()
        
        with tab4:
            render_automation_tab()
    else:
        # 회사가 선택되지 않은 경우
        tab1, tab2, tab3 = st.tabs(["📊 대시보드", "📰 공고 목록", "🤖 자동화 설정"])
        
        with tab1:
            render_dashboard_tab()
        
        with tab2:
            render_announcements_tab()
        
        with tab3:
            render_automation_tab()

if __name__ == "__main__":
    main()
