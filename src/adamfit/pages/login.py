"""Login page: the only page available until someone logs in."""

import streamlit as st

from adamfit import auth

st.title("AdamFit")
st.subheader("Log in")

with st.form("login_form"):
    username = st.text_input("Username", autocomplete="username")
    password = st.text_input("Password", type="password", autocomplete="current-password")
    submitted = st.form_submit_button("Log in", type="primary")

if submitted:
    try:
        user_id = auth.authenticate(username, password)
    except Exception as exc:
        st.error(f"Could not reach the database: {exc}")
        st.stop()

    if user_id is None:
        st.error("Incorrect username or password.")
    else:
        auth.log_in(user_id)
        st.rerun()

st.caption("No account yet? Create one from a terminal: `uv run adamfit-create-user <username>`")
