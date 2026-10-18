"""Streamlit entry point: the home page."""

import streamlit as st

from adamfit.db import fetch_all, get_pool

st.set_page_config(page_title="AdamFit", page_icon=":muscle:")

st.title("AdamFit")
st.write("Welcome to my personal fitness app.")

try:
    get_pool()  # create the shared connection pool on first run
    fetch_all("SELECT 1 AS ok")
    st.success("Connected to the database.")
except Exception as exc:
    st.error(f"Could not connect to the database: {exc}")
