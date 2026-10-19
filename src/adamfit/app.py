"""Streamlit entry point: decides which pages exist and runs the chosen one.

This script runs on every interaction. Logged-out visitors only get the login
page. Logged-in users get the full menu and a log-out button.
"""

import streamlit as st

from adamfit import auth

st.set_page_config(page_title="AdamFit", page_icon=":muscle:")

user = auth.current_user() if auth.current_user_id() is not None else None

if user is None:
    # Only clear a stale session (its user was deleted). Clearing on every
    # logged-out run would also wipe widget state, so the Log in button's
    # click would be lost before the login page could see it.
    if auth.current_user_id() is not None:
        auth.log_out()
    page = st.navigation(
        [st.Page("pages/login.py", title="Log in", icon=":material/login:")]
    )
else:
    page = st.navigation(
        {
            "Home": [
                st.Page("pages/home.py", title="Home", icon=":material/home:", default=True),
            ],
            "Me": [
                st.Page("pages/profile.py", title="My Profile", icon=":material/person:"),
            ],
            "Nutrition": [
                st.Page("pages/nutrition.py", title="Nutrition", icon=":material/restaurant:"),
            ],
            "Library": [
                st.Page("pages/exercises.py", title="Exercises", icon=":material/fitness_center:"),
            ],
        }
    )
    with st.sidebar:
        st.caption(f"Logged in as **{user['username']}**")
        if st.button("Log out", icon=":material/logout:"):
            auth.log_out()
            st.rerun()

page.run()
