# paperless-tag-no-ocr — Dokumente ohne OCR-Text markieren

Paperless und der paperless-ai-Index zeigen unterschiedliche Dokumentzahlen, weil
Dokumente **ohne Text** (Fotos, Scans ohne OCR) bewusst nicht eingebettet werden
(`scripts/sync_paperless.py` verwirft leeren `content`). Dieses Tool macht die
Differenz in Paperless selbst sichtbar: es setzt einen Sammel-Tag auf alle
Dokumente mit leerem `content`.

Der Tag wird mit `matching_algorithm: 0` (keins) angelegt — er greift also nie
automatisch bei neuen Dokumenten, sondern nur über dieses Tool.

## Nutzung (MCP-Tool `paperless_tag_no_ocr`)

```jsonc
// Trockenlauf — wie viele Dokumente haben keinen Text?
{}

// Anwenden: Tag anlegen (falls nötig), setzen und veraltete Tags entfernen
{ "apply": true }

// Anderer Tag-Name / anderer Host
{ "apply": true, "tag_name": "kein Text", "host": "mystorage" }
```

Idempotent: mehrfaches Ausführen ändert nichts Zusätzliches. Bekommt ein
Dokument nachträglich Text (OCR-Nachlauf), entfernt der nächste Lauf den Tag
dort wieder (`untagged`).

## Wie es läuft

`run.sh` pipet `tag_no_ocr.py` per `ssh <host> docker exec -i <container> python -`
in den **paperless-ai-Container**. Der bringt `PAPERLESS_URL`, `PAPERLESS_TOKEN`
und `httpx` bereits mit — die Registry braucht deshalb keinerlei
Paperless-Credentials. Geschrieben wird über `POST /api/documents/bulk_edit/`
in 100er-Batches.

Voraussetzungen: SSH-Zugang zum Docker-Host, laufender `paperless-ai`-Container.
