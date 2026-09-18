#!/usr/bin/env python3
"""End-to-end checks for progressive routing scenarios."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "scripts/query-index.py"
CASES = [
    ("删除列表项，5 秒内撤销并支持键盘", {"undo-window", "motion-accessibility"}, 4),
    ("设计一个不模板化的 AI 数据后台", {"minimal-data", "layout-patterns"}, 8),
    ("把这个角色做成毛绒玩偶和周边", {"character-ip"}, 2),
    ("GPUIX 能不能跑移动端？", {"gpui-mobile"}, 3),
    ("后端需要高可用、高并发、高扩展", {"availability-patterns", "capacity-model", "scaling-strategies"}, 3),
]
NEGATIVE_CASES = [
    ("hello world", {"morph-icon", "ripple-button", "liquid-slider"}),
    ("GPUIX mobile", {"morph-icon", "ripple-button", "liquid-slider"}),
]

for query, expected, max_leaves in CASES:
    raw = subprocess.check_output(["python3", str(QUERY), query], text=True)
    result = json.loads(raw)
    loaded = {item["leaf_id"] for item in result["matches"]}
    assert expected.issubset(loaded), f"{query}: missing {expected - loaded}"
    assert result["trace"]["loaded_leaf_count"] <= max_leaves, f"{query}: loaded too much"
    assert result["trace"]["loaded_leaf_count"] <= 8, f"{query}: exceeds global cap"
    assert len(result["trace"]["selected_subdomains"]) <= 3, f"{query}: exceeds subdomain cap"
    assert result["trace"]["domain_index_paths"], f"{query}: domain index was not loaded"
    assert result["trace"]["intent_index_paths"], f"{query}: intent index was not loaded"
    subdomains = len(result["trace"]["selected_subdomains"])
    assert len(result["trace"]["selected_intents"]) <= 3 * subdomains, f"{query}: exceeds per-subdomain intent cap"
for query, forbidden in NEGATIVE_CASES:
    raw = subprocess.check_output(["python3", str(QUERY), query], text=True)
    result = json.loads(raw)
    loaded = {item["leaf_id"] for item in result["matches"]}
    assert loaded.isdisjoint(forbidden), f"{query}: false positive {loaded & forbidden}"
raw = subprocess.check_output(["python3", str(QUERY), "GPUIX 能不能跑移动端？"], text=True)
gpui_result = json.loads(raw)
gpui_mobile = next(item for item in gpui_result["matches"] if item["leaf_id"] == "gpui-mobile")
assert gpui_mobile["scope"] == "provider-specific", "provider scope was lost"
assert gpui_mobile["do_not_generalize"] is True, "provider boundary was lost"
for option in ("--max-leaves", "--max-entries"):
    completed = subprocess.run(
        ["python3", str(QUERY), "撤销", option, "0"],
        text=True,
        capture_output=True,
    )
    assert completed.returncode != 0, f"{option}: zero must be rejected"
print(f"progressive query ok: {len(CASES)} scenarios")
