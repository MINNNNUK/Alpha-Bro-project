# streamlit 라이브러리 불러오기
import streamlit as st
import time

st.title('Media elements')
st.caption('text 참고사이트: https://docs.streamlit.io/library/api-reference/media')

st.header('1.Image')
# 버튼을 누를 때마다 랜덤 이미지
if st.button('랜덤이미지'):
    random_url = f'https://picsum.photos/250/250?random={time.time()}'
    st.image(random_url)

st.header('2.Audio')
st.audio('/Users/minkim/git_test/kpmg-2025/data/MusicSample.mp3')

st.header('3.Video')
st.video('/Users/minkim/git_test/kpmg-2025/data/VideoSample.mp4')