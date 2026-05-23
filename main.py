import os
import io
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

st.set_page_config(page_title="AI English Tutor (EC 2.52)", page_icon="📱", layout="centered")
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("❌ 找不到 GEMINI_API_KEY！請檢查您的 .env 檔案。")
    st.stop()

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=api_key)

client = get_gemini_client()

st.title("🎙️ AI English Copilot (EC 2.52)")
st.caption("版本狀態：難易度控制版 | 語速請直接點擊語音條右側調整 ✨")

# --- 🛠️ 介面控制面板（只留下播放條做不到的難易度） ---
st.write("### ⚙️ 學習設定")
level = st.selectbox(
    "選擇對話難易度 (Difficulty)",
    ["中級 Regular (A2-B1)", "初級 Simple (A1-A2)", "高級 Advanced (C1-C2)"]
)

# --- 根據選擇動態調整大腦指令 ---
LEVEL_INSTRUCTIONS = {
    "初級 Simple (A1-A2)": "Use very simple words, extremely short sentences, and speak like you are talking to a beginner child. Avoid any idioms or complex phrasal verbs.",
    "中級 Regular (A2-B1)": "Use simple everyday English suitable for a casual conversation with a friend (A2-B1 level).",
    "高級 Advanced (C1-C2)": "Talk like a native speaker using advanced vocabulary, natural American idioms, phrasal verbs, and longer, more detailed sentences. Challenge the user!"
}

SYSTEM_INSTRUCTION = f"""
You are a friendly, chatty, and supportive friend from the US. 
Your primary goal is to keep a natural, two-way conversation flowing with the user.

[CURRENT SYSTEM DIFFICULTY]: {LEVEL_INSTRUCTIONS[level]}

Rules for holding a great conversation:
1. ALWAYS CATCH THE BALL: Respond directly to what the user just said. Show interest, surprise, or excitement before moving on. Never ignore their input.
2. ASK CATCHABLE QUESTIONS: Always end your response with ONE simple, casual, open-ended question. The question MUST be 100% connected to the current topic. No deep or stressful questions.
3. GUIDE THE CONVERSATION: If the user gives a very short answer, don't let the conversation die. Act like a good friend—ask for more details, or guide them by giving a tiny example from your own life.
4. KEEP IT CASUAL: Talk like a real person in a voice chat. Use friendly filler words like "Oh wow!", "Hmm", "No way!", or "That's cool!". Keep your text short and relaxed.
5. NO DIRECT CORRECTIONS: Never fix the user's grammar directly. Just model natural usage in your own words.
"""

if "current_level" not in st.session_state:
    st.session_state.current_level = level

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "mic_counter" not in st.session_state:
    st.session_state.mic_counter = 0

# --- 如果切換難易度，自動刷新對話 ---
if "gemini_chat" not in st.session_state or st.session_state.current_level != level:
    st.session_state.current_level = level
    st.session_state.chat_history = []
    
    st.session_state.gemini_chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7)
    )
    initial_response = st.session_state.gemini_chat.send_message(
        "Hey there! I'm so excited to chat with you today. How has your day been so far?"
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

st.write("---")

# 渲染歷史聊天訊息
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("audio_bytes"):
            st.audio(message["audio_bytes"], format=message["audio_mime"], autoplay=message.get("is_new", False))
            message["is_new"] = False

st.write("---")

user_input = None
current_mic_key = f"mobile_mic_{st.session_state.mic_counter}"

audio_recording = mic_recorder(
    start_prompt="🎤 Start Recording",
    stop_prompt="🛑 Stop & Send",
    key=current_mic_key
)

if audio_recording and "bytes" in audio_recording:
    audio_bytes = audio_recording["bytes"]
    if audio_bytes:
        with st.spinner("✨ Gemini 正在聆聽..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                        "Please transcribe this audio into English text. Only output the transcribed text, nothing else."
                    ]
                )
                transcribed_text = response.text.strip()
                if transcribed_text:
                    user_input = transcribed_text
            except Exception as e:
                st.error(f"❌ 語音轉錄失敗: {e}")

if not user_input:
    st.chat_input("Or type your English response here...", key="text_chat_input")
    if st.session_state.get("text_chat_input"):
        user_input = st.session_state.text_chat_input

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    if audio_recording and "bytes" in audio_recording:
        st.session_state.mic_counter += 1
        
    with st.chat_message("assistant"):
        with st.spinner("AI 朋友思考中..."):
            response = st.session_state.gemini_chat.send_message(user_input)
            
        assistant_audio_bytes = None
        with st.spinner("🎵 正在準備回覆語音..."):
            try:
                tts = gTTS(text=response.text.strip(), lang='en', tld='com')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                assistant_audio_bytes = fp.getvalue()
            except Exception as e:
                st.error(f"⚠️ 語音生成失敗: {e}")

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response.text,
        "audio_bytes": assistant_audio_bytes,
        "audio_mime": "audio/mp3",
        "is_new": True
    })
        
    st.rerun()