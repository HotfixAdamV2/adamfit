"""Home page: a welcome screen with a quick link to the profile page."""

import streamlit as st

from adamfit import auth

user = auth.current_user()

st.title(f"Welcome, {user['username']}")
st.write("Welcome to my personal fitness app.")
st.page_link("pages/profile.py", label="Log your weight on My Profile", icon=":material/monitor_weight:")
