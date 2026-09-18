#!/usr/bin/env python3
"""Progressively route a user query to the smallest useful Jargon knowledge set."""
from __future__ import annotations
import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel: str):
    with (ROOT / rel).open(encoding="utf-8") as f:
        return json.load(f)

def normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).lower().strip()

def chunks(value: str) -> list[str]:
    text = normalize(value)
    # Keep Chinese runs and latin/digit words; substring matching handles short Chinese phrases.
    return re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9][a-z0-9+.#:/-]*", text)

def score(query: str, keywords: list[str]) -> int:
    q = normalize(query)
    q_tokens = [token for token in chunks(q) if len(token) >= 3 or any("\u4e00" <= char <= "\u9fff" for char in token)]
    points = 0
    for keyword in keywords:
        candidate = normalize(keyword)
        if candidate in q and (len(candidate) >= 3 or any("\u4e00" <= char <= "\u9fff" for char in candidate)):
            points += 3
            continue
        # Chinese requests often contain a shorter phrase inside a descriptive
        # keyword (e.g. “高可用” inside “高可用模式”). Use overlapping bigrams
        # instead of a heavyweight tokenizer.
        if (
            any("\u4e00" <= char <= "\u9fff" for char in candidate)
            and any(candidate[i : i + 2] in q for i in range(0, max(0, len(candidate) - 1), 1))
            and len(candidate) >= 2
        ):
            points += 2
            continue
        points += sum(1 for token in q_tokens if token in candidate)
    return points

def main() -> None:
    parser = argparse.ArgumentParser(description="Progressive Jargon runtime query")
    parser.add_argument("query", nargs="+", help="user request")
    parser.add_argument("--max-leaves", type=int, default=None)
    parser.add_argument("--max-entries", type=int, default=None)
    args = parser.parse_args()
    query = " ".join(args.query)
    root = load("index/root.json")
    runtime = load("index/runtime.json")
    limits = root["loading_policy"]
    max_leaves = args.max_leaves or limits["max_leaf_packages"]
    max_entries = args.max_entries or limits["max_entries_per_leaf"]

    ranked = []
    for route in runtime["routes"]:
        route_score = score(query, route["keywords"])
        if route_score:
            ranked.append((route_score, route))
    ranked.sort(key=lambda pair: (-pair[0], pair[1]["entry_count"], pair[1]["leaf_id"]))

    # If the query is broad, use the first matching routes only; never dump the whole index.
    selected = ranked[:max_leaves]
    selected_subdomains = []
    for _, route in selected:
        key = (route["domain_id"], route["subdomain_id"])
        if key not in selected_subdomains:
            selected_subdomains.append(key)
    selected_subdomains = selected_subdomains[: limits["max_subdomains"]]
    selected = [pair for pair in selected if (pair[1]["domain_id"], pair[1]["subdomain_id"]) in selected_subdomains][:max_leaves]

    loaded = []
    for route_score, route in selected:
        leaf = load(route["path"])
        terms = []
        for item in leaf.get("entries", [])[:max_entries]:
            searchable = " ".join([item.get("name", ""), item.get("plain_language", ""), item.get("when_to_use", ""), *item.get("aliases", [])])
            if score(query, [searchable]) or not ranked:
                terms.append(item)
        if not terms:
            terms = leaf.get("entries", [])[:max_entries]
        loaded.append({
            "leaf_id": route["leaf_id"], "score": route_score, "knowledge_type": route["knowledge_type"],
            "scope": route["scope"], "do_not_generalize": route["do_not_generalize"],
            "path": route["path"], "entries": terms,
        })

    output = {
        "query": query,
        "strategy": "progressive",
        "trace": {
            "levels": ["root", "subdomain", "intent", "leaf", "entry"],
            "root_loaded": "index/root.json",
            "runtime_router_loaded": "index/runtime.json",
            "selected_subdomains": [{"domain_id": d, "subdomain_id": s} for d, s in selected_subdomains],
            "loaded_leaf_paths": [item["path"] for item in loaded],
            "loaded_leaf_count": len(loaded),
            "entry_limit": max_entries,
        },
        "matches": loaded,
        "network_search": "not_requested",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
