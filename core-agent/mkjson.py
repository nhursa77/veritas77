# -*- coding: utf-8 -*-
r"""
mkjson.py — pretvori .md tekst (Članak X ...) u standardizirani JSON (schema_version 1.1)
Kompatibilno s ustav.json strukturom iz Veritas H.77 core-agenta.

Uporaba (PowerShell):
  cd C:\veritas-agent\core-agent
  python .\mkjson.py --in "data\Opca_deklaracija_o_ljudskim_pravima_Veritas.md" --doc-id udhr --title "Opća deklaracija o ljudskim pravima (UN, 1948)" --out "data\udhr.json"
  python .\mkjson.py --in "data\medjunarodni_pakt_o_gradjanskim_pravima_txt.md" --doc-id iccpr --title "Međunarodni pakt o građanskim i političkim pravima" --out "data\iccpR.json"
  python .\mkjson.py --in "data\medjunarodni_pakt_o_gospodarskim_socijalnim_i_kulturnim_pravima_txt.md" --doc-id icescr --title "Međunarodni pakt o gospodarskim, socijalnim i kulturnim pravima" --out "data\icescr.json"
"""
from __future__ import annotations
import argparse, json, re, hashlib, os, datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

ARTICLE_RE = re.compile(
    r'^\s*[#>\-*\s]*([ČC]lanak)\s+([0-9]+[a-z]?)(?:\s*[\.\:])?\s*$', re.IGNORECASE
)
PART_RE    = re.compile(r'^\s*(DIO)\s+([IVXLCDM]+)\b', re.IGNORECASE)
CHAPTER_RE = re.compile(r'^\s*(GLAVA|POGLAVLJE)\s+([0-9IVXLCDM]+)\b', re.IGNORECASE)
SECTION_RE = re.compile(r'^\s*(ODJELJAK|ODJEL|ODJELAK)\s+([0-9IVXLCDM]+)\b', re.IGNORECASE)

def sha256_of_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def norm(s: str) -> str:
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    lines = [ln.strip() for ln in s.split('\n')]
    out: List[str] = []
    buf: List[str] = []
    for ln in lines:
        if not ln:
            if buf:
                out.append(' '.join(buf).strip())
                buf = []
            continue
        buf.append(ln)
    if buf:
        out.append(' '.join(buf).strip())
    return '\n\n'.join(out).strip()

def make_aliases(n: str) -> List[str]:
    base = n.lower()
    return [
        f"članak {base}", f"clanak {base}", f"čl. {base}", f"cl. {base}",
        f"čl {base}", f"cl {base}", base
    ]

def parse_md_to_articles(text: str) -> List[Dict[str, Any]]:
    lines = text.splitlines()
    cur_part = None; cur_chap = None; cur_sect = None
    articles: List[Dict[str, Any]] = []
    cur_num: Optional[str] = None
    cur_buf: List[str] = []

    def flush():
        nonlocal cur_num, cur_buf, cur_part, cur_chap, cur_sect
        if cur_num is None: return
        art_text = norm('\n'.join(cur_buf))
        entry: Dict[str, Any] = {
            "id": f"cl-{cur_num}",
            "number": cur_num,
            "label": f"čl. {cur_num}",
            "title": "",
            "text": art_text,
            "meta": {
                "part": cur_part,
                "chapter": cur_chap,
                "section": cur_sect,
                "aliases": make_aliases(cur_num)
            }
        }
        articles.append(entry)
        cur_num, cur_buf = None, []

    for raw in lines:
        if PART_RE.match(raw):
            m = PART_RE.match(raw); cur_part = f"{m.group(1).title()} {m.group(2)}"; continue
        if CHAPTER_RE.match(raw):
            m = CHAPTER_RE.match(raw); cur_chap = f"{m.group(1).title()} {m.group(2)}"; continue
        if SECTION_RE.match(raw):
            m = SECTION_RE.match(raw); cur_sect = f"{m.group(1).title()} {m.group(2)}"; continue

        m = ARTICLE_RE.match(raw)
        if m:
            flush()
            cur_num = m.group(2)
            cur_buf = []
        else:
            cur_buf.append(raw)
    flush()
    return [a for a in articles if a["text"]]

def build_json(md_path: Path, doc_id: str, title: str, lang: str="hr") -> Dict[str, Any]:
    raw = md_path.read_text(encoding="utf-8", errors="ignore")
    articles = parse_md_to_articles(raw)
    index = { a["number"]: a["id"] for a in articles }
    meta = {
        "schema_version": "1.1",
        "doc": {
            "doc_id": doc_id,
            "title": title,
            "lang": lang,
            "source_path": str(md_path),
            "hash_sha256": sha256_of_file(md_path),
            "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "publisher": "UN / RH (prevedeni tekstovi)",
            "license": "Referentni tekst za pravnu obradu; bez jamstva."
        },
        "retrieval": {
            "unit": "article",
            "strict_citation": True,
            "id_prefix": "cl-"
        }
    }
    return {"meta": meta, "index": index, "articles": articles}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Put do .md izvora")
    ap.add_argument("--doc-id", required=True, help="Kratki ID dokumenta (npr. udhr/iccpR/icescr)")
    ap.add_argument("--title", required=True, help="Naslov dokumenta")
    ap.add_argument("--lang", default="hr", help="Jezik (default: hr)")
    ap.add_argument("--out", dest="outp", required=True, help="Put do izlaznog .json")
    args = ap.parse_args()

    inp = Path(args.inp); outp = Path(args.outp)
    outp.parent.mkdir(parents=True, exist_ok=True)

    data = build_json(inp, args.doc_id, args.title, lang=args.lang)
    with outp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Generirano: {outp}  | članka: {len(data['articles'])}")
    print(f"    sha256 src: {data['meta']['doc']['hash_sha256']}")
    if data["articles"]:
        a0 = data["articles"][0]
        print(f"    Primjer: {a0['label']} → {a0['text'][:120].replace('\\n',' ')} ...")

if __name__ == "__main__":
    main()
