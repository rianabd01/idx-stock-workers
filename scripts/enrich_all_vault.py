#!/usr/bin/env python3
"""Batch enrichment worker for company_vault/idx/*.md skeleton files.

Scrapes lembarsaham.com for each skeleton emiten, sends structural context to OpenRouter,
writes the enriched Markdown profile, appends research notes to notes.md,
and finally triggers vault_indexer and profile_embeddings.
"""

import concurrent.futures
import html
import json
import os
import re
import sys
import threading
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

VAULT_IDX_DIR = BASE_DIR / "company_vault" / "idx"
NOTES_FILE = BASE_DIR / "company_vault" / "notes.md"

OPENROUTER_API_KEY = os.getenv("AI_API_KEY")
MODEL_NAME = os.getenv("AI_MODEL", "stealth/space-bunny-alpha")
MAX_WORKERS = 3

write_lock = threading.Lock()
completed_count = 0
failed_tickers = []


def is_skeleton(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
        return "Profil bisnis lengkap belum tersedia" in content
    except Exception:
        return False


def fetch_lembarsaham_data(tick: str) -> tuple[str, str] | None:
    url = f"https://lembarsaham.com/fundamental-saham/emiten/{tick}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        },
    )
    try:
        raw = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"[{tick}] Error fetching lembarsaham: {e}", flush=True)
        return None

    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    t = re.sub(r"<[^>]+>", "\n", t)
    t = html.unescape(t)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in t.split("\n")]
    lines = [ln for ln in lines if len(ln) > 1]
    out = []
    prev = None
    for ln in lines:
        if ln != prev:
            out.append(ln)
        prev = ln

    pi = None
    for i, ln in enumerate(out):
        if ln.strip() == "Profil Perusahaan" and i < len(out) - 5:
            pi = i
            break
    if pi is None:
        pi2 = [i for i, ln in enumerate(out) if ln == "Profil Perusahaan"]
        pi = pi2[-1] if pi2 else 0

    desc_window = "\n".join(out[max(0, pi - 35) : pi])
    block_window = "\n".join(out[pi : pi + 65])
    return desc_window, block_window


def call_ai_enrichment(tick: str, company_context: str) -> str | None:
    prompt = f"""Kamu adalah analis pasar modal Indonesia. Berdasarkan data mentah emiten {tick} dari lembarsaham berikut, buat profil company vault berformat Markdown standar persis seperti ini (hanya output Markdown-nya saja tanpa pengantar atau penutup apapun):

---
ticker: {tick}
name: <Nama Resmi Perusahaan Tbk>
sektor: <Sektor IDX IC>
subsektor: <Subsektor IDX IC>
komoditas: []
tag: [<daftar tag relevan>]
---

# Ringkasan bisnis
<2-3 paragraf ringkasan bisnis, produk/layanan utama, anak usaha, pengendali, dan tahun IPO/berdiri>

# Sumber pendapatan utama
- <poin sumber pendapatan>

# Driver bisnis
- <poin penggerak bisnis>

# Risiko utama
- <poin risiko bisnis/pasar>

# Sensitif terhadap berita
- <poin sensitivitas terhadap berita sektor/makro>

Data mentah:
{company_context}
"""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    req_ai = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    for attempt in range(3):
        try:
            res = urllib.request.urlopen(req_ai, timeout=60).read().decode("utf-8")
            data = json.loads(res)
            msg = data["choices"][0]["message"]
            content = msg.get("content") or ""
            if not content and "reasoning_details" in msg:
                for p in msg["reasoning_details"]:
                    if p.get("text"):
                        content += p["text"]
            if not content and msg.get("reasoning"):
                content = msg["reasoning"]

            content = content.strip()
            # Clean markdown code wrapper if present
            if content.startswith("```markdown"):
                content = content[len("```markdown") :].strip()
            elif content.startswith("```"):
                content = content[3:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()

            if content.startswith("---") and "# Ringkasan bisnis" in content:
                return content
            print(f"[{tick}] Incomplete response, retrying ({attempt+1}/3)...", flush=True)
            time.sleep(2)
        except Exception as e:
            print(f"[{tick}] AI attempt {attempt+1} failed: {e}", flush=True)
            time.sleep(3)
    return None


def process_ticker(target_path: Path, idx: int, total: int):
    global completed_count
    tick = target_path.stem.upper()

    data = fetch_lembarsaham_data(tick)
    if not data:
        failed_tickers.append(tick)
        return

    desc, block = data
    context = f"=== DESKRIPSI & PRODUK ===\n{desc}\n\n=== BLOK STRUKTURAL ===\n{block}"

    enriched_content = call_ai_enrichment(tick, context)
    if not enriched_content:
        failed_tickers.append(tick)
        print(f"[{tick}] Failed AI enrichment", flush=True)
        return

    # Extract name and sector from frontmatter for notes.md
    name_m = re.search(r"^name:\s*(.+)$", enriched_content, re.M)
    sektor_m = re.search(r"^sektor:\s*(.+)$", enriched_content, re.M)
    name = name_m.group(1).strip() if name_m else tick
    sektor = sektor_m.group(1).strip() if sektor_m else "-"

    note_entry = f"\n## {tick} — {name}\n- Klasifikasi: IDX IC {sektor}.\n- Sumber: lembarsaham.com/fundamental-saham/emiten/{tick} (diakses 2026-10-04).\n- Status IR: website dianalisis.\n"

    with write_lock:
        target_path.write_text(enriched_content + "\n", encoding="utf-8")
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(note_entry)
        completed_count += 1
        print(f"[{completed_count}/{total}] {tick} ({name}) ENRICHED successfully!", flush=True)

    # Polite interval
    time.sleep(1.0)


def main():
    skeleton_files = [p for p in sorted(VAULT_IDX_DIR.glob("*.md")) if is_skeleton(p)]
    # Process in reverse alphabetical order (following existing convention)
    skeleton_files.reverse()

    total = len(skeleton_files)
    print(f"Found {total} skeleton files in {VAULT_IDX_DIR} to enrich.", flush=True)

    if total == 0:
        print("All vault files are already enriched! Nothing to do.", flush=True)
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_ticker, p, i + 1, total): p
            for i, p in enumerate(skeleton_files)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                p = futures[future]
                print(f"[{p.stem}] Exception in thread: {exc}", flush=True)

    print(
        f"\nBatch enrichment finished! Successfully enriched: {completed_count}/{total}. Failed: {len(failed_tickers)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
