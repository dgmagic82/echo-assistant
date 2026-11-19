"""Offline tests: no network, no API key. Run with `uv run pytest`."""

import json

import pytest
from langchain_core.documents import Document

from echo import chain, config, kb

DOC = """---
doc_id: 99
title: Тестовый документ
topic: тест
type: справка
---
# Тестовый документ

Назначение: строка до первого раздела в фрагменты не идёт.

## Первый раздел
Текст первого раздела.

## Пустой раздел

## Второй раздел
Текст второго раздела.
"""


def test_parse_doc_reads_front_matter():
    meta, body = kb.parse_doc(DOC)
    assert meta == {"doc_id": "99", "title": "Тестовый документ", "topic": "тест", "type": "справка"}
    assert body.lstrip().startswith("# Тестовый документ")


def test_parse_doc_rejects_missing_keys():
    with pytest.raises(ValueError, match="type"):
        kb.parse_doc(DOC.replace("type: справка\n", ""))


def test_split_doc_one_chunk_per_nonempty_section_with_citation():
    chunks = kb.split_doc(*kb.parse_doc(DOC))
    assert [c.metadata["section"] for c in chunks] == ["Первый раздел", "Второй раздел"]
    assert chunks[0].metadata["source"] == "Тестовый документ / Первый раздел"
    assert chunks[1].page_content.startswith("Тестовый документ\n## Второй раздел")
    assert "Назначение" not in chunks[0].page_content


def test_split_doc_splits_long_section():
    long = DOC.replace("Текст первого раздела.", "Длинное предложение про доставку пледа. " * 100)
    first = [c for c in kb.split_doc(*kb.parse_doc(long)) if c.metadata["section"] == "Первый раздел"]
    assert len(first) > 1 and all(len(c.page_content) < kb.MAX_CHUNK_CHARS + 200 for c in first)


def test_whole_kb_has_16_documents_with_sections():
    docs = kb.load_docs()
    assert [m["doc_id"] for m, _ in docs] == [f"{i:02d}" for i in range(1, 17)]
    for meta, body in docs:
        assert kb.sections(body), f"в документе {meta['doc_id']} нет разделов ##"


def test_always_on_docs_are_not_indexed():
    indexed = {c.metadata["doc_id"] for c in kb.load_chunks()}
    assert not indexed & set(config.ALWAYS_ON + config.NOT_INDEXED)
    assert [d.metadata["doc_id"] for d in kb.always_on_docs()] == list(config.ALWAYS_ON)


def test_templates_are_one_per_section():
    templates = [c for c in kb.load_chunks() if c.metadata["doc_id"] == "01"]
    assert len(templates) >= 18 and all(c.metadata["type"] == "шаблоны" for c in templates)


def _hit(doc_id, section):
    return (Document(page_content="x", metadata={"doc_id": doc_id, "title": f"Док {doc_id}", "section": section,
                                                 "path": f"{doc_id}_x.md", "source": f"Док {doc_id} / {section}"}), 0.1)


def test_resolve_sources_drops_unknown_and_duplicate_numbers():
    hits = [_hit("07", "весь документ"), _hit("04", "Брак")]
    out = chain.resolve_sources([2, 2, 0, 9, 1], hits)
    assert [(s["n"], s["doc_id"]) for s in out] == [(2, "04"), (1, "07")]
    assert out[0]["path"] == "04_x.md" and out[0]["section"] == "Брак"


def test_user_message_numbers_fragments_and_wraps_input():
    msg = chain.user_message("Плед полинял", [_hit("07", "весь документ"), _hit("04", "Брак")], "Ozon", 2)
    assert "[1] Документ 07." in msg and "[2] Документ 04." in msg
    assert "площадка: Ozon, оценка: 2 из 5" in msg
    assert msg.rstrip().endswith("<input>\nПлед полинял\n</input>")


def test_schema_enums_match_classification_doc():
    _, body = kb.get_doc("07")
    for value in ("позитивная", "смешанная", "жалоба", "предложение", "Сайт и оплата", "Общее впечатление"):
        assert value in body
    assert set(chain.Topic.__args__) <= set(dict(kb.sections(body))["Темы (одна или несколько)"].rstrip(".").split(", "))


def test_eval_set_has_15_inputs_and_demo_set():
    qs = json.loads((config.ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
    assert len(qs) == 15 and len({q["id"] for q in qs}) == 15
    assert sum(q["demo"] == "типовой" for q in qs) == 5 and sum(q["demo"] == "вне базы" for q in qs) == 2
    assert all(len(q["input"]) <= config.MAX_INPUT_CHARS for q in qs)


def test_prompt_has_no_placeholders():
    text = chain.system_prompt()
    assert "{{" not in text and "[уточнить у отдела]" in text and "[решение менеджера]" in text


def test_search_query_drops_product_and_names_marketplace():
    assert chain.search_query("Товар: Плед «Облако». Отзыв: «полинял»", "Ozon") == "Отзыв на Ozon. Отзыв: «полинял»"
    assert chain.search_query("Вопрос сотрудника: как стирать?", "сайт") == "Вопрос сотрудника: как стирать?"
