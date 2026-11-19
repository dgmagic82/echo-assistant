"""Rebuild the vector index from kb/.

    uv run python ingest.py            # parse, embed, save to index/
    uv run python ingest.py --dry-run  # parse and print stats only, no API calls

Run it after any change in kb/. Embedding the whole base costs well under $0.01.
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone

from echo import config, kb


def main() -> None:
    docs = kb.load_docs()
    chunks = kb.load_chunks()
    by_type = Counter(c.metadata["type"] for c in chunks)
    print(f"документов: {len(docs)} (целиком в каждый запрос: {', '.join(config.ALWAYS_ON)}), "
          f"фрагментов в индексе: {len(chunks)}, по типам: {dict(by_type)}")
    print(f"самый длинный фрагмент: {max(len(c.page_content) for c in chunks)} символов")
    if "--dry-run" in sys.argv:
        return
    index = kb.build_index(chunks)
    index.save_local(str(config.INDEX_DIR))
    (config.INDEX_DIR / "manifest.json").write_text(json.dumps({
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "embed_model": config.EMBED_MODEL,
        "documents": [m["doc_id"] for m, _ in docs],
        "chunks": len(chunks),
        "chunks_by_type": by_type,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"индекс сохранён в {config.INDEX_DIR}")


if __name__ == "__main__":
    main()
