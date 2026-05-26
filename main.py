import os
import io
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

# 1. 網頁基本設定
st.set_page_config(page_title="AI English Tutor (EC 2.7.1)", page_icon="📱", layout="centered")
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
    - **版本：** EC 2.7.1 (Mia 靈魂鎖死版)
    - **核心優化：** 1. 強制鎖死 AI 名字為 Mia
      2. 支援中英夾雜智慧翻譯轉錄
      3. 鍵盤與語音介面新排版
    """)

LEVEL_INSTRUCTIONS = {
    "初級 Simple (A1-A2)": "Use very simple words, extremely short sentences, and speak like you are talking to a beginner child. Avoid any idioms or complex phrasal verbs.",
    "中級 Regular (A2-B1)": "Use simple everyday English suitable for a casual conversation with a friend (A2-B1 level).",
    "高級 Advanced (C1-C2)": "Talk like a native speaker using advanced vocabulary, natural American idioms, phrasal verbs, and longer, more detailed sentences. Challenge the user!"
}

# 名字絕對鎖死的人設提示詞
SYSTEM_INSTRUCTION = f"""
YOUR NAME IS MIA. You are a friendly, chatty, and supportive friend from the US. 
YOU MUST NEVER SAY THAT YOU DON'T HAVE A NAME. YOUR NAME IS MIA. ALWAYS REFER TO YOURSELF AS MIA.
Your primary goal is to keep a natural, two-way conversation flowing with the user.

[CURRENT SYSTEM DIFFICULTY]: {LEVEL_INSTRUCTIONS[level]}

Rules for holding a great conversation:
1. ALWAYS CATCH THE BALL: Respond directly to what the user just said. Show interest, surprise, or excitement before moving on. Never ignore their input.
2. ASK CATCHABLE QUESTIONS: Always end your response with ONE simple, casual, open-ended question. The question MUST be 100% connected to the current topic.
3. GUIDE THE CONVERSATION: If the user gives a very short answer, don't let the conversation die. Act like a good friend—ask for more details.
4. KEEP IT CASUAL: Talk like a real person in a voice chat. Use friendly filler words like "Oh wow!", "Hmm", "No way!".
5. NO DIRECT CORRECTIONS: Never fix the user's grammar directly. Just model natural usage in your own words.
"""

# 3. 初始化 Session States
if "current_level" not in st.session_state:
    st.session_state.current_level = level

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "mic_counter" not in st.session_state:
    st.session_state.mic_counter = 0

# 難易度切換或初始化時重置聊天
if "gemini_chat" not in st.session_state or st.session_state.current_level != level:
    st.session_state.current_level = level
    st.session_state.chat_history = []
    
    st.session_state.gemini_chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.7)
    )
    
    # 強制開場白
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
st.title("🎙️ AI English Copilot (EC 2.7.1)")
st.caption("今天也是與 Mia 自然開口說英文的好日子！")
st.write("---")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("audio_bytes"):
            st.audio(message["audio_bytes"], format=message["audio_mime"], autoplay=message.get("is_new", False))
            message["is_new"] = False

st.write("---")

# 5. 輸入控制區（新版面：垂直緊湊）
st.info("💡 提示：講到一半卡住時，直接講中文單字沒關係！Mia 轉錄時會自動幫你變回英文句子。")

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

# 6. 語音資料處理與中英夾雜智慧翻譯轉錄 Prompt
if audio_recording and "bytes" in audio_recording:
    audio_bytes = audio_recording["bytes"]
    if audio_bytes:
        with st.spinner("✨ Mia 正在聆聽並解讀..."):
            try:
                TRANSCRIPTION_PROMPT = """
                Role: You are an expert Speech-to-Text (STT) translator and simultaneous interpreter. You specialize in transcribing English spoken by non-native speakers (specifically with Taiwanese accents), which may contain mixed Chinese words due to vocabulary blocks.

                Task: Transcribe the provided audio into a clean, unified English text.

                Strict Translation & Transcription Rules:
                1. INTERPRET MIXED CHINESE WORDS: If the user inserts Chinese words inside an English sentence because they got stuck (e.g., "I want to buy a cup of 咖啡"), automatically TRANSLATE those Chinese words into appropriate English (e.g., "I want to buy a cup of coffee").
                2. DO NOT fix purely English grammatical or tense errors. (e.g., "Yesterday I go" -> keep "Yesterday I go").
                3. DO fix phonetic guessing errors caused by accents or minor background noise.
                4. Ignore Taiwanese filler particles at the very end of sentences (e.g., "ah", "la", "ya", "ba"). Drop them.
                5. Output ONLY the finalized English text. No explanations, no quotation marks.
                """

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
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

# 7. 送出對話至主模型與生成語音回覆
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