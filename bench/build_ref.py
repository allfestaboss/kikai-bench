"""タスクから参照解を生成する。

    python -m bench.build_ref T001

参照解は「STEP ファイルに実際に入っている semantic PMI」であって、
NIST のテストケース定義（xlsx）ではない。NIST 自身が
「CAD がどうモデル化したか／どう STEP に書き出したかで差が出うる」と
断っているので、定義と中身は必ずしも一致しない。定義のほうは
抽出器を外から検算するのに使う（bench/spec.py）。
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

from .pmi import extract
from .step import load

ROOT = Path(__file__).resolve().parent.parent


def build(task_id: str) -> dict:
    task = json.loads((ROOT / "tasks" / task_id / "task.json").read_text(encoding="utf-8"))
    results = []
    for f in task["files"]:
        x = extract(load(ROOT / f["path"]))
        results.append(
            {
                "file": Path(f["path"]).name,
                "schema": x.schema,
                "tolerances": [dataclasses.asdict(t) | {"datums": list(t.datums),
                                                        "modifiers": list(t.modifiers)}
                               for t in x.tolerances],
                "datums": [d.label for d in x.datums],
                "composites": [list(c) for c in x.composites],
                "counts": x.counts(),
            }
        )
    return {
        "task": task_id,
        "standard": "ISO 10303-242 (STEP AP242) / ASME Y14.5",
        "results": results,
        "summary": {
            "n_file": len(results),
            "n_tolerance": sum(len(r["tolerances"]) for r in results),
            "n_datum": sum(len(r["datums"]) for r in results),
            "n_composite": sum(len(r["composites"]) for r in results),
        },
    }


def main() -> int:
    task_id = sys.argv[1] if len(sys.argv) > 1 else "T001"
    ref = build(task_id)
    out = ROOT / "reference" / f"{task_id}.json"
    out.write_text(json.dumps(ref, ensure_ascii=False, indent=1), encoding="utf-8")
    s = ref["summary"]
    print(f"{out.relative_to(ROOT)}: {s['n_file']}ファイル / 幾何公差 {s['n_tolerance']}件 / データム {s['n_datum']}件")
    for r in ref["results"]:
        brief = " ".join(f"{k.replace('_TOLERANCE','')}={v}" for k, v in r["counts"].items())
        print(f"    {r['file']}: {brief}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
