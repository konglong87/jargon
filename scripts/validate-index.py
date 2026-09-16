#!/usr/bin/env python3
"""Validate Jargon root/package/term index consistency."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)

root = load(ROOT / "index/root.json")["domains"]
packages = load(ROOT / "index/packages.json")["packages"]
root_ids = [item["domain_id"] for item in root]
package_ids = [item["domain_id"] for item in packages]
assert len(root_ids) == len(set(root_ids)), "duplicate root domain_id"
assert len([item["package_id"] for item in packages]) == len(set(item["package_id"] for item in packages)), "duplicate package_id"
assert set(root_ids) == set(package_ids), f"domain mismatch: roots={set(root_ids)-set(package_ids)}, packages={set(package_ids)-set(root_ids)}"
for item in packages:
    term_path = ROOT / item["term_path"]
    assert term_path.is_file(), f"missing term package: {item['term_path']}"
    term = load(term_path)
    assert term["package_id"] == item["package_id"], f"package id mismatch: {item['package_id']}"
    assert term["domain_id"] == item["domain_id"], f"domain id mismatch: {item['package_id']}"
    assert term["status"] == item["status"], f"status mismatch: {item['package_id']}"
    intent_ids = {intent["id"] for intent in term.get("intents", [])}
    assert set(item["intents"]) == intent_ids, f"intent mismatch: {item['package_id']}"
print(f"index ok: {len(root)} domains, {len(packages)} packages")
