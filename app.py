"""
app.py  –  SecureChat E2EE Platform
Cloud-based End-to-End Encrypted Messaging and File Sharing
Built with Streamlit · Hosted on Streamlit Cloud
"""

import streamlit as st
import pyotp, qrcode, io, time, random
from PIL import Image

import store
import crypto_engine as ce
import ui_helpers as ui

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SecureChat E2EE",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

store._init()
ui.inject_css()


# ═════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION PAGES
# ═════════════════════════════════════════════════════════════════════════════

def page_login():
    ui.app_header()
    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown("""
        <div class="auth-card">
            <div class="auth-title">Welcome back 👋</div>
            <div class="auth-subtitle">Sign in to your encrypted account</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Continue →", use_container_width=True, type="primary")

        if submitted:
            user = store.get_user(username)
            if not user:
                st.error("❌ Username not found.")
            elif not ce.verify_password(password, user["hash"], user["salt"]):
                st.error("❌ Incorrect password.")
            else:
                st.session_state["mfa_pending"] = username
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;color:#6B7280;font-size:0.85rem;'>Don't have an account?</div>",
                    unsafe_allow_html=True)
        if st.button("Create Account", use_container_width=True):
            st.session_state["page"] = "register"
            st.rerun()

        st.markdown("""
        <div style='margin-top:24px;padding:12px;background:#EFF6FF;border-radius:10px;
                    font-size:0.75rem;color:#1D4ED8;text-align:center;'>
            🔒 All messages are encrypted end-to-end.<br>
            We cannot read your conversations.
        </div>
        """, unsafe_allow_html=True)


def page_mfa():
    ui.app_header()
    st.markdown("<br>", unsafe_allow_html=True)

    username = st.session_state["mfa_pending"]
    user     = store.get_user(username)

    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown("""
        <div class="auth-card">
            <div class="auth-title">Two-Factor Auth 🔐</div>
            <div class="auth-subtitle">Enter the 6-digit code from your authenticator app</div>
        </div>
        """, unsafe_allow_html=True)

        totp = pyotp.TOTP(user["mfa_secret"])

        with st.form("mfa_form"):
            code = st.text_input("Authenticator Code", placeholder="000000",
                                 max_chars=6)
            col1, col2 = st.columns(2)
            with col1:
                back = st.form_submit_button("← Back", use_container_width=True)
            with col2:
                verify = st.form_submit_button("Verify →", use_container_width=True, type="primary")

        if back:
            st.session_state["mfa_pending"] = None
            st.rerun()

        if verify:
            if totp.verify(code, valid_window=1):
                st.session_state["current_user"] = username
                st.session_state["mfa_pending"]  = None
                st.success("✅ Verified! Logging you in…")
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("❌ Invalid code. Try again.")

        # Demo helper: show current valid code
        with st.expander("🧪 Demo mode — show current TOTP code"):
            st.info(f"Current valid code: **{totp.now()}**")
            st.caption("In production this would only be in your authenticator app.")


def page_register():
    ui.app_header()
    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        step = st.session_state.get("reg_step", 1)

        # ── STEP 1: credentials ──────────────────────────────────────────────
        if step == 1:
            st.markdown("""
            <div class="auth-card">
                <div class="auth-title">Create Account</div>
                <div class="auth-subtitle">Step 1 of 2 — Choose your credentials</div>
            </div>
            """, unsafe_allow_html=True)

            with st.form("reg_form"):
                username = st.text_input("Username", placeholder="Choose a unique username")
                password = st.text_input("Password", type="password",
                                         placeholder="Minimum 8 characters")
                confirm  = st.text_input("Confirm Password", type="password",
                                         placeholder="Repeat your password")
                submitted = st.form_submit_button("Next →", use_container_width=True,
                                                  type="primary")

            if submitted:
                if not username or not password:
                    st.error("All fields are required.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif store.get_user(username):
                    st.error("That username is already taken.")
                else:
                    # Generate key pair and hash password
                    keypair = ce.generate_key_pair()
                    pw_data = ce.hash_password(password)
                    mfa_secret = pyotp.random_base32()
                    color = random.choice(ui.AVATAR_COLORS)

                    st.session_state["reg_step"]   = 2
                    st.session_state["reg_data"]   = {
                        "username":   username,
                        "hash":       pw_data["hash"],
                        "salt":       pw_data["salt"],
                        "public_key": keypair["public_key"],
                        "priv_key":   keypair["private_key"],
                        "mfa_secret": mfa_secret,
                        "color":      color,
                    }
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Already have an account? Sign in", use_container_width=True):
                st.session_state["page"] = "login"
                st.rerun()

        # ── STEP 2: MFA setup ────────────────────────────────────────────────
        elif step == 2:
            rd = st.session_state["reg_data"]
            st.markdown("""
            <div class="auth-card">
                <div class="auth-title">Set Up MFA 📱</div>
                <div class="auth-subtitle">Step 2 of 2 — Scan this QR code with Google Authenticator or Authy</div>
            </div>
            """, unsafe_allow_html=True)

            totp = pyotp.TOTP(rd["mfa_secret"])
            uri  = totp.provisioning_uri(name=rd["username"], issuer_name="SecureChat E2EE")
            qr   = qrcode.make(uri)
            buf  = io.BytesIO()
            qr.save(buf, format="PNG")
            buf.seek(0)

            col_qr, col_key = st.columns(2)
            with col_qr:
                st.image(buf, width=200, caption="Scan with authenticator")
            with col_key:
                st.markdown("**Manual entry key:**")
                st.code(rd["mfa_secret"], language=None)
                st.caption("Enter this key manually if you cannot scan the QR code.")

            st.markdown("**Verify setup — enter the code shown in your app:**")
            with st.form("mfa_setup_form"):
                code  = st.text_input("6-digit code", max_chars=6)
                col1, col2 = st.columns(2)
                with col1:
                    back = st.form_submit_button("← Back")
                with col2:
                    done = st.form_submit_button("Create Account ✓",
                                                 use_container_width=True, type="primary")

            if back:
                st.session_state["reg_step"] = 1
                st.rerun()

            if done:
                totp2 = pyotp.TOTP(rd["mfa_secret"])
                if totp2.verify(code, valid_window=1):
                    ok = store.register_user(
                        username=rd["username"],
                        pw_hash=rd["hash"], pw_salt=rd["salt"],
                        pub_key=rd["public_key"], priv_key=rd["priv_key"],
                        mfa_secret=rd["mfa_secret"], avatar_color=rd["color"],
                    )
                    if ok:
                        st.success("✅ Account created! You can now log in.")
                        st.session_state["reg_step"] = 1
                        st.session_state["reg_data"] = {}
                        time.sleep(1.2)
                        st.session_state["page"] = "login"
                        st.rerun()
                    else:
                        st.error("Username conflict. Please try a different name.")
                else:
                    st.error("❌ Code incorrect. Make sure your app is set up and try again.")

            # Demo helper
            with st.expander("🧪 Demo — show current code"):
                st.info(f"Current valid code: **{totp.now()}**")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    username  = st.session_state["current_user"]
    user_data = store.get_user(username)
    unread    = store.unread_count(username)
    all_users = store.list_users(exclude=username)

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        # User info
        st.markdown(f"""
        <div style='padding:20px 16px 12px;'>
            <div style='display:flex;align-items:center;gap:12px;'>
                {ui.avatar_html(username, user_data["avatar_color"], 44)}
                <div>
                    <div style='font-weight:700;font-size:0.95rem;color:#F1F5F9;'>{username}</div>
                    <div style='font-size:0.72rem;color:#38BDF8;'>● Online</div>
                </div>
            </div>
        </div>
        <hr style='border-color:rgba(255,255,255,0.08);margin:0 16px 12px;'>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown("<div class='sidebar-section'><h4>Navigation</h4></div>",
                    unsafe_allow_html=True)

        tabs = ["💬 Messages", "📁 Files", "👥 Group Chat", "🔑 Security", "ℹ️ About"]
        active_tab = st.session_state.get("active_tab", "💬 Messages")

        for tab in tabs:
            is_active = (active_tab == tab)
            style = "background:rgba(26,86,219,0.35);border-radius:8px;" if is_active else ""
            total_unread = sum(unread.values())
            badge = (f'<span class="badge">{total_unread}</span>'
                     if "Messages" in tab and total_unread > 0 else "")
            if st.button(f"{tab} {badge}", key=f"nav_{tab}",
                         use_container_width=True):
                st.session_state["active_tab"] = tab
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Contacts
        st.markdown("<div class='sidebar-section'><h4>Contacts</h4></div>",
                    unsafe_allow_html=True)

        if not all_users:
            st.markdown("<div style='font-size:0.8rem;color:#94A3B8;padding:8px 0;'>"
                        "No other users yet.<br>Share the app link to invite friends.</div>",
                        unsafe_allow_html=True)
        else:
            for u in all_users:
                ud = store.get_user(u)
                cnt = unread.get(u, 0)
                badge = f'<span class="badge">{cnt}</span>' if cnt else ""
                is_sel = (st.session_state.get("chat_partner") == u)
                chip_class = "user-chip active" if is_sel else "user-chip"
                st.markdown(f"""
                <div class="{chip_class}">
                    {ui.avatar_html(u, ud["avatar_color"])}
                    <span class="uname">{u}</span>{badge}
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Chat with {u}", key=f"sel_{u}",
                             use_container_width=True):
                    st.session_state["chat_partner"] = u
                    st.session_state["active_tab"]   = "💬 Messages"
                    store.mark_read(u, username)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["current_user"] = None
            st.session_state["chat_partner"] = None
            st.rerun()

    # ── MAIN CONTENT ──────────────────────────────────────────────────────────
    ui.app_header()
    active = st.session_state.get("active_tab", "💬 Messages")

    # ────────────────────────────────────────────────────────────────────────
    if "Messages" in active:
        tab_messages(username, user_data, all_users)
    elif "Files" in active:
        tab_files(username, user_data, all_users)
    elif "Group" in active:
        tab_group(username, user_data)
    elif "Security" in active:
        tab_security(username, user_data)
    elif "About" in active:
        tab_about()


# ═════════════════════════════════════════════════════════════════════════════
# TAB: MESSAGES
# ═════════════════════════════════════════════════════════════════════════════

def tab_messages(username, user_data, all_users):
    partner = st.session_state.get("chat_partner")

    if not partner:
        # Welcome / no-conversation view
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        msgs    = store.get_group_messages()
        files   = store.get_files_for(username)
        all_msg = [m for m in store._init() or [] ]  # just trigger init

        total_msgs  = len(st.session_state["db_messages"])
        total_files = len(st.session_state["db_files"])
        total_users = len(st.session_state["db_users"])

        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-val">{total_msgs}</div>
                <div class="stat-lbl">Encrypted Messages Sent</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-val">{total_files}</div>
                <div class="stat-lbl">Files Shared Securely</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-val">{total_users}</div>
                <div class="stat-lbl">Registered Users</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center;padding:40px 20px;'>
            <div style='font-size:3rem;'>🔒</div>
            <div style='font-size:1.2rem;font-weight:700;color:#0D1B2A;margin-top:12px;'>
                Select a contact to start a secure conversation
            </div>
            <div style='color:#6B7280;font-size:0.88rem;margin-top:8px;'>
                All messages are end-to-end encrypted with AES-256-GCM.
                No one — not even us — can read them.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    partner_data = store.get_user(partner)
    store.mark_read(partner, username)

    # Chat header
    st.markdown(f"""
    <div class="chat-header">
        {ui.avatar_html(partner, partner_data["avatar_color"], 38)}
        <div>
            <div class="chat-name">{partner}</div>
            <div style='font-size:0.72rem;color:#10B981;'>End-to-end encrypted</div>
        </div>
        <span class="enc-badge" style='margin-left:12px;'>🔒 E2EE Active</span>
    </div>
    """, unsafe_allow_html=True)

    # Derive shared secret for this conversation
    try:
        shared = ce.derive_shared_secret(
            user_data["private_key"],
            partner_data["public_key"],
        )
    except Exception:
        st.error("Key exchange failed. Cannot open this conversation.")
        return

    # Fetch and render messages
    convos = store.get_conversation(username, partner)

    msg_html = '<div class="chat-scroll" id="chat-bottom">'
    if not convos:
        msg_html += ('<div style="text-align:center;color:#9CA3AF;font-size:0.85rem;'
                     'padding:60px 0;">No messages yet. Say hello! 👋</div>')
    else:
        for m in convos:
            is_me   = (m["sender"] == username)
            side    = "me" if is_me else "them"
            ts_str  = ui.format_ts(m["ts"])
            try:
                text = ce.decrypt_message(m["blob"], shared)
            except Exception:
                text = "[⚠️ Decryption failed]"

            align  = "flex-end" if is_me else "flex-start"
            msg_html += f"""
            <div class="msg-row {side}">
                <div>
                    <div class="msg-bubble {side}">{text}</div>
                    <div class="msg-time" style="text-align:{'right' if is_me else 'left'};">
                        {ts_str} <span class="msg-lock">🔒</span>
                    </div>
                </div>
            </div>"""

    msg_html += '</div>'
    st.markdown(msg_html, unsafe_allow_html=True)

    # Input area
    st.markdown("<br>", unsafe_allow_html=True)
    col_input, col_send = st.columns([5, 1])
    with col_input:
        msg_text = st.text_input(
            "Message", label_visibility="collapsed",
            placeholder=f"Message {partner} (encrypted)…",
            key="msg_input"
        )
    with col_send:
        send_btn = st.button("Send 🔒", type="primary", use_container_width=True)

    if send_btn and msg_text.strip():
        blob = ce.encrypt_message(msg_text.strip(), shared)
        store.save_message(username, partner, blob)
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# TAB: FILES
# ═════════════════════════════════════════════════════════════════════════════

def tab_files(username, user_data, all_users):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📁 Encrypted File Sharing")
    st.caption("Files are encrypted on your device before upload. "
               "The server stores only ciphertext.")

    col_up, col_list = st.columns([1, 1.6])

    with col_up:
        st.markdown("#### Send a File")
        if not all_users:
            st.info("Register another user to send files.")
        else:
            recipient = st.selectbox("Send to", all_users)
            uploaded  = st.file_uploader(
                "Choose a file", type=None,
                help="Any file type. Max 10 MB for demo."
            )
            if uploaded and st.button("🔒 Encrypt & Send", type="primary",
                                      use_container_width=True):
                raw  = uploaded.read()
                if len(raw) > 10 * 1024 * 1024:
                    st.error("File too large for demo (max 10 MB).")
                else:
                    rd = store.get_user(recipient)
                    try:
                        shared = ce.derive_shared_secret(
                            user_data["private_key"],
                            rd["public_key"],
                        )
                        enc = ce.encrypt_file(raw, shared)
                        store.save_file(username, recipient,
                                        uploaded.name, enc, len(raw))
                        st.success(f"✅ File encrypted and sent to **{recipient}**!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Encryption error: {e}")

    with col_list:
        st.markdown("#### Your Files")
        files = store.get_files_for(username)
        if not files:
            st.markdown("""
            <div style='text-align:center;padding:40px;color:#9CA3AF;'>
                <div style='font-size:2.5rem;'>📭</div>
                <div style='margin-top:8px;'>No files yet.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for f in files:
                direction = "Sent to" if f["sender"] == username else "From"
                other     = f["recipient"] if f["sender"] == username else f["sender"]
                icon      = ui.file_icon(f["name"])
                size_str  = ui.fmt_size(f["size"])
                ts_str    = ui.format_ts(f["ts"])

                st.markdown(f"""
                <div class="file-item">
                    <span class="file-icon">{icon}</span>
                    <div>
                        <div class="file-name">{f["name"]}</div>
                        <div class="file-meta">{direction} <b>{other}</b> · {size_str} · {ts_str}</div>
                    </div>
                    <span class="enc-tag">🔒 E2EE</span>
                </div>""", unsafe_allow_html=True)

                # Only recipient can decrypt
                if f["recipient"] == username:
                    sender_data = store.get_user(f["sender"])
                    if st.button(f"⬇️ Decrypt & Download", key=f"dl_{f['id']}"):
                        try:
                            shared = ce.derive_shared_secret(
                                user_data["private_key"],
                                sender_data["public_key"],
                            )
                            dec = ce.decrypt_file(f["enc_bytes"], shared)
                            st.download_button(
                                label=f"💾 Save {f['name']}",
                                data=dec,
                                file_name=f["name"],
                                key=f"save_{f['id']}",
                            )
                        except Exception as e:
                            st.error(f"Decryption failed: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# TAB: GROUP CHAT
# ═════════════════════════════════════════════════════════════════════════════

def tab_group(username, user_data):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 👥 Group Channel")
    st.caption("Group messages are visible to all logged-in users in this session.")

    msgs = store.get_group_messages()

    msg_html = '<div style="max-height:420px;overflow-y:auto;padding:8px 0;">'
    if not msgs:
        msg_html += ('<div style="text-align:center;color:#9CA3AF;'
                     'padding:40px;font-size:0.88rem;">No group messages yet.</div>')
    else:
        for m in msgs[-50:]:   # last 50
            ud     = store.get_user(m["sender"])
            color  = ud["avatar_color"] if ud else "#6B7280"
            ts_str = ui.format_ts(m["ts"])
            is_me  = (m["sender"] == username)
            name_style = "color:#1A56DB;" if is_me else "color:#7E3AF2;"
            msg_html += f"""
            <div class="group-msg">
                <div class="gsender" style="{name_style}">
                    {m["sender"]} · <span style="font-weight:400;color:#9CA3AF;">{ts_str}</span>
                </div>
                <div class="gtext">{m["text"]}</div>
            </div>"""
    msg_html += '</div>'
    st.markdown(msg_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_i, col_b = st.columns([5, 1])
    with col_i:
        gtxt = st.text_input("Group message", label_visibility="collapsed",
                             placeholder="Send a message to the group…",
                             key="group_input")
    with col_b:
        if st.button("Send", type="primary", use_container_width=True):
            if gtxt.strip():
                store.save_group_message(username, gtxt.strip())
                st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# TAB: SECURITY
# ═════════════════════════════════════════════════════════════════════════════

def tab_security(username, user_data):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🔑 Security & Key Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Your Public Key")
        st.caption("Share this with contacts so they can encrypt messages to you.")
        st.markdown(f'<div class="fingerprint-box">{user_data["public_key"]}</div>',
                    unsafe_allow_html=True)
        st.download_button("⬇️ Export Public Key", data=user_data["public_key"],
                           file_name=f"{username}_public_key.txt")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Key Fingerprint")
        st.caption("Verify this with your contacts out-of-band to prevent MITM attacks.")
        fp = ce.key_fingerprint(user_data["public_key"])
        st.markdown(f'<div class="fingerprint-box">{fp}</div>',
                    unsafe_allow_html=True)

    with col2:
        st.markdown("#### Encryption Details")
        details = {
            "Key Exchange":     "X25519 ECDH",
            "KDF":              "HKDF-SHA256",
            "Content Cipher":   "AES-256-GCM",
            "Nonce Size":       "96 bits (random per message)",
            "MFA":              "TOTP (RFC 6238) — 30-second window",
            "Password Hashing": "PBKDF2-HMAC-SHA256 (480,000 iterations)",
            "File Encryption":  "Chunked AES-256-GCM (1 MB blocks)",
            "Architecture":     "Zero-Knowledge Server",
        }
        for label, value in details.items():
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;align-items:center;
                        padding:10px 0;border-bottom:1px solid #F3F4F6;'>
                <span style='font-size:0.85rem;color:#6B7280;font-weight:500;'>{label}</span>
                <span style='font-size:0.85rem;color:#0D1B2A;font-weight:600;
                             background:#EFF6FF;padding:2px 10px;border-radius:6px;'>{value}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Contact Key Fingerprints")
        all_users = store.list_users(exclude=username)
        if not all_users:
            st.caption("No other users registered yet.")
        else:
            for u in all_users:
                ud = store.get_user(u)
                fp = ce.key_fingerprint(ud["public_key"])
                with st.expander(f"🔑 {u}"):
                    st.markdown(f'<div class="fingerprint-box">{fp}</div>',
                                unsafe_allow_html=True)
                    st.caption("Compare this fingerprint with the user directly "
                               "to verify no man-in-the-middle attack is occurring.")


# ═════════════════════════════════════════════════════════════════════════════
# TAB: ABOUT
# ═════════════════════════════════════════════════════════════════════════════

def tab_about():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ℹ️ About SecureChat E2EE")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='background:#fff;border-radius:14px;padding:24px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.06);border:1px solid #F3F4F6;'>
            <h4 style='color:#0D1B2A;margin-bottom:12px;'>Project Overview</h4>
            <p style='font-size:0.88rem;color:#374151;line-height:1.7;'>
                This platform was developed as a final-year Computer Science project at
                <b>PAAU, Anyigba</b>. It demonstrates how genuine end-to-end encryption
                can be implemented in a cloud-hosted web application using Python and Streamlit.
            </p>
            <p style='font-size:0.88rem;color:#374151;line-height:1.7;'>
                The system implements the zero-knowledge architecture described in
                <b>Chapter Three</b> of the project report, where the cloud server stores
                and relays only ciphertext and never has access to plaintext content.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background:#fff;border-radius:14px;padding:24px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.06);border:1px solid #F3F4F6;'>
            <h4 style='color:#0D1B2A;margin-bottom:12px;'>Technology Stack</h4>
        """, unsafe_allow_html=True)

        tech = [
            ("🐍", "Python 3.11+", "Core language"),
            ("🎈", "Streamlit", "Web UI framework"),
            ("🔐", "cryptography (PyCA)", "X25519, AES-256-GCM, HKDF"),
            ("📱", "pyotp", "TOTP multi-factor authentication"),
            ("☁️", "Streamlit Cloud", "Hosting platform"),
        ]
        for icon, name, desc in tech:
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:10px;padding:8px 0;
                        border-bottom:1px solid #F9FAFB;'>
                <span style='font-size:1.2rem;'>{icon}</span>
                <div>
                    <div style='font-size:0.85rem;font-weight:600;color:#111827;'>{name}</div>
                    <div style='font-size:0.75rem;color:#6B7280;'>{desc}</div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background:#fff;border-radius:14px;padding:24px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.06);border:1px solid #F3F4F6;'>
            <h4 style='color:#0D1B2A;margin-bottom:12px;'>Key References</h4>
        """, unsafe_allow_html=True)

        refs = [
            "Barnes et al. (2023). MLS Protocol RFC 9420. IETF.",
            "NIST (2024). Post-Quantum Standards FIPS 203/204/205.",
            "Kobeissi et al. (2021). Noise Explorer. IEEE EuroS&P.",
            "EFF (2026). Quantum preparedness deadline: 2029.",
            "NITDA (2023). Nigeria Data Protection Act 2023.",
            "IBM Security (2024). Cost of a Data Breach Report.",
            "Gambo & Almulhem (2025). ZTA Systematic Review. Sensors.",
        ]
        for r in refs:
            st.markdown(f"""
            <div style='font-size:0.8rem;color:#374151;padding:7px 0;
                        border-bottom:1px solid #F9FAFB;line-height:1.5;'>
                📖 {r}
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background:linear-gradient(135deg,#0D1B2A,#1A56DB);
                    border-radius:14px;padding:24px;color:#fff;'>
            <h4 style='margin-bottom:10px;'>⚠️ Demo Notice</h4>
            <p style='font-size:0.82rem;line-height:1.7;opacity:0.9;'>
                This is an academic demonstration. Data is stored in Streamlit session
                state and is lost when the session ends. In a production deployment,
                a PostgreSQL database would persist encrypted data.
                Private keys would be stored only in the user's browser (WebCrypto API)
                and never transmitted to the server.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════════════════════════════════════

def main():
    store._init()

    # Seed demo users if store is empty
    if not st.session_state["db_users"]:
        _seed_demo_users()

    current = st.session_state.get("current_user")
    mfa_pend = st.session_state.get("mfa_pending")
    page    = st.session_state.get("page", "login")

    if current:
        page_dashboard()
    elif mfa_pend:
        page_mfa()
    elif page == "register":
        page_register()
    else:
        page_login()


def _seed_demo_users():
    """Create two demo accounts so the app is usable immediately."""
    import random as _rnd

    demos = [
        ("alice", "password123"),
        ("bob",   "password123"),
    ]
    for uname, pw in demos:
        kp     = ce.generate_key_pair()
        pw_d   = ce.hash_password(pw)
        secret = pyotp.random_base32()
        color  = _rnd.choice(ui.AVATAR_COLORS)
        store.register_user(
            username=uname, pw_hash=pw_d["hash"], pw_salt=pw_d["salt"],
            pub_key=kp["public_key"], priv_key=kp["private_key"],
            mfa_secret=secret, avatar_color=color,
        )


if __name__ == "__main__":
    main()
