"""
store.py
In-memory data store backed by Streamlit session state.
On Streamlit Cloud, data persists for the session lifetime only.
In a production system this would be replaced by a PostgreSQL database.
"""

import streamlit as st
import time
import uuid


def _init():
    """Initialise all store namespaces once per session."""
    defaults = {
        "db_users":        {},   # username -> {hash, salt, pub_key, priv_key, mfa_secret, avatar_color}
        "db_messages":     [],   # list of message dicts
        "db_files":        {},   # file_id -> {name, enc_bytes, sender, recipient, timestamp, size}
        "db_group_msgs":   [],   # group messages
        "current_user":    None,
        "chat_partner":    None,
        "active_tab":      "Messages",
        "mfa_pending":     None,
        "reg_keypair":     None,
        "notifications":   [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── USER OPERATIONS ──────────────────────────────────────────────────────────

def register_user(username: str, pw_hash: str, pw_salt: str,
                  pub_key: str, priv_key: str, mfa_secret: str,
                  avatar_color: str) -> bool:
    _init()
    if username in st.session_state["db_users"]:
        return False
    st.session_state["db_users"][username] = {
        "hash":         pw_hash,
        "salt":         pw_salt,
        "public_key":   pub_key,
        "private_key":  priv_key,   # stored client-side in session only
        "mfa_secret":   mfa_secret,
        "avatar_color": avatar_color,
        "joined":       time.time(),
    }
    return True


def get_user(username: str) -> dict | None:
    _init()
    return st.session_state["db_users"].get(username)


def list_users(exclude: str = None) -> list[str]:
    _init()
    return [u for u in st.session_state["db_users"] if u != exclude]


# ── MESSAGE OPERATIONS ────────────────────────────────────────────────────────

def save_message(sender: str, recipient: str, cipherblob: str, msg_type: str = "text") -> dict:
    _init()
    msg = {
        "id":        str(uuid.uuid4()),
        "sender":    sender,
        "recipient": recipient,
        "blob":      cipherblob,
        "type":      msg_type,
        "ts":        time.time(),
        "read":      False,
    }
    st.session_state["db_messages"].append(msg)
    return msg


def get_conversation(user_a: str, user_b: str) -> list[dict]:
    _init()
    return [
        m for m in st.session_state["db_messages"]
        if (m["sender"] == user_a and m["recipient"] == user_b) or
           (m["sender"] == user_b and m["recipient"] == user_a)
    ]


def mark_read(sender: str, recipient: str):
    _init()
    for m in st.session_state["db_messages"]:
        if m["sender"] == sender and m["recipient"] == recipient:
            m["read"] = True


def unread_count(recipient: str) -> dict:
    """Return {sender: count} of unread messages for recipient."""
    _init()
    counts = {}
    for m in st.session_state["db_messages"]:
        if m["recipient"] == recipient and not m["read"]:
            counts[m["sender"]] = counts.get(m["sender"], 0) + 1
    return counts


# ── FILE OPERATIONS ───────────────────────────────────────────────────────────

def save_file(sender: str, recipient: str, name: str,
              enc_bytes: bytes, original_size: int) -> str:
    _init()
    fid = str(uuid.uuid4())
    st.session_state["db_files"][fid] = {
        "name":      name,
        "enc_bytes": enc_bytes,
        "sender":    sender,
        "recipient": recipient,
        "ts":        time.time(),
        "size":      original_size,
    }
    return fid


def get_files_for(user: str) -> list[dict]:
    _init()
    result = []
    for fid, f in st.session_state["db_files"].items():
        if f["sender"] == user or f["recipient"] == user:
            result.append({"id": fid, **f})
    return sorted(result, key=lambda x: x["ts"], reverse=True)


# ── GROUP MESSAGES ────────────────────────────────────────────────────────────

def save_group_message(sender: str, text: str) -> dict:
    _init()
    msg = {"id": str(uuid.uuid4()), "sender": sender,
           "text": text, "ts": time.time()}
    st.session_state["db_group_msgs"].append(msg)
    return msg


def get_group_messages() -> list[dict]:
    _init()
    return st.session_state["db_group_msgs"]
