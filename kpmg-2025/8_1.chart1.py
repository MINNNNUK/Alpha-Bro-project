import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px
# px 모듈이 없다고 에러가 나는 경우에만 아래 방법으로 plotly 라이브러리 설치
# File > New > Terminal 선택 후, 창에 다음 구분 실행 pip install plotly 

# Unit 1. Streamlit Simple chart
st.header('Unit 1. Streamlit Simple chart')

chart_data = pd.read_csv('https://raw.githubusercontent.com/huhshin/streamlit/master/data_sales.csv')

st.subheader('1. Simple Line chart')
#use_container_width=True 가로로 화면에 꽉 채워 줌
st.line_chart(chart_data, use_container_width=True)

st.subheader('2. Simple Bar chart')
st.bar_chart(chart_data)

st.subheader('3. Simple area chart')
st.area_chart(chart_data)


# Unit 2. Altair chart
st.header('Unit 2. Altair chart') 

# 1) 리테일 매출 데이터 로드 (Wide 형태: 열에 팀별 매출이 들어 있음)
# identifier(x)-'date', unpivot column(범례,color)-'teams’, variable column(y)-'sales'
# id_vars=['date'], var_name='teams', value_name='sales'
df = pd.read_csv('https://raw.githubusercontent.com/huhshin/streamlit/master/data_retail.csv')

# 2) melt로 Wide → Long 변환
# id_vars : 그대로 유지할 식별자 컬럼
df_melted = pd.melt(df, id_vars=['date'], var_name='teams', value_name='sales')

# columns 함수를 이용하여 좌-원본 데이터, 우-변환 데이터 확인하기
col1, col2 = st.columns(2)
with col1:
    st.text('원본 데이터-df')
    st.dataframe(df)
with col2:
    st.text('변경 데이터-df_melted')
    st.dataframe(df_melted)
        


st.subheader('4-1. Altair Line chart')
chart = alt.Chart(df_melted, title='일별 팀 매출 비교').mark_line().encode(x='date', y='sales', color='teams', strokeDash='teams').properties(width=650, height=350)

# 각 점 위에 매출값 라벨 표시
text = alt.Chart(df_melted).mark_text(dx=0,dy=0,color='black').encode(x='date', y='sales', detail='teams', text=alt.Text('sales:Q'))
st.altair_chart(chart+text, use_container_width=True)  # use_container_width = True 가로로 화면에 채워줌
    
st.subheader('4-2. Altair Bar chart')
chart = alt.Chart(df_melted, title='일별 매출').mark_bar().encode(x='date', y='sales', color='teams')

text = alt.Chart(df_melted).mark_text(dx=0,dy=0,color='black').encode(x='date', y='sales', detail='teams', text=alt.Text('sales:Q'))  # 소수점 이하 1자리: 'sales:Q', format='.1f'  
    
st.altair_chart(chart+text, use_container_width=True)
    

st.subheader('4-3. Altair Scatter chart')

iris = pd.read_csv('https://raw.githubusercontent.com/huhshin/streamlit/master/data_iris.csv')
# caption으로 'sepal:꽃받침, petal:꽃잎' 설명 출력하기 


# petal_length, petal_width로 Altair Circle chart 그리기
chart = alt.Chart(iris).mark_circle().encode(x='petal_length', y='petal_width', color='species')    
st.altair_chart(chart, use_container_width=True)

st.header('Unit 3. Plotly pie/Donut chart')


# 두 개의 탭: 파이 vs 도넛
medal = pd.read_csv('https://raw.githubusercontent.com/huhshin/streamlit/master/data_medal.csv')
tab1, tab2 = st.tabs(['Plotly pie', 'Donut chart'])
with tab1:
    st.text('Plotly pie')
    fig=px.pie(medal, values='gold', names='nation', title='올림픽 양궁 금메달 현황')        # values: 비율 기준 열, names: 라벨
    fig.update_traces(textposition='inside', textinfo = 'percent+label+value')            # 조각 내부에 percent+label+value 표시
    fig.update_layout(font = dict(size=16))                                               # 범례 표시 제거 : fig.update(layout_showlegend=False)
    st.plotly_chart(fig)
with tab2:
    st.text('Donut chart')
    fig=px.pie(medal, values='gold', names='nation', title='올림픽 양궁 금메달 현황', hole=.3)   # hole=0.3 → 도넛 형태
    fig.update_traces(textposition='outside', textinfo = 'percent+label+value')               # 도넛 바깥쪽에 라벨/비율/값 표시
    fig.update_layout(font = dict(size=16))
    # 범례 표시 제거 : fig.update(layout_showlegend=False)
    st.plotly_chart(fig) 