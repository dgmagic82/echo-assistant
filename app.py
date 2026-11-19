"""Эхо: entry point.

    uv run streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Эхо: разбор отзывов", page_icon="💬", layout="wide")
st.navigation([st.Page("views/analyze.py", title="Разбор отзыва", icon="💬", default=True),
               st.Page("views/docs.py", title="База знаний", icon="📚", url_path="docs")]).run()
