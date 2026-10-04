import streamlit as st
import os
from openai import OpenAI
import datetime
import json

#设置页面的基本配置项
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

#大标题
st.title("AI智能伴侣")

#系统提示词
system_prompt = """
你叫 %s,现在是用户的真实伴侣,请完全代入伴侣角色.
规则:
1.每次只能回一条消息
2.禁止任何场景或状态性描述
3.匹配用户的语言
4.回复简短,像微信聊天一样
5.有需要的话可以使用emoji表情
6.用符合伴侣性格的方式对话
7.回复的内容,要充分体现伴侣的性格特征
伴侣性格:
%s
你必须严格按照上述规则来回复用户!
"""

# 保存会话信息:
def save_session():
    if st.session_state.current_session:
        session_data = {
            "current_session": st.session_state.current_session,
            "nick_name": st.session_state.nick_name,
            "character_traits": st.session_state.character_traits,
            "messages": st.session_state.messages
        }
        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        with open(f"sessions/%s.json" % st.session_state.current_session, "w", encoding = "utf-8") as f:
                json.dump(session_data, f,ensure_ascii=False, indent=2)

#加载所有会话信息:
def load_sessions():
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for file_name in file_list:
            if file_name.endswith(".json"):
                session_list.append(file_name[:-5])
                session_list.sort(reverse = True)
    return session_list

#加载指定会话信息:
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json", "r", encoding = "utf-8") as f:
                session_data = json.load(f)
                st.session_state.current_session = session_name
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.character_traits = session_data["character_traits"]
                st.session_state.messages = session_data["messages"]
    except Exception:
        st.error("读取会话信息失败!")

#删除会话:
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = ""
    except Exception:
        st.error("删除会话信息失败!")

# 初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages = []
# 初始化昵称信息:
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "雨姐"
# 初始化伴侣性格信息:
if "character_traits" not in st.session_state:
    st.session_state.character_traits = "活泼开朗的东北姑娘,可以参考网红东北雨姐的风格"
# 初始化会话标识:
if "current_session" not in st.session_state:
    st.session_state.current_session = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#展示聊天记录
st.text(f"当前会话:{st.session_state.current_session}")
for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

#创建与AI大模型交互的客户端对象
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

#左侧侧边栏
with st.sidebar:
    st.subheader("伴侣信息")

    #会话框管理:
    st.subheader("AI控制面板")

    #新建会话框:
    if st.button("新建会话", width = "stretch", icon = "🫆"):
       save_session()
       if st.session_state.messages:
            st.session_state.messages = []
            st.session_state.current_session = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            save_session()
            st.rerun()

    #历史会话
    st.text("历史会话")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(session, width = "stretch", icon = "📄", key = f"load_{session}", type = "primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
        with col2:
            if st.button("", width = "stretch", icon = "❌", key = f"delete_{session}"):
                delete_session(session)
                st.rerun()

    #分割线
    st.divider()

    #昵称输入框:
    nick_name = st.text_input("昵称", placeholder="请输入伴侣的昵称...",value = st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name

    #性格特征输入框:
    character_traits = st.text_area("性格特征", placeholder="请输入伴侣的性格特征...",value = st.session_state.character_traits)
    if character_traits:
        st.session_state.character_traits = character_traits

#消息输入框
prompt = st.chat_input("请输入您的问题或需求...")
if prompt:
    #显示用户输入的消息
    st.chat_message("user").write(prompt)
    print("<--------- 用户输入,调用AI大模型")
    #保存用户输入的消息
    st.session_state.messages.append({"role": "user", "content": prompt})

    #调用AI大模型
    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com")
    
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {"role": "system", "content": system_prompt %(st.session_state.nick_name,st.session_state.character_traits)},
            *st.session_state.messages
            # {"role": "user", "content": prompt},
        ],
        stream=True,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )

    print("---------> AI大模型调用结束,显示结果")

    #获取AI的回复(非流式输出的解析方式)
    # print(response.choices[0].message.content)
    # assistant_response = response.choices[0].message.content  # 这里可以替换为实际的AI模型调用
    # #显示AI的回复
    # st.chat_message("assistant").write(assistant_response)

    #获取AI的回复(流式输出的解析方式)
    response_message = st.empty()
    full_concent = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            concent = chunk.choices[0].delta.content
            full_concent += concent
            response_message.chat_message("assistant").write(full_concent)

    #保存AI的回复
    st.session_state.messages.append({"role": "assistant", "content": full_concent})

    #保存会话
    save_session()