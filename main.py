import os
import io
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

# 1. 網頁基本設定
st.set_page_config(page_title="AI English Tutor (EC 2.7)", page_icon="📱", layout="centered")
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("❌ 找不到 GEMINI_API_KEY！請檢查您的 .env 檔案。")
    st.stop()

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=api_key)

client = get_gemini_client()

# 2. 側邊欄設定區
with st.sidebar:
    st.header("⚙️ 學習設定")
    level = st.selectbox(
        "選擇對話難易度 (Difficulty)",
        ["中級 Regular (A2-B1)", "初級 Simple (A1-A2)", "高級 Advanced (C1-C2)"]
    )
    st.write("---")
    st.markdown("""
    ### 📱 狀態說明
    - **版本：** EC 2.7 (Mia 版)
    - **核心優化：** 1. 專屬英文專門 Copilot - Mia 靈魂寫入
      2. 支援中英夾雜智慧翻譯轉錄
      3. 鍵盤與語音介面視覺優化
    - **提示：** 語速請點擊對話框內的語音條右側三個點自行調整 ✨
    """)

LEVEL_INSTRUCTIONS = {
    "初級 Simple (A1-A2)": "Use very simple words, extremely short sentences, and speak like you are talking to a beginner child. Avoid any idioms or complex phrasal verbs.",
    "中級 Regular (A2-B1)": "Use simple everyday English suitable for a casual conversation with a friend (A2-B1 level).",
    "高級 Advanced (C1-C2)": "Talk like a native speaker using advanced vocabulary, natural American idioms, phrasal verbs, and longer, more detailed sentences. Challenge the user!"
}

# Mia 的核心人設定義
SYSTEM_INSTRUCTION = f"""
Your name is Mia. You are a friendly, chatty, and supportive friend from the US. 
Always introduce yourself or reference yourself as Mia when appropriate.
Your primary goal is to keep a natural, two-way conversation flowing with the user.

[CURRENT SYSTEM DIFFICULTY]: {LEVEL_INSTRUCTIONS[level]}

Rules for holding a great conversation:
1. ALWAYS CATCH THE BALL: Respond directly to what the user just said. Show interest, surprise, or excitement before moving on. Never ignore their input.
2. ASK CATCHABLE QUESTIONS: Always end your response with ONE simple, casual, open-ended question. The question MUST be 100% connected to the current topic. No deep or stressful questions.
3. GUIDE THE CONVERSATION: If the user gives a very short answer, don't let the conversation die. Act like a good friend—ask for more details, or guide them by giving a tiny example from your own life.
4. KEEP IT CASUAL: Talk like a real person in a voice chat. Use friendly filler words like "Oh wow!", "Hmm", "No way!", or "That's cool!". Keep your text short and relaxed.
5. NO DIRECT CORRECTIONS: Never fix the user's grammar directly. Just model natural usage in your own words.
"""

# 3. 初始化 Session States
if "current_level" not in st.session_state:
    st.session_state.current_level = level

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "mic_counter" not in st.session_state:
    st.session_state.mic_counter = 0

# 難易度切換時重置聊天
if "gemini_chat" not in st.session_state or st.session_state.current_level != level:
    st.session_state.current_level = level
    st.session_state.chat_history = []
    
    st.session_state.gemini_chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7)
    )
    
    # 讓 Mia 在開場白主動向使用者自我介紹
    initial_response = st.session_state.gemini_chat.send_message(
        "Hey there! I'm Mia, your English copilot. I'm so excited to chat with you today! How has your day been so far?"
    )
    
    initial_audio_bytes = None
    try:
        tts = gTTS(text=initial_response.text.strip(), lang='en', tld='com')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        initial_audio_bytes = fp.getvalue()
    except Exception:
        pass

    st.session_state.chat_history.append({
        "role": "assistant", 
        "content": initial_response.text,
        "audio_bytes": initial_audio_bytes,
        "audio_mime": "audio/mp3",
        "is_new": True
    })

# 4. 主畫面渲染
st.title("🎙️ AI English Copilot (EC 2.7)")
st.caption("今天也是與 Mia 自然開口說英文的好日子！")
st.write("---")

# 顯示歷史對話
for message in st.session_state.