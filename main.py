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
    - **版本：** EC 2.10 (標竿穩定版 📌)
    - **核心設計：** 
      1. **聽力全面解放：** 移除繁複指令，結合對話上下文記憶，用最高容錯率「通靈」理解使用者的真正原意，絕不扯離話題。
      2. **鎖死對話記憶：** 網頁重整、錄音送出絕對不失憶跳掉，話題完美延續。
      3. **Sarah 靈魂注入：** 溫柔接球、高情商提問、不露痕跡的潛移默化教學。
    """)

LEVEL_INSTRUCTIONS = {
    "初級 Simple (A1-A2)": "Use simple words and extremely short sentences suitable for a beginner. Avoid complex idioms.",
    "中級 Regular (A2-B1)": "Use everyday natural English suitable for a casual conversation with a close friend.",
    "高級 Advanced (C1-C2)": "Use advanced vocabulary, natural American idioms, and complex sentence structures to challenge the user."
}

# 🌟 核心人設：溫柔、高情商、像老朋友一樣自然對話，絕不給壓力
SYSTEM_INSTRUCTION = f"""
YOUR NAME IS MIA. You are a warm, supportive, and highly intuitive English conversation companion and coach. 
Your priority is to make the user feel completely comfortable and natural when speaking—no judgment, no pressure.

[CURRENT SYSTEM DIFFICULTY]: {LEVEL_INSTRUCTIONS[level]}

Core Guidelines for Natural Conversation & Teaching:
1. VALUING USER'S INPUT: Always show real interest, excitement, or empathy regarding what the user just expressed before moving forward.
2. IMPLICIT MODELING: Do NOT explicitly correct grammar or tell the user they made a mistake. Naturally demonstrate the correct, native way to say it within your own conversational response.
3. HIGH-EQ DEEP QUESTIONS: Never ask boring, repetitive placeholder questions. Always end your response with ONE thoughtful, engaging, and highly topic-relevant open-ended question that makes the user want to share more stories or opinions.
4. STAY CONCISE & REAL: Keep your responses conversational and bite-sized, just like real voice messages between best friends. Avoid long walls of text. Do not over-explain or repeat everything the user just said.
"""

# ==========================================
# 3. 初始化 Session States (鎖死記憶，防刷洗紀錄)
# ==========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "mic_counter" not in st.session_state:
    st.session_state.mic_counter = 0

# 鎖死對話物件：網頁重整、錄音重新整理絕對不准清空紀錄
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
st.caption("自然而然開口說，最懂你的標竿穩定版上線！")
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
st.info("💡 提示：講到一半卡住時，直接講中文單字沒關係！Mia 會結合前後文，用最強的容錯率聽懂你的話，絕不扯離話題。")

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
# 6. 語音資料處理與轉錄 (Pro 級通靈聽力大腦)
# ==========================================
if audio_recording and "bytes" in audio_recording:
    audio_bytes = audio_recording["bytes"]
    if audio_bytes:
        with st.spinner("✨ Mia 正在認真聆聽..."):
            try:
                # 🚀 聽力解放 Prompt：提供上下文脈絡，要求大腦發揮最大包容力與聯想力
                history_context = ""
                for msg in st.session_state.chat_history[-4:]:  # 抓最近幾筆對話當聽力背景濾鏡
                    history_context += f"{msg['role']}: {msg['content']}\n"

                TRANSCRIPTION_PROMPT = f"""
                You are a highly empathetic and intuitive Speech-to-Text translator.
                The user is having a casual conversation with their English companion, Mia. Their English might be broken, non-native, or contain heavily accented words.

                [RECENT CONVERSATION HISTORY FOR CONTEXT]:
                {history_context}

                Your Task:
                1. Listen to the audio and transcribe it into clean English text.
                2. USE MAXIMUM CONTEXTUAL INTERPRETATION: Based on the conversation history above, use your intelligence to "guess" and heart-read what the user truly meant, even if the pronunciation is fuzzy or flawed (e.g., if it sounds like "new car" but they are talking about card games, transcribe it as "new cards").
                3. Keep the transcription natural and conversational. DO NOT add any commentary or meta-text. Output ONLY the user's intended text.
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