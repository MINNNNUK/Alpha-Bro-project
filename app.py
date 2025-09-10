ㅏㅇ
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json

# 페이지 설정
st.set_page_config(
    page_title="정부지원사업 맞춤 추천 플랫폼",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터 로드 함수들
@st.cache_data
def load_alpha_companies():
    """알파 기업 데이터 로드"""
    try:
        df = pd.read_csv('/Users/minkim/git_test/kpmg-2025/data2/alpha_companies.csv')
        return df
    except Exception as e:
        st.error(f"알파 기업 데이터 로드 오류: {e}")
        return pd.DataFrame()

@st.cache_data
def load_recommendation_data():
    """맞춤 추천 데이터 로드"""
    try:
        df = pd.read_csv('/Users/minkim/git_test/kpmg-2025/data2/2025 맞춤/활성공고만맞춤추천_결과.csv')
        return df
    except Exception as e:
        st.error(f"맞춤 추천 데이터 로드 오류: {e}")
        return pd.DataFrame()

@st.cache_data
def load_latest_announcements():
    """최신 공고 데이터 로드"""
    try:
        # K-Startup 데이터
        kstartup_files = [
            '/Users/minkim/git_test/kpmg-2025/data2/collected_data/kstartup_2025_daily_new_20250906_151712.csv',
            '/Users/minkim/git_test/kpmg-2025/data2/collected_data/kstartup_2025_recent_30days_2025-08-07_to_2025-09-06.csv'
        ]
        
        # BizInfo 데이터
        bizinfo_files = [
            '/Users/minkim/git_test/kpmg-2025/data2/collected_data_biz/bizinfo_2025_daily_new_20250906_153336.csv',
            '/Users/minkim/git_test/kpmg-2025/data2/collected_data_biz/bizinfo_2025_recent_30days_2025-08-07_to_2025-09-06.csv'
        ]
        
        all_data = []
        
        # K-Startup 파일들 로드
        for file in kstartup_files:
            if os.path.exists(file):
                try:
                    df = pd.read_csv(file)
                    df['source'] = 'K-Startup'
                    all_data.append(df)
                    print(f"K-Startup 파일 로드 성공: {file}, 행 수: {len(df)}")
                except Exception as e:
                    print(f"K-Startup 파일 로드 실패: {file}, 오류: {e}")
        
        # BizInfo 파일들 로드
        for file in bizinfo_files:
            if os.path.exists(file):
                try:
                    df = pd.read_csv(file)
                    df['source'] = 'BizInfo'
                    all_data.append(df)
                    print(f"BizInfo 파일 로드 성공: {file}, 행 수: {len(df)}")
                except Exception as e:
                    print(f"BizInfo 파일 로드 실패: {file}, 오류: {e}")
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            print(f"전체 최신 공고 데이터 로드 완료: {len(combined_df)}행")
            return combined_df
        else:
            print("로드된 데이터가 없습니다.")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"최신 공고 데이터 로드 오류: {e}")
        return pd.DataFrame()

@st.cache_data
def load_integrated_announcements():
    """통합 공고 데이터 로드"""
    try:
        df = pd.read_csv('/Users/minkim/git_test/kpmg-2025/data2/통합공고/2025년도_정부지원사업_통합공고_최종분석결과.csv')
        return df
    except Exception as e:
        st.error(f"통합 공고 데이터 로드 오류: {e}")
        return pd.DataFrame()

def save_company_data(company_data):
    """회사 데이터 저장"""
    try:
        # 기존 데이터 읽기 (캐시 무시)
        existing_df = pd.read_csv('/Users/minkim/git_test/kpmg-2025/data2/alpha_companies.csv')
        
        # 새 데이터 추가
        new_df = pd.DataFrame([company_data])
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # CSV 파일로 저장
        updated_df.to_csv('/Users/minkim/git_test/kpmg-2025/data2/alpha_companies.csv', index=False)
        
        # 캐시 클리어
        load_alpha_companies.clear()
        
        return True
    except Exception as e:
        st.error(f"회사 데이터 저장 오류: {e}")
        return False

def get_company_recommendations(company_name, recommendation_df):
    """특정 회사의 맞춤 추천 공고 가져오기"""
    if recommendation_df.empty:
        return pd.DataFrame()
    
    # 회사명으로 필터링 (기업명 컬럼 사용)
    filtered_df = recommendation_df[recommendation_df['기업명'] == company_name]
    return filtered_df

def get_latest_announcements_by_company(company_name, announcements_df):
    """회사 정보 기반 최신 공고 필터링"""
    if announcements_df.empty:
        return pd.DataFrame()
    
    # 회사 정보 가져오기
    alpha_companies = load_alpha_companies()
    company_info = alpha_companies[alpha_companies['사업아이템 한 줄 소개'] == company_name]
    
    if company_info.empty:
        return announcements_df.head(10)  # 기본적으로 최신 10개
    
    # 회사 정보에서 키워드 추출
    keywords = []
    for col in ['사업아이템 한 줄 소개', '업종', '전문분야']:
        if col in company_info.columns:
            value = company_info[col].iloc[0]
            if pd.notna(value) and value != '':
                keywords.extend(str(value).split())
    
    # 키워드 기반 필터링
    filtered_announcements = []
    for _, announcement in announcements_df.iterrows():
        score = 0
        announcement_text = ' '.join([str(announcement[col]) for col in announcement.index if pd.notna(announcement[col])])
        
        for keyword in keywords:
            if keyword.lower() in announcement_text.lower():
                score += 1
        
        if score > 0:
            announcement['match_score'] = score
            filtered_announcements.append(announcement)
    
    if filtered_announcements:
        result_df = pd.DataFrame(filtered_announcements)
        return result_df.sort_values('match_score', ascending=False).head(10)
    else:
        return announcements_df.head(10)

def generate_custom_recommendations(company_info, integrated_announcements, latest_announcements):
    """새로 추가된 회사를 위한 맞춤 추천 생성"""
    if integrated_announcements.empty and latest_announcements.empty:
        return pd.DataFrame()
    
    # 회사 정보에서 키워드 추출
    keywords = []
    for col in ['사업아이템 한 줄 소개', '업종', '전문분야']:
        if col in company_info.columns:
            value = company_info[col].iloc[0]
            if pd.notna(value) and value != '':
                keywords.extend(str(value).split())
    
    recommendations = []
    
    # 통합 공고에서 추천
    if not integrated_announcements.empty:
        for _, announcement in integrated_announcements.iterrows():
            score = 0
            announcement_text = ' '.join([str(announcement[col]) for col in announcement.index if pd.notna(announcement[col])])
            
            for keyword in keywords:
                if keyword.lower() in announcement_text.lower():
                    score += 1
            
            if score > 0:
                announcement['match_score'] = score
                announcement['source'] = '통합공고'
                recommendations.append(announcement)
    
    # 최신 공고에서 추천
    if not latest_announcements.empty:
        for _, announcement in latest_announcements.iterrows():
            score = 0
            announcement_text = ' '.join([str(announcement[col]) for col in announcement.index if pd.notna(announcement[col])])
            
            for keyword in keywords:
                if keyword.lower() in announcement_text.lower():
                    score += 1
            
            if score > 0:
                announcement['match_score'] = score
                if 'source' not in announcement:
                    announcement['source'] = '최신공고'
                recommendations.append(announcement)
    
    if recommendations:
        result_df = pd.DataFrame(recommendations)
        return result_df.sort_values('match_score', ascending=False).head(10)
    else:
        return pd.DataFrame()

def get_added_companies():
    """추가된 회사 목록 가져오기 (캐시 무시)"""
    try:
        # 캐시를 무시하고 직접 파일 읽기
        df = pd.read_csv('/Users/minkim/git_test/kpmg-2025/data2/alpha_companies.csv')
        # No.가 23보다 큰 회사들 (새로 추가된 회사들)
        added_companies = df[df['No.'] > 23]
        return added_companies
    except Exception as e:
        st.error(f"추가된 회사 목록 로드 오류: {e}")
        return pd.DataFrame()

def delete_company(company_no):
    """회사 삭제"""
    try:
        # 기존 데이터 읽기
        df = pd.read_csv('/Users/minkim/git_test/kpmg-2025/data2/alpha_companies.csv')
        
        # 해당 회사 삭제
        df = df[df['No.'] != company_no]
        
        # No. 컬럼 재정렬
        df['No.'] = range(1, len(df) + 1)
        
        # CSV 파일로 저장
        df.to_csv('/Users/minkim/git_test/kpmg-2025/data2/alpha_companies.csv', index=False)
        
        # 캐시 클리어
        load_alpha_companies.clear()
        
        return True
    except Exception as e:
        st.error(f"회사 삭제 오류: {e}")
        return False

def main():
    st.title("🏢 정부지원사업 맞춤 추천 플랫폼")
    
    # 데이터 로드
    alpha_companies = load_alpha_companies()
    recommendation_data = load_recommendation_data()
    latest_announcements = load_latest_announcements()
    integrated_announcements = load_integrated_announcements()
    
    # 세션 상태 초기화
    if 'selected_company' not in st.session_state:
        st.session_state.selected_company = None
    if 'company_type' not in st.session_state:
        st.session_state.company_type = None
    
    # 사이드바
    with st.sidebar:
        st.header("회사 관리")
        
        # 기존 회사 선택
        if not alpha_companies.empty:
            company_names = alpha_companies['사업아이템 한 줄 소개'].tolist()
            selected_company = st.selectbox(
                "기존 회사 선택",
                ["회사를 선택하세요"] + company_names
            )
            
            if selected_company != "회사를 선택하세요":
                if st.button("선택한 회사로 설정"):
                    st.session_state.selected_company = selected_company
                    st.session_state.company_type = "existing"
                    st.success(f"'{selected_company}' 회사가 선택되었습니다.")
        
        # 추가된 회사 목록
        st.subheader("추가된 회사 목록")
        added_companies = get_added_companies()
        
        if not added_companies.empty:
            st.info(f"총 {len(added_companies)}개의 추가된 회사가 있습니다.")
            for _, company in added_companies.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"선택: {company['사업아이템 한 줄 소개']}", key=f"select_{company['No.']}"):
                        st.session_state.selected_company = company['사업아이템 한 줄 소개']
                        st.session_state.company_type = "added"
                        st.success(f"'{company['사업아이템 한 줄 소개']}' 회사가 선택되었습니다.")
                        st.rerun()
                
                with col2:
                    if st.button("삭제", key=f"delete_{company['No.']}"):
                        if delete_company(company['No.']):
                            st.success("회사가 삭제되었습니다.")
                            st.rerun()
                        else:
                            st.error("회사 삭제에 실패했습니다.")
        else:
            st.info("추가된 회사가 없습니다.")
        
        # 새 회사 추가
        st.subheader("새 회사 추가")
        with st.form("add_company_form"):
            new_company_name = st.text_input("회사명 (사업아이템 한 줄 소개)")
            business_type = st.selectbox("사업자 유형", ["개인", "법인"])
            establishment_date = st.date_input("설립일")
            location = st.text_input("소재지")
            business_registration_date = st.date_input("사업자등록일")
            business_category = st.text_input("업종")
            specialty = st.text_input("전문분야")
            business_intro = st.text_area("사업 소개")
            
            if st.form_submit_button("회사 추가"):
                if new_company_name:
                    # 새로운 No. 계산
                    new_no = len(alpha_companies) + 1
                    
                    company_data = {
                        'No.': new_no,
                        '사업자유형': business_type,
                        '설립일': establishment_date.strftime('%Y.%m.%d'),
                        '소재지': location,
                        '사업자등록일': business_registration_date.strftime('%Y.%m.%d'),
                        '업종': business_category,
                        '전문분야': specialty,
                        '사업아이템 한 줄 소개': new_company_name,
                        '사업소개': business_intro,
                        '기타1': '',
                        '기타2': '',
                        '기타3': '',
                        '기타4': '',
                        '기타5': '',
                        '기타6': '',
                        '기타7': '',
                        '기타8': ''
                    }
                    
                    if save_company_data(company_data):
                        st.success("회사가 성공적으로 추가되었습니다!")
                        # 추가된 회사 수 표시
                        added_count = len(get_added_companies())
                        st.info(f"현재 추가된 회사 수: {added_count}개")
                        st.session_state.selected_company = new_company_name
                        st.session_state.company_type = "added"
                        st.rerun()
                    else:
                        st.error("회사 추가에 실패했습니다.")
                else:
                    st.error("회사명을 입력해주세요.")
    
    # 메인 컨텐츠
    if st.session_state.selected_company:
        st.header(f"📊 {st.session_state.selected_company} - 맞춤 추천")
        
        # 탭 생성
        tab1, tab2 = st.tabs(["🎯 맞춤 추천", "📰 최신 공고"])
        
        with tab1:
            st.subheader("맞춤 추천 공고")
            
            if st.session_state.company_type == "existing":
                # 기존 회사의 맞춤 추천
                recommendations = get_company_recommendations(st.session_state.selected_company, recommendation_data)
                
                if not recommendations.empty:
                    for _, rec in recommendations.iterrows():
                        with st.expander(f"📋 {rec.get('공고이름', 'N/A')}"):
                            st.write(f"**기업명:** {rec.get('기업명', 'N/A')}")
                            st.write(f"**공고이름:** {rec.get('공고이름', 'N/A')}")
                            st.write(f"**추천이유:** {rec.get('추천이유', 'N/A')}")
                            st.write(f"**모집일:** {rec.get('모집일', 'N/A')}")
                            st.write(f"**마감일:** {rec.get('마감일', 'N/A')}")
                            st.write(f"**남은기간/마감여부:** {rec.get('남은기간/마감여부', 'N/A')}")
                            st.write(f"**투자금액:** {rec.get('투자금액', 'N/A')}")
                            st.write(f"**투자금액사용처:** {rec.get('투자금액사용처', 'N/A')}")
                            st.write(f"**공고상태:** {rec.get('공고상태', 'N/A')}")
                else:
                    st.info("해당 회사에 대한 맞춤 추천이 없습니다.")
            
            else:  # 새로 추가된 회사
                # 회사 정보 가져오기
                company_info = alpha_companies[alpha_companies['사업아이템 한 줄 소개'] == st.session_state.selected_company]
                
                if not company_info.empty:
                    # 맞춤 추천 생성
                    custom_recommendations = generate_custom_recommendations(
                        company_info, integrated_announcements, latest_announcements
                    )
                    
                    if not custom_recommendations.empty:
                        for _, rec in custom_recommendations.iterrows():
                            with st.expander(f"📋 {rec.get('사업명', rec.get('pblancNm', rec.get('title', 'N/A')))}"):
                                st.write(f"**출처:** {rec.get('source', 'N/A')}")
                                st.write(f"**매칭 점수:** {rec.get('match_score', 'N/A')}")
                                
                                # 통합공고 데이터
                                if rec.get('source') == '통합공고':
                                    st.write(f"**기관명:** {rec.get('기관명', 'N/A')}")
                                    st.write(f"**사업명:** {rec.get('사업명', 'N/A')}")
                                    st.write(f"**사업개요:** {rec.get('사업개요', 'N/A')}")
                                    st.write(f"**지원대상:** {rec.get('지원대상', 'N/A')}")
                                    st.write(f"**지원내용:** {rec.get('지원내용', 'N/A')}")
                                    st.write(f"**신청기간:** {rec.get('신청기간', 'N/A')}")
                                    st.write(f"**문의처:** {rec.get('문의처', 'N/A')}")
                                
                                # 최신공고 데이터
                                else:
                                    st.write(f"**사업공고명:** {rec.get('사업공고명', rec.get('pblancNm', rec.get('title', 'N/A')))}")
                                    st.write(f"**공고내용:** {rec.get('공고내용', rec.get('description', rec.get('bsnsSumryCn', 'N/A')))}")
                                    st.write(f"**신청기간:** {rec.get('신청기간', rec.get('rceptPd', 'N/A'))}")
                                    st.write(f"**문의처:** {rec.get('문의처', rec.get('inquiry', 'N/A'))}")
                    else:
                        st.info("해당 회사에 대한 맞춤 추천이 없습니다.")
                else:
                    st.error("회사 정보를 찾을 수 없습니다.")
        
        with tab2:
            st.subheader("최신 공고")
            
            if st.session_state.company_type == "existing":
                # 기존 회사의 최신 공고
                company_announcements = get_latest_announcements_by_company(st.session_state.selected_company, latest_announcements)
            else:
                # 새로 추가된 회사의 최신 공고
                company_info = alpha_companies[alpha_companies['사업아이템 한 줄 소개'] == st.session_state.selected_company]
                if not company_info.empty:
                    company_announcements = get_latest_announcements_by_company(st.session_state.selected_company, latest_announcements)
                else:
                    company_announcements = latest_announcements.head(10)
            
            if not company_announcements.empty:
                for _, announcement in company_announcements.iterrows():
                    # 공고명 결정 (K-Startup vs BizInfo)
                    if announcement.get('source') == 'K-Startup':
                        title = announcement.get('사업공고명', 'N/A')
                        org = announcement.get('공고기관명', 'N/A')
                        content = announcement.get('공고내용', 'N/A')
                        target = announcement.get('신청대상', 'N/A')
                        start_date = announcement.get('접수시작일', 'N/A')
                        end_date = announcement.get('접수종료일', 'N/A')
                        contact = announcement.get('담당연락처', 'N/A')
                    else:  # BizInfo
                        title = announcement.get('pblancNm', announcement.get('title', 'N/A'))
                        org = announcement.get('excInsttNm', announcement.get('author', 'N/A'))
                        content = announcement.get('bsnsSumryCn', announcement.get('description', 'N/A'))
                        target = announcement.get('trgetNm', 'N/A')
                        reqst_dt = announcement.get('reqstDt', 'N/A')
                        start_date = reqst_dt.split(' ~ ')[0] if ' ~ ' in str(reqst_dt) else reqst_dt
                        end_date = reqst_dt.split(' ~ ')[1] if ' ~ ' in str(reqst_dt) else 'N/A'
                        contact = announcement.get('inqireCo', 'N/A')
                    
                    with st.expander(f"📰 {title}"):
                        st.write(f"**출처:** {announcement.get('source', 'N/A')}")
                        if 'match_score' in announcement:
                            st.write(f"**매칭 점수:** {announcement['match_score']}")
                        st.write(f"**공고기관명:** {org}")
                        st.write(f"**공고내용:** {content}")
                        st.write(f"**신청대상:** {target}")
                        st.write(f"**접수시작일:** {start_date}")
                        st.write(f"**접수종료일:** {end_date}")
                        st.write(f"**문의처:** {contact}")
            else:
                st.info("최신 공고가 없습니다.")
    
    else:
        st.info("👈 왼쪽 사이드바에서 회사를 선택하거나 새 회사를 추가해주세요.")

if __name__ == "__main__":
    main()