# Chat: Gotenberg & Tika in der Paperless-Installation

*Datum: 13. Juli 2026*

---

## Frage 1

**User:** Was macht Gotenberg in der Paperless-Installation?

**Claude:**

Gotenberg ist in einer Paperless-ngx-Installation der Dienst, der **Office- und andere Nicht-PDF-Dokumente in PDFs umwandelt**.

Konkret läuft das so: Paperless selbst kann von Haus aus nur PDFs und Bilder (per OCR über Tesseract) verarbeiten. Wenn du aber z. B. eine `.docx`-, `.odt`-, `.xlsx`- oder `.pptx`-Datei in den Consume-Ordner legst oder per E-Mail empfängst, schickt Paperless diese Datei an den Gotenberg-Container. Gotenberg nutzt intern LibreOffice bzw. Chromium, um daraus ein PDF zu erzeugen, und gibt das an Paperless zurück. Das PDF wird dann als Archivversion des Dokuments gespeichert, während das Original erhalten bleibt.

Typische Aufgaben von Gotenberg in dem Setup:

- Konvertierung von Office-Dokumenten (Word, Excel, PowerPoint, LibreOffice-Formate) zu PDF
- Konvertierung von E-Mails (zusammen mit Tika, das oft als zweiter Container daneben läuft): Tika parst die E-Mail-Inhalte, Gotenberg rendert daraus das PDF
- HTML-zu-PDF-Rendering über die eingebaute Chromium-Engine

Deshalb tauchen in den meisten `docker-compose`-Dateien für Paperless-ngx die beiden Container `gotenberg` und `tika` gemeinsam auf — sie werden über die Umgebungsvariablen `PAPERLESS_TIKA_ENABLED`, `PAPERLESS_TIKA_GOTENBERG_ENDPOINT` und `PAPERLESS_TIKA_ENDPOINT` eingebunden.

Kurz gesagt: Ohne Gotenberg kann Paperless nur PDFs und Bilder konsumieren. Mit Gotenberg (+ Tika) kann es auch Office-Dateien und E-Mails archivieren. Wenn du das nicht brauchst, kannst du die beiden Container auch weglassen.

---

## Frage 2

**User:** Kann ich die Funktionen des Gotenberg- bzw. Tika-Containers auch über meine Tools-Registry nutzen, statt dafür den eigenen Tools-Convert-Container zu nutzen?

**Claude:**

Grundsätzlich ja — mit einer wichtigen Einschränkung, die von deinem Setup abhängt.

Gotenberg und Tika sind beides **eigenständige, zustandslose HTTP-APIs**. Paperless ist nur einer von vielen möglichen Clients. Es gibt keine spezielle Kopplung: Paperless schickt einfach HTTP-Requests an die konfigurierten Endpoints (`PAPERLESS_TIKA_GOTENBERG_ENDPOINT` und `PAPERLESS_TIKA_ENDPOINT`). Das heißt umgekehrt auch:

- Du kannst **einen zentralen Gotenberg-/Tika-Container** betreiben und ihn von Paperless *und* deinen anderen Tools gemeinsam nutzen lassen — statt pro Stack einen eigenen Convert-Container laufen zu lassen. Beide Dienste sind stateless, brauchen keine Volumes und skalieren problemlos für mehrere Clients.
- Voraussetzung ist nur, dass die Container sich netzwerktechnisch erreichen (gemeinsames Docker-Netzwerk oder erreichbare interne URL).

Die Einschränkung: Deine anderen Tools müssen die **jeweilige API sprechen**. Gotenberg hat eine eigene API (z. B. `POST /forms/libreoffice/convert` mit Multipart-Upload), Tika ebenfalls (`PUT /tika`, `PUT /rmeta` etc.). Wenn dein bisheriger `tools-convert`-Container eine andere API anbietet (etwa Stirling-PDF, ein eigenes Skript oder eine andere Konvertierungs-API), sind die Aufrufe nicht 1:1 austauschbar — dann müsstest du entweder die Clients anpassen oder einen kleinen Adapter davorsetzen. Umgekehrt gilt dasselbe: Paperless kann *nur* mit echtem Gotenberg/Tika reden, du kannst ihm nicht einfach einen anderen Konverter unterschieben.

Praktisch heißt das: Wenn dein Ziel ist, Duplikate zu vermeiden, ist der sauberste Weg meist, Gotenberg (und ggf. Tika) als zentralen Shared Service in deiner Tools-Registry zu führen und Paperless per Endpoint-Variable darauf zeigen zu lassen.

Was genau ist dein `tools-convert`-Container bzw. was meinst du mit Tools-Registry — ein eigener Stack mit z. B. Stirling-PDF, oder etwas Selbstgebautes? Dann kann ich dir konkreter sagen, ob die APIs kompatibel sind.
