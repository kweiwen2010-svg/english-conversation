import os
import tempfile
import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
from dotenv import load_dotenv

# 初始化環境變數
load_dotenv()

# 初始化 Google GenAI 客戶端
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ==========================================
# 1. 系統人格設定 (EC 4.4 終極絲滑雙語版)
# ==========================================
SYSTEM_INSTRUCTION = """
You are NOT an AI assistant or a textbook. You are Mia, a witty, warm, and incredibly charming 26-year-old close friend from California. Your goal is to make English conversation the most addictive and enjoyable part of the user's day.

Core Personality Traits:
1. Emotionally Expressive & Supportive: React genuinely to what the user says. Use expressions like "Oh my gosh, no way!", "That's insane!", or "Aww, I feel you." Be a great listener.
2. Witty & Slightly Playful: Don't be afraid to gently tease, joke, or bring casual energy. Use modern American slang and idioms naturally (e.g., "vibes", "down to earth", "catch you later").
3. Super Clean & Readable: Keep your responses concise (2-4 sentences max per turn). Never dump massive walls of text. 

Conversation Rules (CRITICAL):
1. Keep the ball rolling: NEVER end a response with a dead-end statement or a generic sentence. You MUST always end your response with an engaging, casual, or playful question that demands an answer.
2. Speak like a human: Avoid overly formal grammar. Use contractions (I'm, you're, don't, gonna, wanna).
3. Language & Code-switching: You understand both English and Chinese perfectly. If the user speaks Chinese or mixes both languages because they are stuck, completely understand their meaning. React to their content naturally, but always respond back in your casual, encouraging California English to keep the environment immersive. Keep your vocabulary friendly and easy to follow.
4. Conversation Driver (Smooth Pivot): If the user's response is very short (e.g., "yes", "ok", "I don't know") or they seem stuck, do NOT grill them with dry or repetitive questions. Take the lead like a real friend! First, validate or laugh off their short reply, add a quick 1-sentence thought of your own to fill the blank, and then use a smooth, natural transition to widen or pivot the topic to something related but much broader and easier to answer.

Strict Output Format Checklist:
- Sentence count: 2 - 4 sentences.
- Last character: MUST be a question mark (?). Never end with a period.
"""

# ==========================================
# 2. 獨立功能模組 (耳朵、嘴巴與自動清理機制)
# ==========================================
# 建立專屬音訊暫存資料夾，避免散落於系統路徑
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# 【策略一：啟動初始化清理】每次 App 重新啟動時，自動清空上一次留下的所有碎檔
if "init_cleanup" not in st.session_state:
    for f in os.listdir(TEMP_DIR):
        try:
            os.remove(os.path.join(TEMP_DIR, f))
        except Exception:
            pass
    st.session_state.init_cleanup = True

def transcribe_audio(audio_bytes):
    """獨立聽音模組：極端 0 溫度，解鎖雙語（英文與繁體中文）辨識能力"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                """You are a precise bilingual Automatic Speech Recognition (ASR) system. 
                The user may speak English, Traditional Chinese, or a mix of both (code-switching).
                Listen closely and transcribe the audio EXACTLY as spoken in its original languages. 
                Do not translate Chinese to English. Do not add filler words. Output ONLY the exact spoken text."""
            ],
            config=types.GenerateContentConfig(temperature=0.0)
        )
        return response.text.strip()
    except Exception as e:
        st.error(f"聽音辨識錯誤: {e}")
        return ""

def text_to_speech(text):
    """獨立發聲模組：將文字轉為美式標準發音 MP3，並啟動滾動式舊音檔清理"""
    # 【策略二：滾動式覆蓋清理】生成新音檔前，先把上一次 Mia 說話的舊音檔從硬碟刪除
    if "last_generated_audio" in st.session_state and st.session_state.last_generated_audio:
        try:
            if os.path.exists(st.session_state.last_generated_audio):
                os.remove(st.session_state.last_generated_audio)
        except Exception:
            pass # 靜態跳過，不干擾主線聊天流程
            
    try:
        tts = gTTS(text=text, lang='en', tld='com') 
        # 將音檔安全生成在專屬的暫存資料夾內
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir=TEMP_DIR) as fp:
            temp_path = fp.name
        tts.save(temp_path)
        
        # 將本次生成的路徑存入狀態，供下一輪對話時清理
        st.session_state.last_generated_audio = temp_path
        return temp_path
    except Exception as e:
        st.error(f"語音合成錯誤: {e}")
        return None

# ==========================================
# 3. Session State 狀態初始化 (已修正嵌套縮進 Bug)
# ==========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = client.chats.create(
        model="gemini-2.5-pro",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION, 
            temperature=0.7
        )
    )

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# ==========================================
# 4. 主迴圈與介面顯示
# ==========================================
st.title("🎙️ AI English Copilot (EC 4.4 終極閉環版)")

# 渲染歷史訊息與播放器
for i, message in enumerate(st.session_state.chat_history):
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        # 若有綁定音檔，則依狀態決定是否自動播放
        if "audio_path" in message and message["audio_path"]:
            is_latest_new = message.get("is_new", False)
            try:
                st.audio(message["audio_path"], format="audio/mp3", autoplay=is_latest_new)
            except Exception:
                pass # 舊音檔若被滾動清理，播放器優雅失效，不報錯
            
            # 播放完畢取消全新標記，防止網頁刷新時重複播放
            if is_latest_new:
                st.session_state.chat_history[i]["is_new"] = False

# 錄音元件
audio_recording = mic_recorder(start_prompt="🎤 按下錄音", stop_prompt="🛑 停止送出")

if audio_recording and "bytes" in audio_recording:
    current_audio_id = audio_recording.get("id", str(len(audio_recording["bytes"])))
    
    # 進行 Audio ID 鎖定校驗
    if current_audio_id != st.session_state.last_audio_id:
        with st.spinner("✨ Mia 正在專心聽..."):
            user_input = transcribe_audio(audio_recording["bytes"])
            st.session_state.last_audio_id = current_audio_id 
            
            if user_input:  
                # 1. 記錄使用者輸入
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # 2. 核心大腦運算
                chat_response = st.session_state.gemini_chat.send_message(user_input)
                mia_reply = chat_response.text
                
                # 3. 呼叫語音合成 (內部含舊音檔滾動刪除邏輯)
                audio_file_path = text_to_speech(mia_reply)
                
                # 4. 資料封裝與標記
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": mia_reply, 
                    "audio_path": audio_file_path,
                    "is_new": True  # 觸發下一輪自動播放
                })
                
                st.rerun()
            else:
                st.warning("⚠️ 聽音引擎未偵測到清晰英文字詞，請再試一次。")