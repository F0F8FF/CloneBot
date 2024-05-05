import streamlit as st
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import ChatMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.callbacks.base import BaseCallbackHandler
import os

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

st.title('ChatGPT 클론 서비스')

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        ChatMessage(role="assistant", content="안녕하세요.")
    ]

#채팅 대화기록 저장
if "store"  not in st.session_state:
    st.session_state["store"] = dict()

with st.sidebar:
    session_id = st.text_input("Session ID", value="abc123")
    #채팅 대화기록 초기화
    clear_btn = st.button("clear")
    if clear_btn:
        st.session_state["messages"] = []
        st.session_state["store"] = dict()
        st.experimental_rerun()

#이전 대화 출력
if "messages" in st.session_state and len(st.session_state["messages"]) > 0:
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)

#세션 ID를 기반으로 세션 기록을 가져옴
def get_session_history(session_ids: str) -> BaseChatMessageHistory:
    if session_ids not in st.session_state["store"]:
        st.session_state["store"][session_ids] = ChatMessageHistory()
    return st.session_state["store"][session_ids]

if user_input := st.chat_input("메세지를 입력해주세요."):
    #사용자가 입력한 내용
    st.chat_message("user").write(f"{user_input}")
    st.session_state["messages"].append(ChatMessage(role="user", content=user_input))
    
    #AI 답변
    with st.chat_message("assistant"):
        stream_handler = StreamHandler(st.empty())

        #모델 생성
        llm = ChatOpenAI(streaming=True, callbacks=[stream_handler])
        #프롬프트 생성
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "질문에 짧고 간결하게 답변해 주세요.",
                ),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        chain = prompt | llm

        chain_with_memory = (
            RunnableWithMessageHistory(
                chain,
                get_session_history,
                input_messages_key="question",
                history_messages_key="history",
            )
        )

        response = chain_with_memory.invoke(
            {"question" : user_input},
            #세션 ID 설정
            config={"configurable" : {"session_id" : session_id}},
        )

        st.session_state["messages"].append(
            ChatMessage(role="assistant", content=response.content)
        )