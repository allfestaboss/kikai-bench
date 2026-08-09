#!/usr/bin/env python3
"""採点結果を点数とコストの両方で出す。

    python -m bench.summary T002

点数だけの表は、腕が揃って満点になった時点で軸を映さなくなる。
kikai-bench の T001 では B も C も 28/28 で並び、差はトークン2.3倍にしか
出なかった。T002 でファイルを6倍にすると、同じ2.3倍が
「完遂できるかどうか」に変わった。だから常に両方出す。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import cost as costmod

ROOT = Path(__file__).resolve().parent.parent
LEVELS = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
LABEL = {"Q1": "網羅", "Q2": "種別", "Q3": "値/mm", "Q4": "データム",
         "Q5": "修飾子等", "Q6": "複合"}


def _name(path: str, task_id: str) -> str:
    stem = Path(path).stem
    return "参照解" if stem == f"_calib_{task_id.lower()}" else stem


def render(task_id: str) -> int:
    rows = json.loads((ROOT / "out" / f"{task_id}.json").read_text(encoding="utf-8"))
    costs = costmod.load(task_id)
    # 何で測ったか分からないコストは表に出さない。
    # 欠測と未記録は別物で、'-' で流すと区別がつかなくなる。
    if costs:
        costmod.require_env(task_id)
    meta = costmod.meta(task_id)
    work = costmod.workload(task_id)
    units = work["tolerances"]

    head = f"== {task_id} ==  {work['files']}ファイル / 幾何公差 {units}件"
    if meta.get("round"):
        head += f"  （第{meta['round']}回）"
    print()
    print(head)
    if meta.get("note"):
        print(f"   {meta['note']}")

    valid = [c.tokens for c in costs.values() if c and c.tokens]
    base = min(valid) if valid else None

    W, L, R = 12, costmod.ljust, costmod.rjust
    print()
    print(L("提出", W) + "".join(R(LABEL[l], 9) for l in LEVELS)
          + R("合計", 10) + R("%", 7) + R("tok", 9) + R("時間", 10)
          + R("tok/件", 9) + R("倍率", 7))
    print("-" * 118)

    for r in rows:
        name = _name(r["file"], task_id)
        got = {l: 0.0 for l in LEVELS}
        mx = {l: 0.0 for l in LEVELS}
        for c in r["checks"]:
            if c["level"] in got:
                got[c["level"]] += c["points"]
                mx[c["level"]] += c["max"]
        cells = "".join(R(f"{got[l]:.0f}/{mx[l]:.0f}" if mx[l] else "-", 9) for l in LEVELS)
        pct = 100 * r["score"] / r["max"] if r["max"] else 0
        c = costs.get(name)
        print(L(name, W) + cells + f"{r['score']:>7.1f}/{r['max']:<3.0f}{pct:>6.1f}%"
              + R(costmod.fmt_tokens(c.tokens) if c else "-", 9)
              + R(costmod.fmt_seconds(c.seconds) if c else "-", 10)
              + R(f"{c.per_unit(units):.0f}" if c and c.per_unit(units) else "-", 9)
              + R(f"{c.tokens / base:.1f}×" if c and c.tokens and base else "-", 7)
              + ("  ★失格" if r.get("fatal") else ""))

    print()
    for r in rows:
        fails = [c for c in r["checks"] if not c["ok"] and (c["max"] or c["level"] == "Q0")]
        if not fails and not r.get("fatal"):
            continue
        print(f"■ {_name(r['file'], task_id)} の失点:")
        if r.get("fatal"):
            print(f"   ★失格: {r['fatal']}")
        for c in fails:
            lost = c["max"] - c["points"]
            head = f"   [{c['level']}] {c['name']}"
            if c["max"]:
                head += f"  -{lost:.1f}点"
            print(head)
            print(f"        {c['detail'][:300]}")
    return 0


def main() -> int:
    return render(sys.argv[1] if len(sys.argv) > 1 else "T001")


if __name__ == "__main__":
    sys.exit(main())
