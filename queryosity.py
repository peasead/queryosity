"""
Title: Research Search CLI Tool
Author: Andrew Pease
Repo: https://github.com/peasead/queryosity
Description:
    A command-line tool that uses Google Gemini (2.5 Pro via Vertex AI) to emulate
    Google Scholar searches and return research results in Markdown, JSON, or CSV.

    A complete Web of Science (WoS) integration block is included **but commented out**
    so you can enable it later by simply removing the comment markers (paid API needed).

    Note: Google Scholar does not allow for API access, so results are inferred
    using Google Gemini and may not reflect actual listings.
"""

# ────────────────────────────────────────────────────────────────────────────────
# Standard-library & 3rd-party imports
# ────────────────────────────────────────────────────────────────────────────────
import argparse
import asyncio
import csv
import json
import os
import re
import sys
from typing import List, Dict

from dotenv import load_dotenv
from tqdm import tqdm

# Vertex AI preview SDK (Gemini foundation models ≥ 1.5)
import vertexai
from vertexai.preview.generative_models import GenerativeModel

# Optional import for WoS (kept for later) → uncomment when WoS is enabled
# import requests

# ────────────────────────────────────────────────────────────────────────────────
# Environment / API keys
# ────────────────────────────────────────────────────────────────────────────────
load_dotenv()

PROJECT_ID = os.getenv("GEMINI_PROJECT_ID")          # e.g. my-gcp-proj-123
LOCATION   = os.getenv("GEMINI_LOCATION", "us-central1")
# WOS_API_KEY = os.getenv("WOS_API_KEY")            # ← needed only when WoS is enabled

if not PROJECT_ID:
    sys.exit("Error: GEMINI_PROJECT_ID missing in .env")

# ────────────────────────────────────────────────────────────────────────────────
# Initialise Vertex AI & Load Gemini 2.5 Pro model
# ────────────────────────────────────────────────────────────────────────────────
vertexai.init(project=PROJECT_ID, location=LOCATION)
MODEL_ID = "gemini-2.5-pro"  # NEW model
model: GenerativeModel = GenerativeModel(MODEL_ID)

# ═══════════════════════════════════════════════════════════════════════════════
# CLI ARGUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search academic research using Google Gemini / Google Scholar emulation.")

    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--query",      type=str, help="Query string or question.")
    src.add_argument("--input-file", type=str, help="File containing query text.")

    parser.add_argument("--results",  type=int, default=5,
                        help="Number of results to retrieve (Gemini only for now).")
    parser.add_argument("--sort",     choices=["relevance", "retrieved"], default="relevance",
                        help="Sort order for output.")
    parser.add_argument("--output",   type=str, help="Optional output filename (auto-detects .md/.json/.csv).")

    return parser.parse_args()

# ═══════════════════════════════════════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════════════════════════════════════

def read_query_text(args: argparse.Namespace) -> str:
    if args.query:
        return args.query.strip()
    with open(args.input_file, "r", encoding="utf-8") as fh:
        return fh.read().strip()

# ────────────────────────────────────────────────────────────────────────────────
# Gemini / Google-Scholar block
# ────────────────────────────────────────────────────────────────────────────────

async def gemini_scholar_search(query: str, max_results: int) -> List[Dict]:
    prompt = (
        f"Search Google Scholar for recent academic studies related to the following query:\n"
        f"'{query}'.\n"
        f"Provide the top {max_results} articles with this exact Markdown format:\n"
        f"<number>. [<Title>](<URL>)\n**Relevance:** <score>/10\n**Abstract:** <text>\n"
        f"Rate relevance from 1–10 where 10 is the most relevant."
    )

    try:
        resp = model.generate_content(prompt, generation_config={"temperature": 0.7})
        raw_md = resp.text

        pattern = re.compile(
            r"\d+\.\s\[(.*?)\]\((.*?)\)\s*\n\*\*Relevance:\*\*\s*(\d+)/10\n\*\*Abstract:\*\*\s*(.*?)\n",
            re.DOTALL,
        )
        entries = []
        for title, url, score, abstract in pattern.findall(raw_md):
            entries.append({
                "title": title.strip(),
                "link":  url.strip(),
                "relevance": int(score),
                "abstract": abstract.strip(),
                "source": "gemini",
            })
        return entries
    except Exception as exc:
        return [{
            "title": f"Gemini Error: {exc}",
            "link": "",
            "relevance": 0,
            "abstract": "",
            "source": "gemini",
        }]

# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT FORMATTERS
# ═══════════════════════════════════════════════════════════════════════════════

def format_md(entries: List[Dict]) -> str:
    md_lines: List[str] = []
    for idx, e in enumerate(entries, 1):
        md_lines.append(
            f"{idx}. [{e['title']}]({e['link'] or '#'})\n"
            f"**Relevance:** {e['relevance']}/10\n"
            + (f"**Year:** {e.get('year','')}\n" if e.get("year") else "")
            + f"**Abstract:** {e['abstract']}\n"
        )
    return "\n".join(md_lines)

def write_json(entries: List[Dict], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

def write_csv(entries: List[Dict], filepath: str) -> None:
    fieldnames = ["title", "link", "relevance", "abstract", "source"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in entries:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main() -> None:
    args = parse_args()
    query_text = read_query_text(args)

    gemini_results = await gemini_scholar_search(query_text, args.results)
    all_results = gemini_results

    if args.sort == "relevance":
        all_results.sort(key=lambda r: r.get("relevance", 0), reverse=True)

    # Determine output format by file extension or fallback to CLI Markdown
    if args.output:
        ext = os.path.splitext(args.output)[1].lower()
        if ext == ".json":
            write_json(all_results, args.output)
        elif ext == ".csv":
            write_csv(all_results, args.output)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("# Research Results\n\n" + format_md(all_results))
        print(f"\nSaved to {args.output}\n")
    else:
        print("# Research Results\n")
        print(format_md(all_results))
        print("\n*Note: Google Scholar does not allow for API access so results are inferred using Google Gemini 2.5 Pro and may not reflect actual listings.*\n")

if __name__ == "__main__":
    asyncio.run(main())
