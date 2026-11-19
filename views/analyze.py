"""Page «Разбор отзыва»: input → markup, draft and sources."""

import json

import streamlit as st

from echo import chain, config, kb

CHANNELS = ["сайт", "Ozon", "Wildberries", "Яндекс Маркет"]
EXAMPLES = [q for q in json.loads((config.ROOT / "eval" / "questions.json").read_text(encoding="utf-8")) if q["demo"]]


@st.cache_resource
def index():
    return kb.load_index()


def use_example(q: dict) -> None:
    st.session_state.text = q["input"]
    st.session_state.channel = q["channel"] or "сайт"
    st.session_state.stars = q["stars"] or 0


st.session_state.setdefault("used", 0)
st.session_state.setdefault("text", "")

st.title("💬 Эхо: разбор отзыва")
st.caption("Ассистент поддержки магазина «Лавка Тепла». Вставьте отзыв клиента или вопрос сотрудника: Эхо разметит "
           "отзыв, подготовит черновик ответа и покажет, из каких документов базы взяты факты. "
           "Черновик проверяет и публикует человек. Магазин и база учебные, вымышленные.")

st.write("Примеры:")
half = (len(EXAMPLES) + 1) // 2  # two rows, so the labels are not cut
cols = st.columns(half) + st.columns(half)
for col, q in zip(cols, EXAMPLES):
    label = ("вне базы: " if q["demo"] == "вне базы" else "") + q["kind"].split(": ", 1)[-1]
    col.button(label, key=f"ex{q['id']}", on_click=use_example, args=(q,), use_container_width=True)

text = st.text_area("Отзыв или вопрос", key="text", height=120, max_chars=config.MAX_INPUT_CHARS,
                    placeholder="Товар: Плед «Облако». Отзыв: «...»")
c1, c2, c3 = st.columns([2, 2, 1])
channel = c1.selectbox("Площадка", CHANNELS, key="channel")
stars = c2.select_slider("Оценка", options=[0, 1, 2, 3, 4, 5], key="stars",
                         format_func=lambda s: "не указана" if s == 0 else "★" * s)
left = config.MAX_REQUESTS_PER_SESSION - st.session_state.used
go = c3.button("Разобрать", type="primary", use_container_width=True, disabled=left <= 0)
if left <= 0:
    st.info(f"Лимит демо: {config.MAX_REQUESTS_PER_SESSION} разборов за сессию.")

if go:
    if not text.strip():
        st.warning("Вставьте текст отзыва или вопроса.")
        st.stop()
    with st.spinner("Ищу в базе знаний и готовлю ответ…"):
        try:
            r = chain.ask(text.strip(), index(), channel=channel, stars=stars or None)
        except Exception as e:
            st.error(f"Не получилось разобрать: {type(e).__name__}. Попробуйте ещё раз.")
            st.stop()
    st.session_state.used += 1
    a = r.answer

    if a.kind == "отзыв":
        m1, m2, m3 = st.columns(3)
        m1.metric("Тональность", a.tonality or "—")
        m2.metric("Тип", a.review_type or "—")
        m3.metric("Срочность", a.urgency or "—")
        st.write(f"**Кому передать:** {a.department or 'никому'}")
        st.write(f"**Темы:** {', '.join(a.topics) or 'нет'} · **Товар:** {a.product or 'не указан'}"
                 + (f" · **Особый случай:** {a.special_case}" if a.special_case != "нет" else ""))
        st.caption(f"Почему такая срочность: {a.urgency_reason}")
    if a.needs_human:
        st.warning("В ответе есть метка для человека: [уточнить у отдела] или [решение менеджера].")

    st.subheader("Черновик ответа" if a.kind == "отзыв" else "Ответ")
    st.text_area("Черновик", a.draft, height=160, label_visibility="collapsed")
    st.write(f"**Заметка для команды:** {a.team_note}")

    st.subheader("Источники")
    if not r.sources:
        st.caption("Ответ не опирается на документы базы.")
    repo = config.repo_url()
    for s in r.sources:
        c_link, c_git = st.columns([4, 1]) if repo else (st.container(), None)  # full width when there is no GitHub link
        c_link.page_link("views/docs.py", label=f"[{s['n']}] Документ {s['doc_id']}. {s['source']}", icon="📄",
                         query_params={"doc": s["doc_id"], "section": s["section"]})
        if repo:
            c_git.markdown(f"[файл на GitHub]({repo}/kb/{s['path']})")

    st.caption(f"Время ответа {r.latency_ms / 1000:.1f} с · токены {r.tokens_in} → {r.tokens_out}"
               f" (из кэша {r.cache_read}) · модель {config.CHAT_MODEL}")
    with st.expander("Что нашёл поиск"):
        for h in r.retrieved:
            score = "целиком в каждом запросе" if h["score"] is None else f"расстояние {h['score']}"
            st.write(f"[{h['n']}] Документ {h['doc_id']}. {h['source']} ({score})")
