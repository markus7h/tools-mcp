"""Taggt Paperless-Dokumente ohne OCR-Text und raeumt den Tag wieder ab,
sobald ein Dokument doch Text bekommen hat (z.B. nach einem OCR-Nachlauf).

Laeuft IM paperless-ai-Container (nutzt dessen PAPERLESS_URL/PAPERLESS_TOKEN).
Fortschritt nach stderr, Ergebnis als eine JSON-Zeile nach stdout.
"""
import json
import os
import sys

import httpx

APPLY = "--apply" in sys.argv
TAG_NAME = os.getenv("TAG_NAME", "ohne OCR-Text")
BATCH = 100  # ponytail: bulk_edit statt N Einzel-PATCHes; 100er-Payloads bleiben klein

url = os.environ["PAPERLESS_URL"].rstrip("/")
headers = {"Authorization": "Token " + os.environ["PAPERLESS_TOKEN"]}
verify = os.getenv("PAPERLESS_VERIFY_SSL", "true").lower() != "false"


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def bulk(client, ids, *, add=None, remove=None):
    for i in range(0, len(ids), BATCH):
        batch = ids[i:i + BATCH]
        r = client.post(f"{url}/api/documents/bulk_edit/", json={
            "documents": batch,
            "method": "modify_tags",
            "parameters": {"add_tags": add or [], "remove_tags": remove or []},
        })
        r.raise_for_status()
        log(f"  {i + len(batch)}/{len(ids)}")


with httpx.Client(headers=headers, timeout=120, verify=verify, follow_redirects=True) as c:
    r = c.get(f"{url}/api/tags/", params={"name__iexact": TAG_NAME})
    r.raise_for_status()
    found = r.json().get("results") or []
    tag_id = found[0]["id"] if found else None

    # Alle Dokumente einmal durchgehen: Text vorhanden? Tag bereits gesetzt?
    empty, tagged_with_text, page = [], [], 1
    while True:
        r = c.get(f"{url}/api/documents/", params={"page_size": 250, "page": page})
        r.raise_for_status()
        data = r.json()
        for d in data["results"]:
            has_text = bool((d.get("content") or "").strip())
            if not has_text:
                empty.append(d["id"])
            elif tag_id is not None and tag_id in (d.get("tags") or []):
                tagged_with_text.append(d["id"])
        if not data.get("next"):
            break
        page += 1

    log(f"Dokumente ohne Text: {len(empty)}")
    if tagged_with_text:
        log(f"Tag veraltet (Dokument hat inzwischen Text): {len(tagged_with_text)}")

    result = {
        "documents_without_text": len(empty),
        "stale_tags": len(tagged_with_text),
        "tag_id": tag_id,
        "tag_name": TAG_NAME,
        "applied": APPLY,
        "tagged": 0,
        "untagged": 0,
    }

    if not APPLY:
        log("Trockenlauf — nichts geaendert.")
        print(json.dumps(result))
        sys.exit(0)

    if tag_id is None:
        r = c.post(f"{url}/api/tags/", json={
            "name": TAG_NAME, "matching_algorithm": 0, "color": "#a6a6a6",
        })
        r.raise_for_status()
        tag_id = r.json()["id"]
        result["tag_id"] = tag_id
        log(f"Tag '{TAG_NAME}' angelegt (id={tag_id})")

    if empty:
        log("Tagge Dokumente ohne Text ...")
        bulk(c, empty, add=[tag_id])
        result["tagged"] = len(empty)
    if tagged_with_text:
        log("Entferne veraltete Tags ...")
        bulk(c, tagged_with_text, remove=[tag_id])
        result["untagged"] = len(tagged_with_text)

    r = c.get(f"{url}/api/documents/", params={"tags__id__all": tag_id, "page_size": 1})
    r.raise_for_status()
    result["documents_with_tag"] = r.json()["count"]
    log(f"Kontrolle: {result['documents_with_tag']} Dokumente tragen '{TAG_NAME}'")

print(json.dumps(result))
