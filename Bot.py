import streamlit as st

st.title('음식 추천 챗봇')

if user_input := st.chat_input("메세지를 입력해주세요."):
    st.chat_message("user").write(f"{user_input}")