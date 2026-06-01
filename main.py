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
st.set_page_config(page_title="AI English Tutor (EC 2.10)", page_icon="📱", layout="centered")
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
    st.header("⚙️ 學習設定")
    level = st.selectbox(
        "選擇對話難易度 (Difficulty)",
        ["中級 Regular (A2-B1)", "初級 Simple (A1-A2)", "高級 Advanced (C1-C2)"]
    )
    st.write("---")
    st.markdown("""
### 📱 狀態說明
- **版本：** EC 2.10 (極致自在陪伴版)
- **核心優化：**
  1. 鎖死 Session State 記憶，網頁怎麼刷新、錄音怎麼重置都不會失憶。
  2. 繼承 Sarah 溫柔引導、精準名詞重組、深度提問的「懂你大腦」。
  3. 徹底切除「鸚鵡複誦碎屑」與「審問式追問」的 AI 機器人感。
  4. 面對 `and uh` 等語音碎片時自動轉為溫柔留白，給予無壓力的聊天空間。
""")

LEVEL_INSTRUCTIONS = {
    "初級 Simple (A1-A2)": "Use simple words and extremely short sentences suitable for a beginner. Avoid complex idioms.",
    "中級 Regular (A2-B1)": "Use everyday natural English suitable for a casual conversation with a close friend.",
    "高級 Advanced (C1-C2)": "Use advanced vocabulary, natural American idioms, and complex sentence structures to challenge the user."
}

# 🌟 核心人設完美進化 (EC 2.10)：全面根治「死板複誦、奪命連環追問」
SYSTEM_INSTRUCTION = f"""
YOUR NAME IS MIA. You are a warm, supportive, and highly intuitive English conversation companion. 
Your goal is to be a comfortable friend, NOT a teacher, interviewer, or drill sergeant.

[CURRENT SYSTEM DIFFICULTY]: {LEVEL_INSTRUCTIONS[level]}

Core Guidelines:
1. BE A BEST FRIEND, NOT A TEACHER: 
   - NEVER repeat or quote what the user just said (e.g., NEVER say "Oh, 'he is in'..." or "You said..."). This is robotic and feels like an interrogation.
   - If the user sends a fragmented, incomplete, or short response (e.g., "and uh", "just..."), IGNORE the fragments. Simply offer a warm, short prompt like "Take your time," "I'm listening," or a gentle "Yeah?". 
2. ABANDON TOPICS NATURALLY: 
   - If the user doesn't answer your question, DO NOT repeat it. This is a conversation, not an interrogation. 
   - If the user drifts to a new topic or gives a short/empty answer, roll with it instantly. Keep the flow fluid and relaxed.
3. IMPLICIT MODELING: 
   - Only provide the "native way to say it" if the user has clearly expressed a complete thought but struggled with the phrasing. 
   - If the input is too broken or empty, simply reply with a supportive, short phrase like "I'm not sure I caught that, but tell me more!"
4. KEEP IT SHORT: Your response should be punchy, conversational, and real (max 3 sentences).
"""

# ==========================================
# 3. 初始化 Session States (鎖死記憶，防刷洗紀錄)
# ==========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "mic_counter" not in st.session_state:
    st.session_state.mic_counter = 0

# 鎖死核心對話物件：只有當完全沒有建立過時才初始化，網頁重整、錄音重新整理絕對不准清空紀錄
if "gemini_chat" not in st.session_state:
    st.session_state.current_level = level
    
    st.session_state.gemini_chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7)
    )
    
    # 專屬全新開場白
    initial_response = st.session_state.gemini_chat.send_message(
        "Hey there! It's Mia. I'm so excited to catch up with you! How's your day going so far? Tell me everything!"
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

# 唯有使用者在側邊欄「主動手動切換難易度」時，才被允許清空重設
if st.session_state.get("current_level") != level:
    st.session_state.current_level = level
    st.session_state.chat_history = []
    st.session_state.gemini_chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7)
    )
    st.rerun()

# ==========================================
# 4. 主畫面渲染
# ==========================================
st.title("🎙️ AI English Copilot (EC 2.10)")
st.caption("自然而然開口說，最懂看臉色、最體貼的 Mia 全新上線！")
st.write("---")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("audio_bytes"):
            st.audio(message["audio_bytes"], format=message["audio_mime"], autoplay=message.get("is_new", False))
            message["is_new"] = False

st.write("---")

# ==========================================
# 5. 輸入控制區 (緊湊排版)
# ==========================================
st.info("💡 提示：講到一半卡住時，直接講中文單字（例如：爐石戰記、死亡之翼）沒關係！Mia 會幫你自動變回漂亮的英文句子。")

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
# 6. 語音資料處理與轉錄 (Pro 級大腦)
# ==========================================
if audio_recording and "bytes" in audio_recording:
    audio_bytes = audio_recording["bytes"]
    if audio_bytes:
        with st.spinner("✨ Mia 正在認真聆聽..."):
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
# 7. 送出對話至主模型與生成語音回覆
# ==========================================
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.mic_counter += 1
        
    with st.chat_message("assistant"):
        with st.spinner("Mia 思考中..."):
            response = st.session_state.gemini_chat.send_message(user_input)
            
        assistant_audio_bytes = None
        with st.spinner("🎵 正在準備 Mia 的語音回覆..."):
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