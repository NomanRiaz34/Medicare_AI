"""Static visual components. Never pass patient/model/API-key text into unsafe HTML."""
import streamlit as st


def apply_theme(dark=False):
    if dark:
        bg, surface, text, muted, border, field, wash = "#0c1624", "#142235", "#edf5fc", "#a6bbce", "#2c4158", "#1a2b40", "#17353c"
    else:
        bg, surface, text, muted, border, field, wash = "#f3f7fa", "#ffffff", "#172e43", "#637b8e", "#dce7ee", "#f8fafc", "#eaf6f3"
    st.markdown(f"""<style>
    .stApp {{background:{bg}; color:{text}; font-family:Arial,Helvetica,sans-serif;}}
    [data-testid="stHeader"] {{background:transparent;}}
    .block-container {{max-width:1280px;padding-top:4.5rem;padding-bottom:2.5rem;}}
    [data-testid="stSidebar"] {{background:{surface};border-right:1px solid {border};}}
    [data-testid="stSidebar"] .block-container {{padding-top:1.5rem;}}
    .stApp h1,.stApp h2,.stApp h3,.stApp h4 {{color:{text};letter-spacing:-.035em;}}
    .stApp h1 {{font-size:2.55rem;line-height:1.13;font-weight:750;}}
    .stApp p,.stApp label,.stApp li {{color:{text};}}
    [data-testid="stCaptionContainer"], [data-testid="stCaption"], .stCaption {{color:{muted} !important;opacity:1 !important;}}
    [data-testid="stCaptionContainer"] p,[data-testid="stCaption"] p,.stCaption p {{color:{muted} !important;opacity:1 !important;font-size:.83rem;line-height:1.6;}}
    [data-testid="stWidgetLabel"] p {{font-weight:600;font-size:.86rem;}}
    [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"]>div {{border-color:{border};}}
    [data-testid="stForm"] {{background:{surface};border:1px solid {border};border-radius:20px;padding:1.6rem;}}
    [data-testid="stMetric"] {{background:{surface};border:1px solid {border};border-radius:17px;padding:18px 22px;}}
    [data-testid="stMetricValue"] {{color:{text};font-size:1.9rem;font-weight:700;}}
    [data-testid="stMetricLabel"] p {{color:{muted};font-size:.8rem;}}
    [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea {{color:{text};background:{field};}}
    [data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div {{background:{field};color:{text};border-color:{border};border-radius:11px;}}
    [data-testid="stMultiSelect"] span {{color:{text};}}
    [data-testid="stSelectbox"] [data-baseweb="select"] span {{color:{text};}}
    [data-testid="stExpander"] {{background:{surface};border-radius:13px;}}
    [data-testid="stExpander"] details {{border-color:{border};}}
    [data-testid="stExpander"] summary {{color:{text};}}
    [data-testid="stTabs"] [data-baseweb="tab-list"] {{gap:20px;border-bottom:1px solid {border};}}
    [data-testid="stTabs"] button[role="tab"] {{color:{muted};padding:10px 6px;}}
    [data-testid="stTabs"] button[aria-selected="true"] {{color:#0b9988;}}
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {{background:#0b9988;}}
    [data-testid="stButton"] button,[data-testid="stDownloadButton"] button {{border-radius:11px;border-color:{border};}}
    [data-testid="stButton"] button:not([kind="primary"]),[data-testid="stDownloadButton"] button {{background:{surface};color:{text};}}
    [data-testid="stButton"] button[kind="primary"], [data-testid="stFormSubmitButton"] button {{border:0;border-radius:12px;background:linear-gradient(100deg,#078d80,#147d98);color:white;min-height:46px;}}
    [data-testid="stFormSubmitButton"] button p,[data-testid="stButton"] button[kind="primary"] p {{color:white;}}
    [data-testid="stAlert"] p {{color:{text};}}
    [data-testid="stAlert"] {{border-radius:12px;}}
    [data-testid="stLinkButton"] a {{background:{surface};color:{text};border:1px solid {border};border-radius:11px;}}
    [data-testid="stLinkButton"] a p {{color:{text} !important;}}
    [data-testid="stSelectbox"] [role="combobox"], [data-testid="stMultiSelect"] [role="combobox"] {{background:{field};color:{text};}}
    [data-testid="stSelectbox"]>div>div, [data-testid="stMultiSelect"]>div>div {{background:{field};color:{text};}}
    [data-testid="stSelectbox"] svg,[data-testid="stMultiSelect"] svg {{fill:{muted};}}
    [data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder {{color:{muted};opacity:1;}}
    [data-testid="stTooltipIcon"] svg {{fill:{muted};}}
    .mg-brand {{display:flex;align-items:center;gap:12px;margin-bottom:20px;}}
    .mg-symbol {{display:inline-grid;place-items:center;width:44px;height:44px;background:linear-gradient(145deg,#0caa97,#147d98);border-radius:14px;color:white;font-size:28px;font-weight:600;box-shadow:0 6px 16px #0b998825;}}
    .mg-brand-title {{color:{text};font-size:1.25rem;font-weight:750;letter-spacing:-.03em;}}
    .mg-brand-sub {{color:{muted};font-size:.7rem;letter-spacing:.13em;text-transform:uppercase;}}
    .mg-kicker {{color:#0d9b8c;font-size:.73rem;letter-spacing:.17em;font-weight:750;text-transform:uppercase;margin-bottom:15px;}}
    .mg-intro {{color:{muted};font-size:1.04rem;line-height:1.8;max-width:540px;}}
    .mg-hero {{background:linear-gradient(120deg,{surface},{wash});border:1px solid {border};border-radius:22px;padding:28px 32px;margin:5px 0 24px;}}
    .mg-hero h1 {{margin:0 0 12px;font-size:2.2rem;}}
    .mg-hero p {{color:{muted};margin:0;line-height:1.7;}}
    .mg-chip {{display:inline-flex;align-items:center;gap:7px;border:1px solid {border};border-radius:999px;color:{muted};padding:6px 12px;font-size:.75rem;background:{surface};margin-right:6px;margin-bottom:8px;}}
    .mg-dot {{width:7px;height:7px;border-radius:50%;background:#12b99c;}}
    .mg-step {{display:flex;align-items:center;gap:15px;margin:21px 0;color:{text};}}
    .mg-step-num {{flex-shrink:0;width:33px;height:33px;display:grid;place-items:center;border-radius:11px;background:{wash};color:#0b9988;font-size:.83rem;font-weight:750;}}
    .mg-step strong {{font-size:.9rem;}}
    .mg-step small {{display:block;color:{muted};font-size:.8rem;margin-top:3px;}}
    .mg-section {{display:flex;align-items:center;gap:11px;margin:4px 0 16px;}}
    .mg-section > span {{color:#0b9988;background:{wash};border-radius:8px;padding:5px 9px;font-weight:750;font-size:.76rem;}}
    .mg-section h3 {{font-size:1.12rem;margin:0;}}
    .mg-foot {{color:{muted};font-size:.75rem;line-height:1.7;text-align:center;margin-top:24px;}}
    .mg-empty {{text-align:center;padding:35px 20px;border:1px dashed {border};border-radius:18px;background:{surface};}}
    .mg-empty h3 {{font-size:1.1rem;}}
    .mg-empty p {{color:{muted};font-size:.9rem;}}
    .mg-session {{background:{wash};border:1px solid {border};border-radius:13px;padding:14px;margin-bottom:16px;color:{text};}}
    .mg-session small {{display:block;color:{muted};margin-top:5px;}}
    @media(max-width:700px) {{.block-container {{padding:4rem 1.2rem 1.2rem;}} .stApp h1 {{font-size:2rem;}} .mg-hero {{padding:22px;}} [data-testid="stForm"] {{padding:1rem;}}}}
    </style>""", unsafe_allow_html=True)


def brand():
    st.markdown('''<div class="mg-brand"><div class="mg-symbol">+</div><div>
    <div class="mg-brand-title">MediGuide AI</div><div class="mg-brand-sub">Clarity before care</div>
    </div></div>''', unsafe_allow_html=True)


def login_story():
    brand()
    st.markdown('''<div class="mg-kicker">Your personal guidance workspace</div>
    <h1>A clearer path<br>from symptoms<br>to next steps.</h1>
    <p class="mg-intro">Thoughtful, easy-to-understand symptom guidance to help you prepare for a conversation with a healthcare professional.</p>
    <div style="margin:22px 0 28px"><span class="mg-chip">6 answer languages</span><span class="mg-chip">Voice input</span><span class="mg-chip">PDF reports</span></div>
    <div class="mg-step"><div class="mg-step-num">01</div><div><strong>Connect your OpenAI key</strong><small>Verified with OpenAI before your workspace opens.</small></div></div>
    <div class="mg-step"><div class="mg-step-num">02</div><div><strong>Describe what you are experiencing</strong><small>Type your symptoms or review a voice transcript.</small></div></div>
    <div class="mg-step"><div class="mg-step-num">03</div><div><strong>Prepare for your next conversation</strong><small>Review educational guidance and questions for your doctor.</small></div></div>
    ''', unsafe_allow_html=True)


def home_hero():
    st.markdown('''<div class="mg-hero"><div class="mg-kicker">Your guidance workspace</div>
    <h1>Let’s make your next step clearer.</h1><p>Share what you are experiencing. Get structured educational guidance, warning signs, and questions to take to a professional.</p>
    <div style="margin-top:18px"><span class="mg-chip"><span class="mg-dot"></span>Key connected</span><span class="mg-chip">Private browser session</span><span class="mg-chip">Educational use only</span></div></div>''', unsafe_allow_html=True)


def section(number, title):
    # Only source-authored constants should be passed here.
    st.markdown(f'<div class="mg-section"><span>{number}</span><h3>{title}</h3></div>', unsafe_allow_html=True)


def empty_history():
    st.markdown('''<div class="mg-empty"><h3>Your session starts here</h3><p>Complete your first assessment to see it in your history.</p></div>''', unsafe_allow_html=True)
