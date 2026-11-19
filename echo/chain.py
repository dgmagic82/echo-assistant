"""Answer chain: retrieval → prompt → structured answer with sources.

Prompt layout:
    system = prompts/system.md + always-on docs as fragments [1..4]; the same in every request, so it is cached
    user   = search hits as fragments [5..N] + the input
"""

import re
import time
from dataclasses import dataclass, field
from typing import Literal

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from echo import config, kb

Kind = Literal["отзыв", "вопрос сотрудника", "вне рамок"]
Tonality = Literal["позитивная", "нейтральная", "негативная", "смешанная"]
ReviewType = Literal["жалоба", "благодарность", "предложение", "вопрос"]
Topic = Literal["Качество товара", "Описание и фото товара", "Доставка", "Упаковка", "Поддержка", "Цена",
                "Возврат и обмен", "Сайт и оплата", "Ассортимент", "Общее впечатление"]
Urgency = Literal["высокая", "средняя", "низкая"]
Special = Literal["нет", "оскорбления", "спам", "накрутка", "команда в отзыве"]


class EchoAnswer(BaseModel):
    kind: Kind = Field(description="Что прислал сотрудник")
    tonality: Tonality | None = Field(description="Тональность отзыва; null для вопроса сотрудника")
    review_type: ReviewType | None = Field(description="Тип отзыва; null для вопроса сотрудника")
    topics: list[Topic] = Field(description="Темы отзыва, одна или несколько; пусто для вопроса сотрудника")
    product: str | None = Field(description="Товар из отзыва или null")
    urgency: Urgency | None = Field(description="Срочность по справочнику; null для вопроса сотрудника")
    urgency_reason: str = Field(description="Одна фраза: почему такая срочность")
    department: str | None = Field(description="Кому передать, по документу маршрутизации")
    special_case: Special = Field(description="Особый случай по документу 09 или «нет»")
    draft: str = Field(description="Черновик ответа клиенту обычным текстом, или ответ на вопрос сотрудника, "
                                   "или «ответ не нужен»")
    team_note: str = Field(description="1–2 предложения для команды: что проверить, чего не хватает в базе")
    needs_human: bool = Field(description="В черновике есть метка [решение менеджера] или [уточнить у отдела]")
    sources: list[int] = Field(description="Номера фрагментов, на которые опирается ответ")


@dataclass
class EchoResult:
    answer: EchoAnswer
    sources: list[dict]
    retrieved: list[dict]
    latency_ms: int
    tokens_in: int = 0
    tokens_out: int = 0
    cache_read: int = 0
    cache_write: int = 0


def system_prompt() -> str:
    return (config.PROMPTS_DIR / "system.md").read_text(encoding="utf-8")


def search_query(text: str, channel: str | None = None) -> str:
    """The product name pulls care instructions over procedures, so it is cut; a marketplace is named,
    because replies there follow their own rules (doc 15)."""
    text = re.sub(r"^Товар: [^.]+\. ", "", text)
    return f"Отзыв на {channel}. {text}" if channel and channel != "сайт" else text


def retrieve(index, text: str, channel: str | None = None) -> list[tuple[Document, float | None]]:
    query = search_query(text, channel)
    # templates look like reviews and would crowd out the facts, so facts and templates get separate slots
    return ([(d, None) for d in kb.always_on_docs()]
            + kb.search(index, query, exclude_type="шаблоны")
            + kb.search(index, query, k=config.TEMPLATE_SLOTS, doc_type="шаблоны"))


def fragment(n: int, doc: Document) -> str:
    m = doc.metadata
    return f"[{n}] Документ {m['doc_id']}. {m['source']}\n{doc.page_content}"


def system_message(fixed: list) -> SystemMessage:
    """Prompt + always-on docs: identical in every request, so it carries a cache mark (1 hour)."""
    text = "\n\n".join([system_prompt(), "# Постоянные фрагменты базы знаний"]
                       + [fragment(i, d) for i, (d, _) in enumerate(fixed, 1)])
    return SystemMessage(content=[{"type": "text", "text": text, "cache_control": config.CACHE_CONTROL}])


def user_message(text: str, hits: list, channel: str | None = None, stars: int | None = None, start: int = 1) -> str:
    parts = ["Фрагменты базы знаний, найденные поиском:"]
    parts += [fragment(i, d) for i, (d, _) in enumerate(hits, start)]
    head = ", ".join(x for x in [channel and f"площадка: {channel}", stars and f"оценка: {stars} из 5"] if x)
    parts.append(f"Вход от сотрудника{f' ({head})' if head else ''}:\n<input>\n{text}\n</input>")
    return "\n\n".join(parts)


def resolve_sources(numbers: list[int], hits: list) -> list[dict]:
    """Turns the model's fragment numbers into citations; unknown numbers are dropped, not trusted."""
    out, seen = [], set()
    for n in numbers:
        if n in seen or not 1 <= n <= len(hits):
            continue
        seen.add(n)
        m = hits[n - 1][0].metadata
        out.append({"n": n, "doc_id": m["doc_id"], "title": m["title"], "section": m["section"],
                    "path": m["path"], "source": m["source"]})
    return out


def llm() -> ChatOpenAI:
    return ChatOpenAI(model=config.CHAT_MODEL, base_url=config.BASE_URL, api_key=config.api_key(),
                      temperature=config.TEMPERATURE, max_tokens=config.MAX_TOKENS, timeout=30, max_retries=1,
                      extra_body=config.EXTRA_BODY)


def ask(text: str, index, channel: str | None = None, stars: int | None = None,
        model: ChatOpenAI | None = None, method: str = "json_schema") -> EchoResult:
    started = time.perf_counter()
    hits = retrieve(index, text, channel)
    fixed = [h for h in hits if h[1] is None]  # always-on docs come first and have no search score
    messages = [system_message(fixed),
                HumanMessage(user_message(text, hits[len(fixed):], channel, stars, start=len(fixed) + 1))]
    out = ((model or llm()).with_structured_output(EchoAnswer, method=method, include_raw=True)
           .invoke(messages))
    if out["parsing_error"] or out["parsed"] is None:
        raise RuntimeError(f"Модель вернула ответ не по схеме: {out['parsing_error']}")
    usage = getattr(out["raw"], "usage_metadata", None) or {}
    raw_usage = (getattr(out["raw"], "response_metadata", None) or {}).get("token_usage") or {}
    details = raw_usage.get("prompt_tokens_details") or {}
    return EchoResult(
        answer=out["parsed"], sources=resolve_sources(out["parsed"].sources, hits),
        retrieved=[{"n": i, "source": d.metadata["source"], "doc_id": d.metadata["doc_id"],
                    "score": None if s is None else round(float(s), 4)} for i, (d, s) in enumerate(hits, 1)],
        latency_ms=int((time.perf_counter() - started) * 1000),
        tokens_in=usage.get("input_tokens", 0), tokens_out=usage.get("output_tokens", 0),
        cache_read=details.get("cached_tokens") or 0, cache_write=details.get("cache_write_tokens") or 0)
