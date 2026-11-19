"""Page «База знаний»: one document, opened from a source link (?doc=05&section=...)."""

import streamlit as st

from echo import kb

docs = kb.load_docs()
ids = [m["doc_id"] for m, _ in docs]
wanted = st.query_params.get("doc")
doc_id = st.selectbox("Документ", ids, index=ids.index(wanted) if wanted in ids else 0,
                      format_func=lambda i: f"{i}. {next(m['title'] for m, _ in docs if m['doc_id'] == i)}")
meta, body = next((m, b) for m, b in docs if m["doc_id"] == doc_id)
st.caption(f"Файл kb/{meta['path']} · тип: {meta['type']} · тема: {meta['topic']}")

section = st.query_params.get("section") if doc_id == wanted else None
if section:
    text = dict(kb.sections(body)).get(section)
    if text:
        st.info(f"**Раздел, на который сослался ассистент: {section}**\n\n{text}")
st.markdown(body)
