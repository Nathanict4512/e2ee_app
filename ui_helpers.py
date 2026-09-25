"""
ui_helpers.py
Shared CSS, colour palette, and UI component helpers.
"""

import streamlit as st
import time


# ── COLOUR PALETTE ────────────────────────────────────────────────────────────
AVATAR_COLORS = [
    "#1A56DB", "#7E3AF2", "#0E9F6E", "#C81E1E",
    "#FF8A4C", "#0694A2", "#6C2BD9", "#D61F69",
]


def inject_css():
    st.markdown("""
    <style>
    /* ── Google font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Hide default Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    section[data-testid="stSidebar"] > div:first-child { padding-top: 0; }

    /* ── App shell ── */
    .app-header {
        background: linear-gradient(135deg, #0D1B2A 0%, #1A56DB 100%);
        padding: 18px 28px;
        display: flex; align-items: center; gap: 14px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.25);
    }
    .app-header h1 {
        color: #fff; font-size: 1.35rem; font-weight: 700;
        margin: 0; letter-spacing: -0.3px;
    }
    .app-header .subtitle {
        color: #93C5FD; font-size: 0.72rem; font-weight: 400;
        margin: 0;
    }
    .lock-icon { font-size: 1.8rem; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #0D1B2A !important;
    }
    section[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    .sidebar-section {
        padding: 12px 16px;
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .sidebar-section h4 {
        color: #93C5FD !important;
        font-size: 0.72rem; text-transform: uppercase;
        letter-spacing: 1px; margin-bottom: 8px;
    }

    /* ── User chip in sidebar ── */
    .user-chip {
        display: flex; align-items: center; gap: 10px;
        padding: 8px 10px; border-radius: 8px;
        cursor: pointer; transition: background 0.15s;
        margin-bottom: 4px;
    }
    .user-chip:hover { background: rgba(255,255,255,0.08); }
    .user-chip.active { background: rgba(26,86,219,0.35); }
    .user-chip .avatar {
        width: 34px; height: 34px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.85rem; color: #fff;
        flex-shrink: 0;
    }
    .user-chip .uname { font-size: 0.88rem; font-weight: 500; }
    .user-chip .badge {
        margin-left: auto; background: #EF4444;
        color: #fff; font-size: 0.68rem; font-weight: 700;
        padding: 1px 6px; border-radius: 999px;
    }

    /* ── Chat window ── */
    .chat-header {
        background: #fff;
        border-bottom: 1px solid #E5E7EB;
        padding: 14px 20px;
        display: flex; align-items: center; gap: 12px;
    }
    .chat-header .chat-name { font-size: 1rem; font-weight: 600; color: #0D1B2A; }
    .chat-header .enc-badge {
        font-size: 0.7rem; background: #ECFDF5;
        color: #065F46; padding: 2px 10px; border-radius: 999px;
        font-weight: 600;
    }

    /* ── Message bubbles ── */
    .chat-scroll {
        height: 420px; overflow-y: auto;
        padding: 20px; background: #F8FAFC;
        display: flex; flex-direction: column; gap: 10px;
    }
    .msg-row { display: flex; align-items: flex-end; gap: 8px; }
    .msg-row.me { flex-direction: row-reverse; }
    .msg-bubble {
        max-width: 68%; padding: 10px 14px;
        border-radius: 18px; font-size: 0.9rem;
        line-height: 1.45; word-break: break-word;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    }
    .msg-bubble.them {
        background: #fff; color: #1F2937;
        border-bottom-left-radius: 4px;
    }
    .msg-bubble.me {
        background: linear-gradient(135deg, #1A56DB, #7E3AF2);
        color: #fff; border-bottom-right-radius: 4px;
    }
    .msg-time { font-size: 0.65rem; color: #9CA3AF; margin-top: 3px; }
    .msg-lock { font-size: 0.7rem; opacity: 0.6; }

    /* ── Cards ── */
    .stat-card {
        background: #fff; border-radius: 14px;
        padding: 20px 18px; text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #F3F4F6;
    }
    .stat-card .stat-val {
        font-size: 2rem; font-weight: 700; color: #1A56DB;
    }
    .stat-card .stat-lbl {
        font-size: 0.78rem; color: #6B7280; margin-top: 4px;
    }

    /* ── File item ── */
    .file-item {
        display: flex; align-items: center; gap: 12px;
        padding: 12px 16px; background: #fff;
        border-radius: 10px; margin-bottom: 8px;
        border: 1px solid #F3F4F6;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .file-icon { font-size: 1.6rem; }
    .file-name { font-size: 0.88rem; font-weight: 600; color: #111827; }
    .file-meta { font-size: 0.72rem; color: #6B7280; }
    .enc-tag {
        margin-left: auto; font-size: 0.68rem;
        background: #EFF6FF; color: #1D4ED8;
        padding: 2px 8px; border-radius: 999px; font-weight: 600;
    }

    /* ── Fingerprint box ── */
    .fingerprint-box {
        font-family: monospace; font-size: 0.78rem;
        background: #F1F5F9; border: 1px solid #CBD5E1;
        border-radius: 8px; padding: 10px 14px;
        letter-spacing: 1px; color: #334155;
        word-break: break-all;
    }

    /* ── Auth page ── */
    .auth-card {
        max-width: 440px; margin: 40px auto;
        background: #fff; border-radius: 20px;
        padding: 40px 36px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.10);
    }
    .auth-title {
        font-size: 1.55rem; font-weight: 700;
        color: #0D1B2A; margin-bottom: 6px;
    }
    .auth-subtitle { font-size: 0.88rem; color: #6B7280; margin-bottom: 28px; }

    /* ── Group chat ── */
    .group-msg {
        padding: 8px 14px; border-radius: 12px;
        background: #fff; margin-bottom: 6px;
        border-left: 3px solid #1A56DB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .group-msg .gsender { font-size: 0.72rem; font-weight: 700; color: #1A56DB; }
    .group-msg .gtext   { font-size: 0.88rem; color: #1F2937; margin-top: 2px; }

    /* ── Stremlit input overrides ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px !important;
        border: 1.5px solid #E5E7EB !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #1A56DB !important;
        box-shadow: 0 0 0 3px rgba(26,86,219,0.12) !important;
    }
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)


def app_header():
    st.markdown("""
    <div class="app-header">
        <span class="lock-icon">🔒</span>
        <div>
            <h1>SecureChat E2EE</h1>
            <p class="subtitle">End-to-End Encrypted · Zero-Knowledge · AES-256-GCM</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def avatar_html(username: str, color: str, size: int = 34) -> str:
    letter = username[0].upper()
    return (f'<div class="avatar" style="background:{color};'
            f'width:{size}px;height:{size}px;border-radius:50%;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-weight:700;font-size:{int(size*0.42)}px;color:#fff;">'
            f'{letter}</div>')


def format_ts(ts: float) -> str:
    import datetime
    dt = datetime.datetime.fromtimestamp(ts)
    now = datetime.datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%d %b %H:%M")


def fmt_size(n_bytes: int) -> str:
    if n_bytes < 1024:
        return f"{n_bytes} B"
    if n_bytes < 1024**2:
        return f"{n_bytes/1024:.1f} KB"
    return f"{n_bytes/1024**2:.1f} MB"


def file_icon(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    icons = {
        "pdf": "📄", "doc": "📝", "docx": "📝",
        "xls": "📊", "xlsx": "📊", "csv": "📊",
        "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️", "gif": "🖼️",
        "mp4": "🎥", "mp3": "🎵",
        "zip": "🗜️", "rar": "🗜️", "7z": "🗜️",
        "py": "🐍", "js": "📜", "html": "🌐",
    }
    return icons.get(ext, "📎")
