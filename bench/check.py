#!/usr/bin/env python3
"""semantic PMI 読解の機械採点器。参照解だけを真として採点する。

  Q0 形式（JSONとして読めるか・ファイルが揃っているか）  ※失格判定のみ、配点なし
  Q1 公差の網羅（取りこぼしと捏造の両方を見る）          20点
  Q2 種別                                          15点
  Q3 値と mm 換算                                   20点
  Q4 データムと優先順位                               20点
  Q5 修飾子・公差域の形・突出長さ                       15点
  Q6 複合公差の対                                    10点

Q1 は再現率だけでなく適合率も見る。**取りこぼしと同じ重さで捏造を減点する。**
28件中20件しか読めなかった答案と、8件でっち上げて水増しした答案を
同じ点にしてはいけない。

この採点器を書くまでに実際に踏んだ罠を、そのまま設計に入れてある。

  * ゼロは有効な公差値である。`value or -1` のような falsy 既定値を書くと
    最大実体公差方式のゼロ位置度（⌀0Ⓜ）が不一致に化ける。実際に化けた。
  * 手書きの答案は JSON として壊れることがある（オブジェクト間のカンマ落ち）。
    壊れた提出は失格。中身が正しくても器が壊れていれば受け取れない。
  * 部分提出は実際に出る（6ファイル中5ファイル）。未提出のファイルは
    そのファイル分を0点にするだけで、提出済みの分は正しく採点する。
  * データムは順序が優先順位そのもの。集合ではなく列として比べる。

使い方: check.py <task.json> <reference.json> <submission.json ...>
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REL_TOL = 1e-6  # 値の相対許容。CAD由来の浮動小数ノイズ(1e-13程度)は吸収する
ABS_FLOOR = 1e-9  # ゼロ近傍の絶対許容

POINTS = {"Q1": 20.0, "Q2": 15.0, "Q3": 20.0, "Q4": 20.0, "Q5": 15.0, "Q6": 10.0}
LEVEL_NAME = {
    "Q1": "公差の網羅",
    "Q2": "種別",
    "Q3": "値と mm 換算",
    "Q4": "データムと優先順位",
    "Q5": "修飾子・公差域・突出・単位あたり",
    "Q6": "複合公差の対",
}


def num(v) -> float | None:
    """数値に正規化する。**0.0 を falsy で潰さない。**"""
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def close(got, want) -> bool:
    g, w = num(got), num(want)
    if g is None or w is None:
        return g is None and w is None
    return abs(g - w) <= max(abs(w) * REL_TOL, ABS_FLOOR)


def _norm_list(v) -> list[str]:
    if not isinstance(v, (list, tuple)):
        return []
    return [str(x) for x in v]


def _norm_enum(v) -> list[str]:
    """列挙値の書式差を吸収する。

    STEP では .FREE_STATE. と書かれる。パーサがドットを落とすかどうかは
    実装の都合であって、読み取り能力の差ではない。課題でも指定していないので、
    ここで揃える。
    """
    return sorted(str(x).strip().strip(".").upper() for x in _norm_list(v))


def _files(doc: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in doc.get("results") or []:
        name = Path(str(r.get("file", ""))).name
        if name:
            out[name] = r
    return out


def _tols(rec: dict) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for t in rec.get("tolerances") or []:
        try:
            out[int(t["id"])] = t
        except (KeyError, TypeError, ValueError):
            continue
    return out


def grade(ref_doc: dict, sub_doc: dict, levels: list[str] | None = None) -> dict:
    """levels を渡すとその水準だけで採点する。

    課題が訊いていないものを減点しないため。T001 は複合公差を設問に
    含めていないので Q6 を外す。腕は訊かれたことに答えている。"""
    active = [l for l in POINTS if levels is None or l in levels]
    ref_files = _files(ref_doc)
    sub_files = _files(sub_doc)

    checks: list[dict] = []
    fatal = None
    if not sub_files:
        fatal = "results が無いか、file 名が付いていない"

    missing_files = [f for f in ref_files if f not in sub_files]
    checks.append({
        "level": "Q0", "name": "対象ファイルが揃っている",
        "ok": not missing_files, "points": 0.0, "max": 0.0,
        "detail": "OK" if not missing_files else f"未提出 {len(missing_files)}件: {missing_files}",
    })

    # 集計器。ファイルをまたいで足し合わせる。
    tally = {k: [0.0, 0.0] for k in active}  # level -> [得点分子, 満点分母]
    details: dict[str, list[str]] = {k: [] for k in active}

    for fname, ref_rec in ref_files.items():
        rt = _tols(ref_rec)
        sub_rec = sub_files.get(fname)
        st = _tols(sub_rec) if sub_rec else {}
        n = len(rt)
        if not n:
            continue

        # ---- Q1 網羅。取りこぼしと捏造を対称に見る ----
        if "Q1" not in active:
            pass
        hit = len(set(rt) & set(st))
        extra = len(set(st) - set(rt))
        recall = hit / n
        precision = hit / (hit + extra) if (hit + extra) else 0.0
        f1 = (2 * recall * precision / (recall + precision)) if (recall + precision) else 0.0
        if "Q1" in active:
            tally["Q1"][0] += f1
            tally["Q1"][1] += 1
        if f1 < 1.0:
            details["Q1"].append(
                f"{fname}: 一致{hit}/{n}"
                + (f" 捏造{extra}件" if extra else "")
                + (" 未提出" if sub_rec is None else "")
            )

        # ---- Q2〜Q5 は公差1件ずつ ----
        for level, judge in (
            ("Q2", lambda r, s: str(s.get("kind", "")) == str(r.get("kind", ""))),
            ("Q3", lambda r, s: close(s.get("value"), r.get("value"))
                                and close(s.get("value_mm"), r.get("value_mm"))),
            ("Q4", lambda r, s: _norm_list(s.get("datums")) == _norm_list(r.get("datums"))),
            ("Q5", lambda r, s: _norm_enum(s.get("modifiers")) == _norm_enum(r.get("modifiers"))
                                and str(s.get("zone_form") or "") == str(r.get("zone_form") or "")
                                and close(s.get("projected_length_mm"), r.get("projected_length_mm"))
                                and close(s.get("unit_length_mm"), r.get("unit_length_mm"))
                                and str(s.get("unit_area_shape") or "").strip(".").upper()
                                    == str(r.get("unit_area_shape") or "").strip(".").upper()),
        ):
            if level not in active:
                continue
            good = 0
            bad: list[str] = []
            for i, r in rt.items():
                s = st.get(i)
                if s is not None and judge(r, s):
                    good += 1
                elif s is None:
                    bad.append(f"#{i}(未提出)")
                else:
                    bad.append(f"#{i}")
            tally[level][0] += good
            tally[level][1] += n
            if bad:
                details[level].append(f"{fname}: {good}/{n}  誤り {', '.join(bad[:6])}"
                                      + (" …" if len(bad) > 6 else ""))

        # ---- Q6 複合公差の対 ----
        rc = {tuple(int(x) for x in p) for p in (ref_rec.get("composites") or [])}
        sc_raw = (sub_rec or {}).get("composites") or []
        sc = set()
        for p in sc_raw:
            try:
                sc.add(tuple(int(x) for x in p))
            except (TypeError, ValueError):
                continue
        if (rc or sc) and "Q6" in active:
            hit_c = len(rc & sc)
            extra_c = len(sc - rc)
            rec_c = hit_c / len(rc) if rc else 0.0
            pre_c = hit_c / (hit_c + extra_c) if (hit_c + extra_c) else 0.0
            f1c = (2 * rec_c * pre_c / (rec_c + pre_c)) if (rec_c + pre_c) else 0.0
            tally["Q6"][0] += f1c
            tally["Q6"][1] += 1
            if f1c < 1.0:
                details["Q6"].append(f"{fname}: 一致{hit_c}/{len(rc)}"
                                     + (f" 捏造{extra_c}対" if extra_c else ""))

    for level, (got, mx) in tally.items():
        pts = POINTS[level] * (got / mx) if mx else 0.0
        checks.append({
            "level": level, "name": LEVEL_NAME[level],
            "ok": mx > 0 and abs(got - mx) < 1e-9,
            "points": pts, "max": POINTS[level],
            "detail": " / ".join(details[level]) if details[level] else "OK",
        })

    score = 0.0 if fatal else sum(c["points"] for c in checks)
    total_max = sum(POINTS[l] for l in active)
    if total_max and abs(total_max - 100.0) > 1e-9:
        score = score * 100.0 / total_max  # 満点は常に100に正規化する
    return {
        "file": sub_doc.get("_file", "?"),
        "score": score,
        "max": 100.0,
        "fatal": fatal,
        "checks": checks,
    }


def main() -> int:
    task_path, ref_path, *subs = sys.argv[1:]
    task = json.loads(Path(task_path).read_text(encoding="utf-8"))
    levels = task.get("grade_levels")
    ref = json.loads(Path(ref_path).read_text(encoding="utf-8"))
    out = []
    for s in subs:
        try:
            sub = json.loads(Path(s).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            # 手書きの答案は器が壊れることがある。中身が正しくても受け取らない。
            out.append({"file": s, "score": 0.0, "max": 100.0,
                        "fatal": f"JSONとして読めない: {e}", "checks": []})
            continue
        sub["_file"] = s
        out.append(grade(ref, sub, levels))
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
