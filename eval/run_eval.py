"""Run the 15 eval inputs through the assistant and compare with the expected fields.

    uv run python eval/run_eval.py --retrieval   # search only: is the expected document among the fragments (embeddings, ~$0.0001)
    uv run python eval/run_eval.py               # full run through the model, writes eval/results.json
    ECHO_CHAT_MODEL=anthropic/claude-haiku-5.5 uv run python eval/run_eval.py --out results_haiku55.json

Field checks are automatic. Drafts, labels and invented facts are checked by reading results.json;
the verdicts go into eval/report.md by hand.
"""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from echo import chain, config, kb  # noqa: E402

HERE = Path(__file__).parent
PRICES = {"anthropic/claude-haiku-4.5": (1.00, 5.00), "anthropic/claude-haiku-5.5": (0.10, 0.50)}  # $ per 1M, OpenRouter 19.11.2026
CACHE_READ, CACHE_WRITE_1H = 0.1, 2.0  # Anthropic prompt cache multipliers of the input price


def cost(r) -> float:
    """tokens_in includes cached tokens; a cache read costs 0.1 of input, a 1-hour cache write 2.0."""
    p_in, p_out = PRICES[config.CHAT_MODEL]
    plain = r.tokens_in - r.cache_read - r.cache_write
    return (plain * p_in + r.cache_read * p_in * CACHE_READ + r.cache_write * p_in * CACHE_WRITE_1H
            + r.tokens_out * p_out) / 1e6


def field_ok(name: str, want, got) -> bool:
    if name == "department":  # free text from doc 08: a substring is enough
        return bool(got) and want.lower() in got.lower()
    return want == got


def main() -> None:
    qs = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    index = kb.load_index()
    retrieval_only = "--retrieval" in sys.argv
    rows, found_all = [], 0
    for q in qs:
        hits = chain.retrieve(index, q["input"], q["channel"])
        got_docs = {d.metadata["doc_id"] for d, _ in hits}
        found = all(d in got_docs for d in q["docs"])
        found_all += found
        row = {"id": q["id"], "kind": q["kind"], "retrieval_ok": found, "expected_docs": q["docs"],
               "retrieved": [f"{d.metadata['doc_id']} / {d.metadata['section']}" for d, _ in hits]}
        if not retrieval_only:
            r = chain.ask(q["input"], index, channel=q["channel"], stars=q["stars"])
            a = r.answer.model_dump()
            checks = {k: field_ok(k, v, a.get(k)) for k, v in q["expect"].items()}
            row |= {"answer": a, "sources": [f"{s['doc_id']} / {s['section']}" for s in r.sources],
                    "checks": checks, "latency_s": round(r.latency_ms / 1000, 1),
                    "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
                    "cache_read": r.cache_read, "cache_write": r.cache_write, "cost_usd": cost(r)}
        rows.append(row)
        status = "" if retrieval_only else (f"{sum(row['checks'].values())}/{len(row['checks'])} полей, "
                                            f"{row['latency_s']} с, {row['tokens_in']}→{row['tokens_out']} ток.")
        print(f"{q['id']:2} поиск {'да ' if found else 'НЕТ'} {status}", flush=True)
        if not found:
            print("   нашёл:", "; ".join(row["retrieved"]))

    print(f"\nпоиск нашёл ожидаемые документы: {found_all} из {len(qs)}")
    if retrieval_only:
        return
    fields = [c for r in rows for c in r["checks"].values()]
    lat = [r["latency_s"] for r in rows]
    summary = {
        "model": config.CHAT_MODEL, "retrieval_ok": found_all, "n": len(qs),
        "fields_ok": sum(fields), "fields_total": len(fields),
        "latency_median_s": statistics.median(lat), "latency_max_s": max(lat),
        "tokens_in_mean": round(statistics.mean(r["tokens_in"] for r in rows)),
        "tokens_out_mean": round(statistics.mean(r["tokens_out"] for r in rows)),
        "cache_read_mean": round(statistics.mean(r["cache_read"] for r in rows)),
        "cache_writes": sum(1 for r in rows if r["cache_write"]),
        "cost_usd_total": round(sum(r["cost_usd"] for r in rows), 4),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "results.json"
    (HERE / out).write_text(json.dumps({"summary": summary, "results": rows}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")


if __name__ == "__main__":
    main()
