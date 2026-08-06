#!/usr/bin/env python3
"""採点器が騙されないかを試す。

参照解から意図的に壊した答案を作り、採点器が落とすことを確認する。
落とせなければ採点器が壊れているので、腕の点数を出してはいけない。

このベンチで実際に踏んだ失敗を、そのまま敵対ケースにしてある。

  evil_zero_to_null   公差値 0.0 を null にする。`value or -1` のような
                      falsy 既定値を書いていると 0.0 が不一致に化けるので、
                      逆に「null を 0.0 と同じ」と誤判定していないかを見る
  evil_malformed      オブジェクト間のカンマ落ち。armB の答案が実際にこれで壊れた
  evil_invent         公差を捏造して水増しする。取りこぼしと同じ重さで減点されるか
  evil_datum_reverse  データムの順序を逆にする。順序は優先順位そのもの

使い方: adversarial.py T001
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(task_id: str) -> dict:
    return json.loads((ROOT / "reference" / f"{task_id}.json").read_text(encoding="utf-8"))


def _sub(ref: dict) -> dict:
    """参照解をそのまま答案の形にする（＝満点になるはずのもの）。"""
    return {"task": ref["task"], "results": copy.deepcopy(ref["results"])}


def _each_tol(sub: dict):
    for r in sub["results"]:
        for t in r.get("tolerances") or []:
            yield r, t


def evil_drop_file(ref):
    """ファイルを1つ落とす（部分提出）。"""
    s = _sub(ref)
    if len(s["results"]) > 1:
        s["results"] = s["results"][:-1]
    else:
        s["results"][0]["tolerances"] = s["results"][0]["tolerances"][: len(s["results"][0]["tolerances"]) // 2]
    return s


def evil_invent(ref):
    """公差を捏造して水増しする。"""
    s = _sub(ref)
    r = s["results"][0]
    base = dict(r["tolerances"][0])
    for k in range(8):
        fake = dict(base)
        fake["id"] = 900000 + k
        fake["name"] = f"Invented.{k}"
        r["tolerances"].append(fake)
    return s


def evil_datum_reverse(ref):
    """データムの順序を逆にする。優先順位が変われば測定の基準面が変わる。"""
    s = _sub(ref)
    for _, t in _each_tol(s):
        d = t.get("datums") or []
        if len(d) > 1:
            t["datums"] = list(reversed(d))
    return s


def evil_datum_set(ref):
    """データムを整列させる（集合として扱った答案）。"""
    s = _sub(ref)
    for _, t in _each_tol(s):
        d = t.get("datums") or []
        if len(d) > 1:
            t["datums"] = sorted(d)
    return s


def evil_zero_to_null(ref):
    """公差値 0.0 を null にする。ゼロと欠測を混同していないか。"""
    s = _sub(ref)
    for _, t in _each_tol(s):
        if t.get("value") == 0.0:
            t["value"] = None
            t["value_mm"] = None
    return s


def evil_unit_confusion(ref):
    """mm 換算を忘れて inch の値をそのまま value_mm に入れる。"""
    s = _sub(ref)
    for _, t in _each_tol(s):
        if t.get("value") is not None:
            t["value_mm"] = t["value"]
    return s


def evil_kind_swap(ref):
    """位置度と面の輪郭度を入れ替える。"""
    s = _sub(ref)
    swap = {"POSITION_TOLERANCE": "SURFACE_PROFILE_TOLERANCE",
            "SURFACE_PROFILE_TOLERANCE": "POSITION_TOLERANCE"}
    for _, t in _each_tol(s):
        t["kind"] = swap.get(t.get("kind"), t.get("kind"))
    return s


def evil_drop_zone_form(ref):
    """公差域の形を落とす。⌀ と S⌀ の区別が消える。"""
    s = _sub(ref)
    for _, t in _each_tol(s):
        t["zone_form"] = ""
    return s


def evil_drop_projected(ref):
    """突出公差域の長さを落とす。"""
    s = _sub(ref)
    for _, t in _each_tol(s):
        t["projected_length"] = None
        t["projected_length_mm"] = None
    return s


def evil_drop_composite(ref):
    """複合公差の対を落とす。"""
    s = _sub(ref)
    for r in s["results"]:
        r["composites"] = []
    return s


def benign_rounded(ref):
    """有効数字8桁に丸めただけ。これは通ってよい（許容の境界確認）。"""
    s = _sub(ref)
    for _, t in _each_tol(s):
        for k in ("value", "value_mm", "projected_length", "projected_length_mm"):
            v = t.get(k)
            if isinstance(v, float):
                t[k] = float(f"{v:.8g}")
    return s


def _has(ref, pred) -> bool:
    return any(pred(t) for r in ref["results"] for t in (r.get("tolerances") or []))


# 変異が効かない課題で走らせると「捕まえられなかった」と誤認する。
# 適用できるかを課題ごとに判定する。
# (名前, 生成関数, 失点が出るべき水準, 適用可否)
EVIL = [
    ("evil_drop_file", evil_drop_file, "Q1", lambda r: True),
    ("evil_invent", evil_invent, "Q1", lambda r: True),
    ("evil_datum_reverse", evil_datum_reverse, "Q4",
     lambda r: _has(r, lambda t: len(t.get("datums") or []) > 1)),
    ("evil_datum_set", evil_datum_set, "Q4",
     lambda r: _has(r, lambda t: (t.get("datums") or []) != sorted(t.get("datums") or []))),
    ("evil_zero_to_null", evil_zero_to_null, "Q3",
     lambda r: _has(r, lambda t: t.get("value") == 0.0)),
    ("evil_unit_confusion", evil_unit_confusion, "Q3",
     lambda r: _has(r, lambda t: t.get("value") != t.get("value_mm"))),
    ("evil_kind_swap", evil_kind_swap, "Q2",
     lambda r: _has(r, lambda t: t.get("kind") in
                    ("POSITION_TOLERANCE", "SURFACE_PROFILE_TOLERANCE"))),
    ("evil_drop_zone_form", evil_drop_zone_form, "Q5",
     lambda r: _has(r, lambda t: t.get("zone_form"))),
    ("evil_drop_projected", evil_drop_projected, "Q5",
     lambda r: _has(r, lambda t: t.get("projected_length_mm") is not None)),
    ("evil_drop_composite", evil_drop_composite, "Q6",
     lambda r: any(rr.get("composites") for rr in r["results"])),
]


def main() -> int:
    task_id = sys.argv[1] if len(sys.argv) > 1 else "T001"
    ref = _load(task_id)
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    task = ROOT / "tasks" / task_id / "task.json"
    ref_path = ROOT / "reference" / f"{task_id}.json"

    def score(name: str, payload) -> dict:
        p = out_dir / f"{name}.json"
        if isinstance(payload, str):
            p.write_text(payload, encoding="utf-8")  # 壊れたJSONをそのまま書く
        else:
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(ROOT / "bench" / "check.py"), str(task), str(ref_path), str(p)],
            capture_output=True, text=True,
        )
        return json.loads(r.stdout)[0]

    failures = 0

    base = score(f"_calib_{task_id.lower()}", _sub(ref))
    full = abs(base["score"] - base["max"]) < 1e-9 and not base["fatal"]
    print(f"[{'OK' if full else 'NG'}] 較正: 参照解 {base['score']:.1f}/{base['max']:.0f}")
    if not full:
        for c in base["checks"]:
            if not c["ok"] and c["max"]:
                print(f"       [{c['level']}] {c['name']}: {c['detail'][:200]}")
        failures += 1

    r = score("benign_rounded", benign_rounded(ref))
    ok = abs(r["score"] - r["max"]) < 1e-9
    print(f"[{'OK' if ok else 'NG'}] benign_rounded: {r['score']:.1f}/{r['max']:.0f}  ← 丸めは通るべき")
    if not ok:
        for c in r["checks"]:
            if not c["ok"] and c["max"]:
                print(f"       [{c['level']}] {c['detail'][:200]}")
        failures += 1

    # 壊れた JSON は失格になること。
    # armB の答案が実際にこれで壊れた（オブジェクト間のカンマ落ち）。
    # 区切りを詰めて出さないと "}, {" になり置換が空振りする。
    broken = json.dumps(_sub(ref), ensure_ascii=False, separators=(",", ":"))
    assert "},{" in broken, "壊す対象が見つからない"
    broken = broken.replace("},{", "}{", 1)
    r = score("evil_malformed", broken)
    ok = bool(r["fatal"]) and r["score"] == 0.0
    print(f"[{'OK' if ok else 'NG'}] evil_malformed: {r['score']:.1f}/{r['max']:.0f}"
          + (f"  失格={r['fatal'][:48]}" if r["fatal"] else "  ← 失格になるべき"))
    if not ok:
        failures += 1

    # 課題が採点しない水準の敵対ケースは走らせても意味がない
    graded = json.loads(task.read_text(encoding="utf-8")).get("grade_levels")

    ran = 0
    for name, fn, expect, applies in EVIL:
        if graded is not None and expect not in graded:
            print(f"[--] {name}: この課題は {expect} を採点しないので飛ばす")
            continue
        if not applies(ref):
            print(f"[--] {name}: この課題には該当する対象が無いので飛ばす")
            continue
        ran += 1
        r = score(name, fn(ref))
        caught = r["score"] < r["max"] - 1e-9 or r["fatal"]
        lost = [c["level"] for c in r["checks"] if not c["ok"] and c["max"]]
        ok = caught and (expect in lost or r["fatal"])
        print(f"[{'OK' if ok else 'NG'}] {name}: {r['score']:.1f}/{r['max']:.0f}"
              f"  失点={sorted(set(lost)) or '無し'}  期待={expect}")
        if not ok:
            failures += 1

    total = ran + 3
    print()
    print(f"敵対テスト: {total - failures}/{total} 通過")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
