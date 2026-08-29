#!/usr/bin/env python3
"""Regressionstest: Tabellenzeilen dürfen den Seitenumbruch nicht zerreißen.

Braucht einen laufenden Konvertier-Dienst und pdftotext (poppler).
    python3 convert-service/test_tables.py [http://localhost:3458]
"""
import re, subprocess, sys, urllib.request

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3458").rstrip("/")
ROWS = 25
md = "# Tabellentest\n\n| Gegner | Az | Antrag | Stand |\n|---|---|---|---|\n" + "\n".join(
    f"| Proxalto Lebensversicherung AG Niederlassung Nummer {i} mit langem Namen "
    f"| F17458{i:02d} | 01.02.2025 | MARK{i:02d}START "
    + " ".join(f"Sachstand{i}-{k}" for k in range(1, 26))
    + f" MARK{i:02d}ENDE |"
    for i in range(1, ROWS + 1)
) + "\n"

fails = []
for design in ("magic3", "collana", "magicM"):
    req = urllib.request.Request(f"{URL}/md_to_pdf?design={design}", data=md.encode())
    pdf = urllib.request.urlopen(req, timeout=60).read()
    text = subprocess.run(["pdftotext", "-layout", "-", "-"], input=pdf,
                          capture_output=True).stdout.decode()
    pages = text.split("\f")[:-1]
    # Zeile i ist zerrissen, wenn Anfang und Ende auf verschiedenen Seiten landen
    split = [i for i in range(1, ROWS + 1)
             if {n for n, p in enumerate(pages) if f"MARK{i:02d}START" in p}
             != {n for n, p in enumerate(pages) if f"MARK{i:02d}ENDE" in p}]
    # Kopfzeile muss auf jeder Seite wiederholt werden
    nohdr = [n + 1 for n, p in enumerate(pages) if "Gegner" not in p]
    print(f"{design}: {len(pages)} Seiten, zerrissen: {split or '-'}, ohne Kopf: {nohdr or '-'}")
    if split or nohdr:
        fails.append(design)

assert not fails, f"Seitenumbruch defekt in: {fails}"
print("OK")
