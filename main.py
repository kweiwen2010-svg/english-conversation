import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 頁面基本設定 (必須放在 Streamlit 程式碼的第一行)
st.set_page_config(page_title="AI English Tutor", page_icon="🇬🇧", layout="centered")

# 1. 讀取 .env 檔案中的金鑰
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Missing GEMINI_API_KEY! Please check your .env file.")
    st.stop()

# 2. 初始化 Gemini 客戶端
@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=api_key)

client = get_gemini_client()

# 3. 定義全英文的溫柔家教指令 (完全移除中文提示要求)
SYSTEM_INSTRUCTION = """
You are a warm, gentle, and extremely patient English tutor. 
Your goal is to help the user practice daily English conversation in a relaxed, stress-free environment.

Strict Rules you must follow:
1. Keep your English simple, clear, and easy to understand (around A2-B1 level). Avoid complex or archaic words.
2. DO NOT interrupt the user to correct their grammar or spelling errors during the conversation. 
3. If the user makes a mistake, implicitly use the correct grammar in your response so they can learn naturally.
4. NEVER end the conversation with a dead end. ALWAYS finish your response with ONE clear, friendly, open-ended question to guide the user to reply easily.
5. At the very end of your response, you MUST provide exactly two short "Hints" (in English ONLY) to help the user if they don't know how to reply or what to say next.

Format your output EXACTLY like this:
[Your reply in simple English. Ending with an open question]

---
💡 Hints you can use to reply:
• Choice 1: [A short English sentence example]
• Choice 2: [Another short English sentence example]

(Remember: Do NOT use any language other than English in your response.)
"""

# 4. 初始化對話記憶狀態
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
if "gemini_chat" not in st.session_state:
    # 建立具有記憶功能的對話物件
    st.session_state.gemini_chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
        )
    )
    # 讓 AI 自動發出第一句問候
    initial_response = st.session_state.gemini_chat.send_message(
        "Hello! Please introduce yourself briefly and say hello to me, so we can start our friendly conversation."
    )
    st.session_state.chat_history.append({"role": "assistant", "content": initial_response.text})

# --- UI 介面呈現 ---
st.title("🇬🇧 AI English Conversation Copilot")
st.caption("A stress-free environment to practice your spoken English. Type your response below!")
st.write("---")

# 5. 渲染歷史對話訊息
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 6. 使用者輸入對話框
if user_input := st.chat_input("Type your English response here..."):
    
    # 顯示使用者的對話氣泡
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # 顯示 AI 正在思考的讀條
    with st.chat_message("assistant"):
        with st.spinner("Your tutor is listening..."):
            # 發送訊息給 Gemini
            response = st.session_state.gemini_chat.send_message(user_input)
            st.write(response.text)
            
    # 將 AI 的回應存入歷史紀錄
    st.session_state.chat_history.append({"role": "assistant", "content": response.text})