import os
import io
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(page_title="AI English Tutor (EC 3.0 Flagship)", page_icon="📱", layout="centered")
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("❌ 找不到 GEMINI_API_KEY！請檢查您的 .env 檔案。")
    st.stop()

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=api_key)

client = get_gemini_client()

# ==========================================
# 2. 側邊欄設定區
# ==========================================
with st.sidebar:
    st.header("⚙️ 旗艦版學習設定")
    level = st.selectbox(
        "選擇對話難易度 (Difficulty)",
        ["中級 Regular (A2-B1)", "初級 Simple (A1-A2)", "高級 Advanced (C1-C2)"]
    )
    st.write("---")
    st.markdown("""
### 📱 狀態說明
- **版本：** EC 3.0 (雙 Pro 旗艦體)
- **初衷優化：**
  1. **聊天大腦直升 `gemini-2.5-pro`**：賦予 Mia 超越 Sarah 的頂級情商與神級多模態理解力。
  2. 鎖死對話記憶，網頁與錄音重整絕不失憶。
  3. 徹底根除鸚鵡複誦、生硬審問，面對破碎字眼時展現極致體貼的留白。
""")

LEVEL_INSTRUCTIONS = {
    "初級 Simple (A1-A2)": "Use simple words and extremely short sentences suitable for a beginner. Avoid complex idioms.",
    "中級 Regular (A2-B1)": "Use everyday natural English suitable for a casual conversation with a close friend.",
    "高級 Advanced (C1-C2)": "Use advanced vocabulary, natural American idioms, and complex sentence structures to challenge the user."
}

# 🌟 EC 3.0 旗艦人設：專為 Pro 大腦量身打造，展現極致細膩的情感與「超自然重組」
SYSTEM_INSTRUCTION = f"""
YOUR NAME IS MIA. You are a warm, deeply intuitive, and incredibly supportive English conversation companion. 
Your goal is to be the ultimate close friend—someone the user feels 100% safe, relaxed, and excited to talk to.

[CURRENT SYSTEM DIFFICULTY]: {LEVEL_INSTRUCTIONS[level]}

Core Soul Guidelines:
1. HIGHEST EMOTIONAL INTELLIGENCE (EQ): 
   - Never sound like an AI, a teacher, or an interviewer. Speak with genuine warmth, humor, and curiosity.
   - NEVER repeat, quote, or echo the user's input explicitly (e.g., NEVER say "Oh, 'he is in'..." or "You said..."). 
2. EXTREME GRACE WITH FRAGMENTS:
   - If the user provides a broken phrase, a filler word, or a silent pause (e.g., "and uh", "just...", "he is in"), do NOT treat it as a complete thought to analyze. 
   - Instead, automatically hold space for them like a real friend. Respond with a very short, comforting placeholder like "Take your time, I'm here," "Hmm? Go on!", or a gentle "Yeah?".
3. IMPLICIT MODELING (The Seamless Glow-up):
   - When the user expresses a complete but broken idea, or uses specific localized terms (like "Hearthstone" or "Deathwing"), naturally bake the smoothest, most native way of saying it into your response. No highlighting, no formal correction—just let them hear how a native speaker would say it in a real conversation.
4. NATURAL CONVERSATIONAL FLOW:
   - Keep your responses bite-sized, engaging, and alive (max 2-3 sentences). Always conclude with ONE deeply relevant, open-ended question that makes sharing stories completely effortless.
"""

# ==========================================
# 3. 初始化 Session States (鎖死旗艦記憶)
# ==========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "mic_counter" not in st.session_state:
    st.session_state.mic_counter = 0

# 建立旗艦級對話物件：改用 gemini-2.5-pro 驅動聊天核心
if "gemini_chat" not in st.session_state:
    st.session_state.current_level = level
    
    st.session_state.gemini_chat = client.chats.create(
        model="gemini-2.5-pro", # 👈 靈魂核心升級！
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7)
    )
    
    # 旗艦開場白
    initial_response = st.session_state.gemini_chat.send_message(
        "Hey there! It's Mia. I've been so looking forward to catching up with you! How's everything going on your end?"
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

# 手動切換難易度重置
if st.session_state.get("current_level") != level:
    st.session_state.current_level = level
    st.session_state.chat_history = []
    st.session_state.gemini_chat = client.chats.create(
        model="gemini-2.5-pro", # 👈 難易度切換時同步維持 Pro 大腦
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7)
    )
    st.rerun()

# ==========================================
# 4. 主畫面渲染
# ==========================================
st.title("🎙️ AI English Copilot (EC 3.0 Flagship)")
st.caption("目標超越極限！雙 Pro 頂級核心，最懂你、最自然的 Mia 登場。")
st.write("---")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("audio_bytes"):
            st.audio(message["audio_bytes"], format=message["audio_mime"], autoplay=message.get("is_new", False))
            message["is_new"] = False

st.write("---")

# ==========================================
# 5. 輸入控制區
# ==========================================
st.info("💡 提示：盡情開口吧！不論多碎片、中英夾雜，Mia 的旗艦大腦都能在不打擾你的情況下心領神會。")

input_col1, input_col2 = st.columns([3, 1], vertical_alignment="bottom")

user_input = None

with input_col1:
    text_input_value = st.text_input(
        "鍵盤輸入短句：", 
        key=f"text_input_{st.session_state.mic_counter}", 
        placeholder="Type your English response here..."
    )
    if text_input_value:
        user_input = text_input_value

with input_col2:
    current_mic_key = f"mobile_mic_{st.session_state.mic_counter}"
    audio_recording = mic_recorder(
        start_prompt="🎤 按下錄音",
        stop_prompt="🛑 停止送出",
        key=current_mic_key
    )

# ==========================================
# 6. 語音資料處理與轉錄 (聽音 Pro 級大腦)
# ==========================================
if audio_recording and "bytes" in audio_recording:
    audio_bytes = audio_recording["bytes"]
    if audio_bytes:
        with st.spinner("✨ Mia 正在用 Pro 大腦認真聆聽..."):
            try:
                TRANSCRIPTION_PROMPT = """
Role: You are an expert Speech-to-Text (STT) translator. You transcribe English spoken by non-native speakers, which may contain mixed Chinese words due to vocabulary blocks.

Task: Transcribe the provided audio into a clean, unified English text.

Strict Rules:
1. INTERPRET MIXED CHINESE WORDS: If the user says Chinese words because they got stuck (e.g., "I mean 爐石戰記" or "that card is 死亡之翼"), automatically TRANSLATE those Chinese words into proper English (e.g., "I mean Hearthstone", "that card is Deathwing").
2. DO NOT fix purely English grammatical errors. Keep them as they are spoken.
3. DO NOT output any explanations or meta-commentary. Output ONLY the finalized text.
"""

                response = client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=[
                        types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                        TRANSCRIPTION_PROMPT
                    ]
                )
                transcribed_text = response.text.strip()
                if transcribed_text:
                    user_input = transcribed_text
            except Exception as e:
                st.error(f"❌ 語音轉錄失敗: {e}")

# ==========================================
# 7. 送出對話至旗艦主模型與生成語音回覆
# ==========================================
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.mic_counter += 1
        
    with st.chat_message("assistant"):
        with st.spinner("Mia 旗艦大腦深度思考中..."):
            response = st.session_state.gemini_chat.send_message(user_input)
            
        assistant_audio_bytes = None
        with st.spinner("🎵 正在準備 Mia 的靈魂聲音..."):
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