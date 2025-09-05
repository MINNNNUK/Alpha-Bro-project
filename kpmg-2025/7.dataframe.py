import streamlit as st
import pandas as pd

# 1. 데이터 읽기
# data_subway_in_seoul.csv
# encoding='cp949'  읽어오고 확인하기 
st.text('1. 지하철 데이터 읽고 확인- data_subway_in_seoul.csv')
df = pd.read_csv('data/data_subway_in_seoul.csv', encoding='cp949')
st.dataframe(df)

# 2. '하차' 데이터만 필터링
st.text("2. 구분이 '하차'인 행만 새로운 데이터프레임으로 저장 & 확인") 

df_off = df[df['구분']=='하차']
st.dataframe(df_off)

# 3. 불필요 컬럼 제거
st.text("3. '날짜','연번','역번호','역명','구분','합계' 제외하고 저장 & 확인")

# 방법 1: columns.difference 사용 → 지정한 컬럼을 제외하고 가져오기 (단, 컬럼 순서가 바뀔 수 있음)
df_line = df_off[df_off.columns.difference(['날짜', '연번', '역번호', '역명', '구분', '합계'])]    # columns.difference 쓰면 호선이 제일 뒤로 감

# 방법 2: drop으로 지정한 컬럼 제거 (순서 유지됨)
#df_line = df_off.drop(['날짜', '연번', '역번호', '역명', '구분', '합계'], axis=1) 
st.dataframe(df_line)

# 4. 데이터 구조 변환 (melt)
st.text("4. 아래 방법으로 데이터프레임 변환하여 저장 & 확인")
st.caption("melt 함수 사용 unpivot: identifier-'호선', unpivot column-'시간', variable column-'인원수'")
df_line_melted = pd.melt(df_line, id_vars=['호선'], var_name='시간', value_name='인원수')
st.dataframe(df_line_melted)

# 5. Groupby 집계
st.text("5. '호선','시간' groupby 인원수합 + .reset_index() 저장 & 확인")
df_line_melted = df_line_melted.groupby(['호선','시간'])['인원수'].sum().reset_index()
st.dataframe(df_line_melted)
