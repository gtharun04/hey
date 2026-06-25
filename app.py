"""
AI Agent Buddy — Cloud-Local Hybrid Assistant
==============================================

Setup:
  1. pip install -r requirements.txt
  2. export GROQ_API_KEY="your_groq_api_key_here"
  3. streamlit run app.py

Get a free API key at https://console.groq.com/
Default model: llama-3.3-70b-versatile (replacement for deprecated llama3-70b-8192)
"""

from __future__ import annotations

import html
import json

import streamlit as st
import streamlit.components.v1 as components

from agent import AIBuddy, DEFAULT_MODEL

# ---------------------------------------------------------------------------
# Page config & dark theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Agent Buddy",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

PASTEL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fb 0%, #eef2f7 100%);
        color: #334155;
    }
    
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { display: none; }
    
    .buddy-header {
        text-align: center;
        padding: 1.5rem 0 1rem;
    }
    
    .buddy-header h1 {
        font-size: clamp(1.8rem, 5vw, 2.4rem);
        font-weight: 700;
        background: linear-gradient(90deg, #8b5cf6, #0d9488);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    
    .buddy-header p {
        color: #64748b;
        font-size: clamp(0.9rem, 2.5vw, 1.05rem);
        font-weight: 500;
    }
    
    [data-testid="stChatMessage"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border-radius: 20px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 0.75rem;
        color: #1e293b !important;
    }
    
    [data-testid="stChatMessage"][data-testid*="user"] {
        background: #f3f0ff !important;
        border-color: #e9e3ff !important;
        color: #4c1d95 !important;
    }
    
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] div {
        color: inherit !important;
        font-size: 0.96rem;
        line-height: 1.5;
    }
    
    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
        border-radius: 24px !important;
        box-shadow: 0 4px 12px -2px rgba(0,0,0,0.05) !important;
        font-size: 0.95rem !important;
    }
    
    [data-testid="stChatInput"] textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15) !important;
    }
    
    .voice-panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 0.75rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    div[data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Sidebar text colors */
    div[data-testid="stSidebar"] h3 {
        color: #1e293b !important;
        font-weight: 600;
        font-size: 1.15rem;
    }
    
    div[data-testid="stSidebar"] p, div[data-testid="stSidebar"] span {
        color: #475569 !important;
        font-size: 0.9rem;
    }
    
    /* Custom style for streamlit buttons inside columns */
    div[data-testid="stSidebar"] button {
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
        color: #ef4444 !important;
        padding: 2px 6px !important;
        font-size: 0.8rem !important;
        transition: all 0.2s;
    }
    
    div[data-testid="stSidebar"] button:hover {
        background-color: #fef2f2 !important;
        border-color: #fee2e2 !important;
        transform: scale(1.05);
    }

    @media (max-width: 640px) {
        [data-testid="stChatMessage"] {
            padding: 0.65rem 0.85rem !important;
            margin-bottom: 0.5rem !important;
            border-radius: 16px !important;
        }
        .buddy-header {
            padding: 0.75rem 0 !important;
        }
    }
</style>
"""
st.markdown(PASTEL_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "buddy" not in st.session_state:
    try:
        st.session_state.buddy = AIBuddy()
    except ValueError as exc:
        st.session_state.buddy = None
        st.session_state.buddy_error = str(exc)
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""
if "pending_voice" not in st.session_state:
    st.session_state.pending_voice = ""

# Voice input via query param (set by embedded JS component)
if "voice" in st.query_params:
    _voice_param = st.query_params["voice"]
    if _voice_param:
        st.session_state.pending_voice = _voice_param
    del st.query_params["voice"]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="buddy-header">
        <h1>🤖 AI Agent Buddy</h1>
        <p>Cloud brain · Local memory · Voice enabled</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — memory & controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧠 Memory Bank")
    if st.session_state.buddy:
        facts = st.session_state.buddy.load_facts()
        if facts:
            st.markdown("What I remember about you (click ❌ to delete):")
            for i, fact in enumerate(facts):
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(
                        f'<div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 10px; font-size: 0.82rem; color: #475569; line-height: 1.3; margin-bottom: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">{html.escape(fact)}</div>',
                        unsafe_allow_html=True
                    )
                with col2:
                    if st.button("❌", key=f"del_{i}", help="Delete this fact", use_container_width=True):
                        st.session_state.buddy.delete_fact(fact)
                        st.rerun()
        else:
            st.caption("No personal facts saved yet. Tell me about yourself!")
        st.markdown("---")
        st.caption(f"Model: `{DEFAULT_MODEL}`")
    else:
        st.error("Buddy offline — set GROQ_API_KEY")

    if st.button("Clear chat history", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.buddy:
            st.session_state.buddy.clear_history()
        st.session_state.last_spoken = ""
        st.rerun()

# ---------------------------------------------------------------------------
# API key guard
# ---------------------------------------------------------------------------
if not st.session_state.buddy:
    st.error(st.session_state.get("buddy_error", "GROQ_API_KEY is not configured."))
    st.code("export GROQ_API_KEY='your_key_here'\nstreamlit run app.py", language="bash")
    st.stop()

buddy: AIBuddy = st.session_state.buddy

# ---------------------------------------------------------------------------
# Voice input component (Web Speech API — SpeechRecognition)
# ---------------------------------------------------------------------------
st.markdown('<div class="voice-panel">', unsafe_allow_html=True)
components.html(
    """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background: transparent;
    color: #475569;
    padding: 8px 12px;
  }
  .row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
  #speakBtn {
    flex: 1;
    min-width: 140px;
    padding: 12px 20px;
    border: none;
    border-radius: 999px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    background: linear-gradient(135deg, #a78bfa, #8b5cf6);
    color: white;
    box-shadow: 0 4px 6px -1px rgba(139, 92, 246, 0.2);
    transition: transform 0.15s, box-shadow 0.15s;
    touch-action: manipulation;
  }
  #speakBtn:active { transform: scale(0.97); }
  #speakBtn.listening {
    background: linear-gradient(135deg, #f87171, #ef4444);
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.4);
    animation: pulse 1.2s infinite;
  }
  @keyframes pulse {
    0%, 100% { box-shadow: 0 0 12px rgba(239, 68, 68, 0.3); }
    50% { box-shadow: 0 0 24px rgba(239, 68, 68, 0.5); }
  }
  #sendVoice {
    padding: 12px 18px;
    border: 1px solid #99f6e4;
    border-radius: 999px;
    background: #f0fdfa;
    color: #0d9488;
    font-weight: 600;
    cursor: pointer;
    display: none;
    touch-action: manipulation;
    transition: all 0.2s;
  }
  #sendVoice:hover {
    background: #ccfbfe;
  }
  #status {
    width: 100%;
    font-size: 0.85rem;
    color: #64748b;
    min-height: 1.2em;
    margin-top: 8px;
    font-weight: 500;
  }
  #transcript {
    width: 100%;
    margin-top: 8px;
    padding: 10px 14px;
    border-radius: 12px;
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    color: #334155;
    font-size: 0.92rem;
    font-family: inherit;
    display: none;
    resize: none;
  }
</style>
</head>
<body>
  <div class="row">
    <button id="speakBtn" type="button">🎤 Tap to Speak</button>
    <button id="sendVoice" type="button">Send voice →</button>
  </div>
  <textarea id="transcript" rows="2" placeholder="Your speech will appear here…" readonly></textarea>
  <div id="status">Tap the mic and speak — works best in Chrome/Edge on HTTPS or localhost.</div>

  <script>
    const speakBtn = document.getElementById('speakBtn');
    const sendBtn = document.getElementById('sendVoice');
    const statusEl = document.getElementById('status');
    const transcriptEl = document.getElementById('transcript');
    let recognition = null;
    let finalText = '';

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      statusEl.textContent = 'Speech recognition not supported in this browser. Use Chrome or Edge.';
      speakBtn.disabled = true;
    } else {
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        speakBtn.classList.add('listening');
        speakBtn.textContent = '🔴 Listening…';
        statusEl.textContent = 'Speak now…';
        finalText = '';
      };

      recognition.onresult = (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const t = event.results[i][0].transcript;
          if (event.results[i].isFinal) finalText += t;
          else interim += t;
        }
        const display = (finalText + interim).trim();
        if (display) {
          transcriptEl.style.display = 'block';
          transcriptEl.value = display;
          sendBtn.style.display = 'inline-block';
        }
      };

      recognition.onerror = (e) => {
        statusEl.textContent = 'Error: ' + (e.error || 'unknown');
        resetBtn();
      };

      recognition.onend = () => {
        resetBtn();
        if (finalText.trim()) {
          statusEl.textContent = 'Got it! Tap "Send voice" or speak again.';
        }
      };

      function resetBtn() {
        speakBtn.classList.remove('listening');
        speakBtn.textContent = '🎤 Tap to Speak';
      }

      speakBtn.addEventListener('click', () => {
        if (recognition) {
          try { recognition.start(); } catch (_) { recognition.stop(); recognition.start(); }
        }
      });

      sendBtn.addEventListener('click', () => {
        const text = (finalText || transcriptEl.value).trim();
        if (!text) return;
        try {
          speakBtn.disabled = true;
          sendBtn.disabled = true;
          statusEl.textContent = 'Sending voice message to buddy...';
          const top = window.parent.location;
          const url = new URL(top.href);
          url.searchParams.set('voice', text);
          top.href = url.toString();
        } catch (_) {
          statusEl.textContent = 'Could not send — type in the chat box instead.';
          speakBtn.disabled = false;
          sendBtn.disabled = false;
        }
      });
    }
  </script>
</body>
</html>
    """,
    height=130,
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chat history display
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])
        if msg.get("saved_facts"):
            st.caption("💾 Saved to memory: " + ", ".join(msg["saved_facts"]))

# ---------------------------------------------------------------------------
# Process voice or typed input
# ---------------------------------------------------------------------------
def handle_user_message(prompt: str) -> None:
    prompt = prompt.strip()
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking…"):
        result = buddy.chat(prompt)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["reply"],
            "saved_facts": result["saved_facts"],
        }
    )
    st.session_state.last_spoken = result["reply"]


if st.session_state.pending_voice:
    voice_text = st.session_state.pending_voice
    st.session_state.pending_voice = ""
    handle_user_message(voice_text)
    st.rerun()

if prompt := st.chat_input("Message your buddy…"):
    handle_user_message(prompt)
    st.rerun()

# ---------------------------------------------------------------------------
# Text-to-Speech for latest assistant reply (Web Speech API — SpeechSynthesis)
# ---------------------------------------------------------------------------
if st.session_state.last_spoken:
    tts_text = json.dumps(st.session_state.last_spoken)
    components.html(
        f"""
<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:transparent;">
<script>
(function() {{
  const text = {tts_text};
  if (!text || !window.speechSynthesis) return;

  function speak() {{
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.0;
    u.pitch = 1.0;
    u.lang = 'en-US';
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google'))
      || voices.find(v => v.lang.startsWith('en'));
    if (preferred) u.voice = preferred;
    window.speechSynthesis.speak(u);
  }}

  if (window.speechSynthesis.getVoices().length) speak();
  else window.speechSynthesis.onvoiceschanged = speak;
}})();
</script>
</body></html>
        """,
        height=0,
    )
    st.session_state.last_spoken = ""
