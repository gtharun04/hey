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
    
    /* Ultimate app containers for full-bleed dark gradient background */
    [data-testid="stAppViewContainer"], .stApp, .main {
        background: #0b0f19 !important;
        color: #f1f5f9 !important;
        overflow: hidden !important;
        position: relative !important;
    }

    /* Drifting background circles using CSS animations */
    [data-testid="stAppViewContainer"]::before, [data-testid="stAppViewContainer"]::after {
        content: "";
        position: absolute;
        width: 320px;
        height: 320px;
        border-radius: 50%;
        filter: blur(120px);
        opacity: 0.12;
        z-index: 0;
        pointer-events: none;
    }
    
    [data-testid="stAppViewContainer"]::before {
        background: #8b5cf6;
        top: 15%;
        left: 5%;
        animation: floatBlob1 20s infinite alternate ease-in-out;
    }
    
    [data-testid="stAppViewContainer"]::after {
        background: #06b6d4;
        bottom: 15%;
        right: 5%;
        animation: floatBlob2 24s infinite alternate ease-in-out;
    }
    
    @keyframes floatBlob1 {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(40px, 30px) scale(1.15); }
        100% { transform: translate(-20px, 40px) scale(0.9); }
    }
    
    @keyframes floatBlob2 {
        0% { transform: translate(0, 0) scale(1.1); }
        50% { transform: translate(-30px, -40px) scale(0.9); }
        100% { transform: translate(40px, 20px) scale(1.15); }
    }

    /* Force section layout wrapper to be transparent */
    [data-testid="stAppViewContainer"] > section {
        background: transparent !important;
    }
    
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stToolbar"] { display: none; }
    
    .buddy-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem;
        z-index: 1;
        position: relative;
    }
    
    .buddy-header h1 {
        font-size: clamp(1.8rem, 4.5vw, 2.3rem);
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #c084fc, #8b5cf6, #3b82f6, #06b6d4);
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
        color: #94a3b8;
        font-size: clamp(0.85rem, 2.5vw, 0.95rem);
        font-weight: 500;
        display: flex;
        align-items: center;
        justify-content: center;
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
        z-index: 1;
        position: relative;
    }
    
    div[data-testid="stSidebar"] {
        background: rgba(11, 15, 25, 0.7) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
    
    /* Sidebar text colors */
    div[data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
        font-weight: 600;
        font-size: 1.05rem;
    }
    
    div[data-testid="stSidebar"] p, div[data-testid="stSidebar"] span {
        color: #94a3b8 !important;
        font-size: 0.85rem;
    }
    
    /* Custom style for streamlit buttons inside columns */
    div[data-testid="stSidebar"] button {
        border-radius: 6px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        background-color: rgba(255, 255, 255, 0.04) !important;
        color: #f43f5e !important;
        padding: 1px 4px !important;
        font-size: 0.75rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    div[data-testid="stSidebar"] button:hover {
        background-color: rgba(244, 63, 94, 0.15) !important;
        border-color: rgba(244, 63, 94, 0.3) !important;
        color: #fb7185 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(244, 63, 94, 0.15);
    }

    /* Siri-like borderless visual container with subtle glossy tag support */
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
        z-index: 1;
        position: relative;
    }
    
    .siri-user-query {
        font-size: 1.15rem;
        color: #c084fc;
        font-style: italic;
        font-weight: 500;
        margin-bottom: 1.25rem;
        max-width: 85%;
        opacity: 0;
        animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.1s forwards;
    }
    
    .siri-assistant-reply {
        font-size: 1.6rem;
        color: #f1f5f9;
        font-weight: 700;
        line-height: 1.45;
        max-width: 90%;
        margin-bottom: 0.5rem;
        opacity: 0;
        animation: fadeIn 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.3s forwards;
    }
    
    .siri-memory-tag {
        font-size: 0.75rem;
        color: #2dd4bf;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 99px;
        padding: 4px 12px;
        margin-top: 0.75rem;
        display: inline-block;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        opacity: 0;
        animation: fadeIn 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards;
    }
    
    /* Facts card design */
    .fact-card {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
        font-size: 0.78rem !important;
        color: #cbd5e1 !important;
        line-height: 1.25 !important;
        margin-bottom: 3px !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .fact-card:hover {
        background: rgba(255, 255, 255, 0.04) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        transform: scale(1.02);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2) !important;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
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
# Header & Dynamic Iframe Permissions
# ---------------------------------------------------------------------------
header_html = '<div class="buddy-header"><h1 style="margin: 0; color: #f1f5f9;">AI Buddy</h1><p style="margin: 0.25rem 0 0; color: #94a3b8; font-size: 0.95rem; font-weight: 500; display: flex; align-items: center; justify-content: center;"><span style="display:inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; margin-right: 6px; box-shadow: 0 0 8px #10b981; animation: siriDotPulse 2s infinite;"></span>Listening</p></div>'
st.markdown(header_html, unsafe_allow_html=True)

st.markdown(
    """
    <script>
        // Listen for voice transcript messages from STT iframe to bypass sandbox top-navigation blocks
        window.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'voice_transcript') {
                const url = new URL(window.location.href);
                url.searchParams.set('voice', event.data.text);
                window.location.href = url.toString();
            }
        });

        // Grant microphone permissions dynamically
        const fixIframes = () => {
            document.querySelectorAll('iframe').forEach(iframe => {
                if (!iframe.hasAttribute('allow') || !iframe.getAttribute('allow').includes('microphone')) {
                    iframe.setAttribute('allow', 'microphone');
                    iframe.src = iframe.src;
                }
            });
        };
        fixIframes();
        setInterval(fixIframes, 1000);
    </script>
    """,
    unsafe_allow_html=True
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
                            f'<div class="fact-card">{html.escape(fact)}</div>',
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
    color: #94a3b8;
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
    padding: 12px 36px;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 8px;
    cursor: pointer;
    background: rgba(139, 92, 246, 0.1);
    color: #c084fc;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    outline: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
    touch-action: manipulation;
  }
  #speakBtn:hover {
    background: rgba(139, 92, 246, 0.2);
    border-color: rgba(139, 92, 246, 0.5);
    box-shadow: 0 6px 16px rgba(139, 92, 246, 0.25);
    transform: translateY(-1.5px);
  }
  
  #speakBtn.listening {
    background: rgba(236, 72, 153, 0.15);
    border-color: rgba(236, 72, 153, 0.6);
    color: #f472b6;
    box-shadow: 0 0 20px rgba(236, 72, 153, 0.3);
    animation: simplePulse 1.5s infinite ease-in-out;
  }
  
  @keyframes simplePulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.03); }
  }
  #status {
    width: 100%;
    font-size: 0.8rem;
    color: #94a3b8;
    text-align: center;
    margin-top: 10px;
    font-weight: 500;
    letter-spacing: 0.01em;
    transition: color 0.3s;
  }
  
  /* Frosted Glossy Glass panel for transcript display */
  #transcript {
    width: 100%;
    margin-top: 10px;
    padding: 8px 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    color: #c084fc;
    font-size: 0.92rem;
    font-style: italic;
    font-weight: 500;
    display: none;
    line-height: 1.35;
    text-align: center;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
  }
  
  /* Bouncing voice bars inside STT element */
  #wave-container {
    display: none;
    justify-content: center;
    align-items: center;
    gap: 4px;
    margin-top: 10px;
    height: 18px;
  }
  .bar {
    width: 4px;
    height: 6px;
    background: #8b5cf6;
    border-radius: 99px;
    transition: background 0.3s;
  }
</style>
</head>
<body>
  <div class="row">
    <button id="speakBtn" type="button">Speak</button>
  </div>
  <div id="wave-container">
    <div class="bar" style="background:#c084fc"></div>
    <div class="bar" style="background:#8b5cf6"></div>
    <div class="bar" style="background:#3b82f6"></div>
    <div class="bar" style="background:#06b6d4"></div>
    <div class="bar" style="background:#2dd4bf"></div>
  </div>
  <div id="status">Click 'Speak' to start</div>
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
        gsap.to(speakBtn, { scale: 1.03, duration: 0.3, ease: "power2.out" });
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
        speakBtn.textContent = 'Listening...';
        
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
          statusEl.textContent = "Click 'Speak' to start";
        }
      };

      function resetBtn() {
        speakBtn.classList.remove('listening');
        speakBtn.textContent = 'Speak';
        waveContainer.style.display = 'none';
        if (waveTimeline) {
          waveTimeline.pause();
        }
      }

      speakBtn.addEventListener('click', () => {
        if (recognition) {
          try { recognition.start(); } catch (_) { recognition.stop(); recognition.start(); }
        }
      });

      function sendVoiceMessage(text) {
        try {
          speakBtn.disabled = true;
          window.parent.postMessage({ type: 'voice_transcript', text: text }, '*');
        } catch (_) {
          statusEl.textContent = 'Browser blocked connection.';
          speakBtn.disabled = false;
        }
      }
    }
  </script>
</body>
</html>
    """,
    height=120,
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
        <div class="siri-container" style="text-align: center; margin-top: 1.5rem;">
            <div class="siri-assistant-reply" style="font-size: 1.4rem; color: #94a3b8; font-weight: 500;">
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

# Pure voice assistant model (no text input option)

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
