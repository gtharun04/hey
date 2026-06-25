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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Remove Streamlit default main body extra padding */
    [data-testid="block-container"] {
        padding: 1.5rem 1rem !important;
        max-width: 44rem !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fb 0%, #eef2f7 100%);
        color: #334155;
    }
    
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { display: none; }
    
    .buddy-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem;
    }
    
    .buddy-header h1 {
        font-size: clamp(1.8rem, 4.5vw, 2.3rem);
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #7c3aed, #8b5cf6, #3b82f6, #0d9488);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: textShimmer 5s linear infinite;
        margin-bottom: 0.15rem;
    }
    
    @keyframes textShimmer {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .buddy-header p {
        color: #64748b;
        font-size: clamp(0.85rem, 2.5vw, 0.95rem);
        font-weight: 500;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Make chat input blend in transparently */
    [data-testid="stChatInput"] {
        background: transparent !important;
        padding-bottom: 2rem !important;
    }
    
    [data-testid="stChatInput"] textarea {
        background: rgba(255, 255, 255, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        color: #1e293b !important;
        border-radius: 20px !important;
        backdrop-filter: blur(10px);
        font-size: 0.92rem !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
    }
    
    [data-testid="stChatInput"] textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.1) !important;
    }
    
    .voice-panel {
        background: transparent;
        border: none;
        padding: 0;
        margin-bottom: 0.5rem;
        box-shadow: none;
        display: flex;
        justify-content: center;
        width: 100%;
    }
    
    div[data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Sidebar text colors */
    div[data-testid="stSidebar"] h3 {
        color: #1e293b !important;
        font-weight: 600;
        font-size: 1.05rem;
    }
    
    div[data-testid="stSidebar"] p, div[data-testid="stSidebar"] span {
        color: #475569 !important;
        font-size: 0.85rem;
    }
    
    /* Custom style for streamlit buttons inside columns */
    div[data-testid="stSidebar"] button {
        border-radius: 6px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
        color: #ef4444 !important;
        padding: 1px 4px !important;
        font-size: 0.75rem !important;
        transition: all 0.2s;
    }
    
    div[data-testid="stSidebar"] button:hover {
        background-color: #fef2f2 !important;
        border-color: #fee2e2 !important;
    }

    /* Siri-like borderless visual container */
    .siri-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 1rem 0;
        margin-top: 0.5rem;
        text-align: center;
        width: 100%;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    .siri-user-query {
        font-size: 1.15rem;
        color: #8b5cf6;
        font-style: italic;
        font-weight: 500;
        margin-bottom: 1.25rem;
        max-width: 85%;
        opacity: 0.85;
        animation: fadeIn 0.4s ease-out;
    }
    
    .siri-assistant-reply {
        font-size: 1.6rem;
        color: #1e293b;
        font-weight: 700;
        line-height: 1.45;
        max-width: 90%;
        margin-bottom: 0.5rem;
        animation: fadeIn 0.6s ease-out;
    }
    
    .siri-memory-tag {
        font-size: 0.75rem;
        color: #0d9488;
        background: rgba(13, 148, 136, 0.08);
        border: 1px solid rgba(13, 148, 136, 0.2);
        border-radius: 99px;
        padding: 4px 12px;
        margin-top: 0.75rem;
        display: inline-block;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 640px) {
        .buddy-header {
            padding: 0.5rem 0 !important;
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
        <p><span style="display:inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; margin-right: 6px; box-shadow: 0 0 8px #10b981; animation: siriDotPulse 2s infinite;"></span>Cloud brain · Local memory · Voice enabled</p>
    </div>
    <style>
        @keyframes siriDotPulse {
            0% { opacity: 0.4; }
            50% { opacity: 1; }
            100% { opacity: 0.4; }
        }
    </style>
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
            with st.expander("Click to view/manage facts", expanded=False):
                for i, fact in enumerate(facts):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(
                            f'<div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 5px 8px; font-size: 0.78rem; color: #475569; line-height: 1.25; margin-bottom: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.01);">{html.escape(fact)}</div>',
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
# -------------------------------------------------------st.markdown('<div class="voice-panel">', unsafe_allow_html=True)
st.markdown('<div class="voice-panel">', unsafe_allow_html=True)
components.html(
    """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background: transparent;
    color: #475569;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .row { 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    width: 100%; 
  }
  #speakBtn {
    width: 80px;
    height: 80px;
    border: none;
    border-radius: 50%;
    font-size: 0rem;
    cursor: pointer;
    background: linear-gradient(135deg, #a78bfa, #8b5cf6, #60a5fa, #38bdf8);
    background-size: 300% 300%;
    color: white;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.25), 0 0 20px rgba(96, 165, 250, 0.15);
    transition: box-shadow 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    outline: none;
    position: relative;
    animation: gradientShift 6s ease infinite;
    touch-action: manipulation;
  }
  #speakBtn::before {
    content: "";
    position: absolute;
    top: -4px; left: -4px; right: -4px; bottom: -4px;
    border-radius: 50%;
    background: linear-gradient(135deg, #a78bfa, #8b5cf6, #60a5fa, #38bdf8);
    z-index: -1;
    opacity: 0.4;
    transition: all 0.3s ease;
  }
  #speakBtn::after {
    content: "🎤";
    font-size: 2rem;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
  }
  #speakBtn.listening {
    animation: gradientShift 2s ease infinite;
    box-shadow: 0 0 35px rgba(139, 92, 246, 0.4), 0 0 50px rgba(96, 165, 250, 0.25);
  }
  #speakBtn.listening::before {
    animation: siriRing 1.5s infinite cubic-bezier(0.25, 0, 0, 1);
    opacity: 0.8;
  }
  #speakBtn.listening::after {
    content: "⚡";
    font-size: 1.8rem;
    animation: spinIcon 3s linear infinite;
  }
  @keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  @keyframes siriRing {
    0% { transform: scale(1); opacity: 0.8; }
    100% { transform: scale(1.45); opacity: 0; }
  }
  @keyframes spinIcon {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  #status {
    width: 100%;
    font-size: 0.8rem;
    color: #64748b;
    text-align: center;
    margin-top: 8px;
    font-weight: 500;
  }
  #transcript {
    width: 100%;
    margin-top: 8px;
    padding: 0;
    border: none;
    background: transparent;
    color: #8b5cf6;
    font-size: 1.15rem;
    font-style: italic;
    font-weight: 500;
    display: none;
    line-height: 1.4;
    text-align: center;
    box-shadow: none;
  }
  
  /* Bouncing voice bars inside STT element */
  #wave-container {
    display: none;
    justify-content: center;
    align-items: center;
    gap: 3px;
    margin-top: 8px;
    height: 16px;
  }
  .bar {
    width: 3px;
    height: 5px;
    background: #8b5cf6;
    border-radius: 99px;
  }
</style>
</head>
<body>
  <div class="row">
    <button id="speakBtn" type="button">Tap to Speak</button>
  </div>
  <div id="wave-container">
    <div class="bar" style="background:#8b5cf6"></div>
    <div class="bar" style="background:#a78bfa"></div>
    <div class="bar" style="background:#60a5fa"></div>
    <div class="bar" style="background:#38bdf8"></div>
    <div class="bar" style="background:#0d9488"></div>
  </div>
  <div id="status">Tap the microphone to speak</div>
  <div id="transcript"></div>

  <script>
    const speakBtn = document.getElementById('speakBtn');
    const statusEl = document.getElementById('status');
    const transcriptEl = document.getElementById('transcript');
    const waveContainer = document.getElementById('wave-container');
    let recognition = null;
    let finalText = '';
    let waveTimeline = null;

    // Hover magnetic animation with GSAP
    speakBtn.addEventListener('mouseenter', () => {
      if (!speakBtn.classList.contains('listening')) {
        gsap.to(speakBtn, { scale: 1.08, duration: 0.3, ease: "power2.out" });
      }
    });
    speakBtn.addEventListener('mouseleave', () => {
      if (!speakBtn.classList.contains('listening')) {
        gsap.to(speakBtn, { scale: 1, duration: 0.3, ease: "power2.out" });
      }
    });

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      statusEl.textContent = 'Speech recognition not supported in this browser. Use Chrome or Edge.';
      speakBtn.disabled = true;
    } else {
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      // GSAP wave animation helper
      function initWaveAnimation() {
        waveTimeline = gsap.timeline({ repeat: -1 });
        gsap.utils.toArray('.bar').forEach((bar, i) => {
          waveTimeline.to(bar, {
            height: 18,
            duration: 0.4 + (i * 0.05),
            ease: "sine.inOut",
            repeat: -1,
            yoyo: true
          }, 0);
        });
        waveTimeline.pause();
      }
      initWaveAnimation();

      recognition.onstart = () => {
        speakBtn.classList.add('listening');
        
        // GSAP transition for listening start
        gsap.to(speakBtn, { scale: 1.15, duration: 0.5, ease: "elastic.out(1, 0.3)" });
        gsap.fromTo(statusEl, { opacity: 0, y: 5 }, { opacity: 1, y: 0, duration: 0.3 });
        
        statusEl.textContent = 'Listening...';
        transcriptEl.style.display = 'none';
        waveContainer.style.display = 'flex';
        
        if (waveTimeline) {
          waveTimeline.play();
        }
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
          if (transcriptEl.style.display === 'none') {
            transcriptEl.style.display = 'block';
            gsap.fromTo(transcriptEl, { opacity: 0, scale: 0.95 }, { opacity: 1, scale: 1, duration: 0.3, ease: "power2.out" });
          }
          transcriptEl.textContent = display;
        }
      };

      recognition.onerror = (e) => {
        statusEl.textContent = 'Error: ' + (e.error || 'unknown');
        resetBtn();
      };

      recognition.onend = () => {
        resetBtn();
        const text = (finalText || transcriptEl.textContent).trim();
        if (text) {
          statusEl.textContent = 'Sending message to buddy...';
          sendVoiceMessage(text);
        } else {
          statusEl.textContent = 'Tap the microphone to speak';
        }
      };

      function resetBtn() {
        speakBtn.classList.remove('listening');
        gsap.to(speakBtn, { scale: 1, duration: 0.4, ease: "power2.out" });
        waveContainer.style.display = 'none';
        if (waveTimeline) {
          waveTimeline.pause();
        }
        gsap.to('.bar', { height: 5, duration: 0.3, ease: "power2.out" });
      }

      speakBtn.addEventListener('click', () => {
        if (recognition) {
          try { recognition.start(); } catch (_) { recognition.stop(); recognition.start(); }
        }
      });

      function sendVoiceMessage(text) {
        try {
          speakBtn.disabled = true;
          let parentUrl;
          try {
            parentUrl = window.parent.location.href;
          } catch (e) {
            parentUrl = document.referrer;
          }
          if (!parentUrl || parentUrl === 'about:srcdoc') {
            parentUrl = window.location.href;
          }
          const url = new URL(parentUrl);
          url.searchParams.set('voice', text);
          window.top.location.href = url.toString();
        } catch (_) {
          statusEl.textContent = 'Browser blocked connection. Please type in the box below.';
          speakBtn.disabled = false;
        }
      }
    }
  </script>
</body>
</html>
    """,
    height=180,
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Siri-like visual container (Only last exchange)
# ---------------------------------------------------------------------------
if st.session_state.messages:
    last_user = None
    last_assistant = None
    
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user" and not last_user:
            last_user = msg["content"]
        elif msg["role"] == "assistant" and not last_assistant:
            last_assistant = msg
            
    st.markdown('<div class="siri-container">', unsafe_allow_html=True)
    if last_user:
        st.markdown(f'<div class="siri-user-query">“ {html.escape(last_user)} ”</div>', unsafe_allow_html=True)
    if last_assistant:
        st.markdown(f'<div class="siri-assistant-reply">{last_assistant["content"]}</div>', unsafe_allow_html=True)
        if last_assistant.get("saved_facts"):
            st.markdown(
                f'<div class="siri-memory-tag">💾 Remembered: {", ".join(html.escape(f) for f in last_assistant["saved_facts"])}</div>',
                unsafe_allow_html=True
            )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown(
        """
        <div class="siri-container" style="text-align: center; margin-top: 1rem;">
            <div class="siri-assistant-reply" style="font-size: 1.3rem; color: #64748b; font-weight: 500;">
                How can I help you today?
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

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
