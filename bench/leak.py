"""解答様式の記入例を検査する。**記入例はベンチで最も危ない成果物である。**

    python3 -m bench.leak          # 全課題
    python3 -m bench.leak T001

記入例は**見本であると同時に仕様でもある。**この二重性が3通りに壊れる。

  漏れ   記入例の行が、採点対象の行そのもの -> その行は読まずに答えられる
  誤り   記入例の値が、同じ実体の参照解と食い違う -> 従うと減点される
  隠蔽   採点対象のフィールドが記入例に一度も出ない -> 存在を知りようがない

**T001 の記入例は3つとも起こしている。**

    {"file": "nist_ftc_06_asme1_ap242-e2.stp",
     "tolerances": [{"id": 146, "kind": "FLATNESS_TOLERANCE", "name": "Flatness.1",
                     "value": 0.01, "unit": "inch", "value_mm": 0.254,
                     "datums": [], "modifiers": []}],
     "datums": ["A", "B", "C"]}

  漏れ   公差 #146 の8フィールドが**参照解と完全一致**する。28件中1件を配っている
  誤り   ファイルの datums は実際には10個（A-H, J, K）。記入例は3個しか書いていない
  隠蔽   平面度には公差域の形が無いので `zone_form` が例に出ない。
         **6本の独立した解答者が、1件のずれもなく同じ9箇所を null で出した。**
         読解の失敗ではなく、聞かれていないことに答えなかっただけである
         （docs/T001n3.md に記録）

**この3つは同じ1つの記入例から出ている。**しかも互いに逆を向いている。
漏れを避けようとして作り物の例を書けば「実在しない行」になり、
実在の行を選べば漏れになる。**正しい形は「実在するが採点対象ではない行」である。**

シリーズの別のベンチ（bim-bench）は逆側の検査を持っている——
記入例の行が参照解に**実在するか**を確かめる（作り話を防ぐため）。
両方が要る。片方だけだともう片方に倒れる。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 既知の欠陥。数が変わったら検査か素材が変わっている。
#
# 「誤り」は記入例が実物より短い一覧を書いていることによる。**省略である旨は
# 課題文のどこにも書いていない**ので、記入例は実在しない値を形として示している。
# 見本の省略なら本来は「省略」と書くべきで、書いていない以上これは欠陥である。
KNOWN = {"T001": {"leak": 1, "wrong": 1, "note": 0},
         # T002 の note 2件は**誤検出**。件数 3 と 2 が本文の「3」「2」に当たっただけで、
         # 該当する文は採点対象の件数を述べていない。人が読んで判定した。
         "T002": {"leak": 0, "wrong": 2, "note": 0},
         # T003 の note は、欠陥を説明するつもりで採点対象の件数を2つ開示している。
         # **記入例を直した版が、直す理由を書いた文で別の漏れを作った。**
         # T006（bim-bench）と同じ形で、これで3回連続である。走行後なので直さない。
         # T003 の note 2件は**本物**。28 は公差の総数、9 は zone_form が非空の件数で、
         # どちらも欠陥を説明する文の中でこちらが書いた。腕が指摘して分かった。
         # T003 の note の「28」は本物（公差の総数）。「9」は10未満なので助言に落ちる。
         "T003": {"leak": 0, "wrong": 0, "note": 1}}


def approx(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-6
    return a == b


def note_leak(task: dict, ref: dict) -> list[str]:
    """課題文の散文が、採点対象の**件数**を漏らしていないか。

    記入例が実在の行かどうかとは別の経路である。T003 の note は
    「28件中1件を配っていた」「同じ9箇所を null で出した」と書いており、
    28 は公差の総数、9 は zone_form が非空の件数そのものだった。
    **欠陥を説明するために書いた文が、次の漏れになる。**
    """
    tols = [t for r in ref.get("results", []) for t in r.get("tolerances", [])]
    counts = {"公差の総数": len(tols)}
    for f in ("zone_form", "modifiers", "projected_length_mm",
              "unit_length_mm", "unit_area_shape", "composite_role"):
        n = sum(1 for t in tols if t.get(f) not in (None, "", [], {}))
        if n:
            counts[f"{f} が非空の件数"] = n
    text = " ".join(str(task.get(k, "")) for k in ("note", "title", "asked",
                                                   "grade_levels_note",
                                                   "answer_format_note"))
    nums = set(re.findall(r"\d+", text))
    # **小さい件数は判定力が無い。**設問番号の (4) が「修飾子4件」に当たる、という類の
    # 一致が必ず出る。**判定力の無い一致で関門を止めてはいけない**ので、
    # 10未満は助言として出すだけにして、落とすのは10以上に限る
    # （shortcut.py を助言に格下げしたのと同じ理由）。
    strong = [f"{label}={n}" for label, n in counts.items() if str(n) in nums and n >= 10]
    weak = [f"{label}={n}" for label, n in counts.items() if str(n) in nums and n < 10]
    return strong, weak


def check(task_id: str) -> int:
    tp = ROOT / "tasks" / task_id / "task.json"
    rp = ROOT / "reference" / f"{task_id}.json"
    if not tp.exists() or not rp.exists():
        return 0
    task = json.loads(tp.read_text(encoding="utf-8"))
    ref = json.loads(rp.read_text(encoding="utf-8"))
    ex_results = (task.get("answer_format") or {}).get("results") or []
    by_file = {r["file"]: r for r in ref.get("results", [])}

    leaks, wrongs = [], []
    seen_fields: set[str] = set()
    graded_fields: set[str] = set()

    # **「採点対象」は採点器が実際に見るフィールドに限る。**
    # 参照解の非空フィールドを全部要求すると、採点していない複合公差まで
    # 記入例に出せと言うことになる（T003 でその矛盾が出た）。
    # grade_levels に載っている段のフィールドだけを見る。
    GRADED_BY_LEVEL = {
        "Q1": {"id"},
        "Q2": {"kind"},
        "Q3": {"value", "value_mm", "unit"},
        "Q4": {"datums"},
        "Q5": {"modifiers", "zone_form", "projected_length_mm",
               "unit_length_mm", "unit_area_shape"},
        "Q6": {"composite_role", "composite_partner"},
    }
    active = set(task.get("grade_levels") or GRADED_BY_LEVEL)
    want = set().union(*(GRADED_BY_LEVEL[l] for l in active if l in GRADED_BY_LEVEL))
    for rec in ref.get("results", []):
        for tol in rec.get("tolerances", []):
            graded_fields |= {k for k, v in tol.items()
                              if k in want and v not in (None, "", [], {})}

    for exr in ex_results:
        # 例に出たフィールドは、例がどのファイルのものでも数える。
        for extol in exr.get("tolerances", []):
            seen_fields |= {k for k, v in extol.items()
                            if v not in (None, "", [], {})}
        # 漏れ・誤りの照合は、例が**採点対象のファイル**のときだけ意味を持つ。
        # 課題に出てこないファイルから採った例は、定義上どちらにも当たらない
        # （それが「実在するが採点対象ではない行」という正しい形である）。
        rec = by_file.get(exr.get("file"))
        if rec is None:
            continue
        for extol in exr.get("tolerances", []):
            real = next((t for t in rec.get("tolerances", [])
                         if t.get("id") == extol.get("id")), None)
            if real is None:
                continue
            same = [k for k in extol if k in real and approx(extol[k], real[k])]
            diff = [k for k in extol if k in real and not approx(extol[k], real[k])]
            if not diff:
                leaks.append((exr["file"], extol.get("id"), len(same)))
            elif diff:
                wrongs.append((exr["file"], extol.get("id"), diff))
        # ファイル単位のフィールド
        for k, v in exr.items():
            if k in ("file", "tolerances", "schema"):
                continue
            if k in rec and not approx(v, rec[k]):
                wrongs.append((exr["file"], f"（ファイル）{k}", [f"{v} ≠ {rec[k]}"]))

    hidden = sorted(graded_fields - seen_fields)
    notes, notes_weak = note_leak(task, ref)

    print(f"=== {task_id} 解答様式の記入例 ===")
    for f, tid, n in leaks:
        print(f"  [漏れ] {f} の #{tid} が参照解と{n}フィールド完全一致。"
              f"**この行は読まずに答えられる**")
    for f, tid, d in wrongs:
        print(f"  [誤り] {f} の {tid}: {d}")
    if hidden:
        print(f"  [隠蔽] 採点対象なのに記入例に一度も出ないフィールド {len(hidden)}件:")
        print(f"         {', '.join(hidden)}")
    for x in notes:
        print(f"  [課題文] 散文が採点対象の件数を漏らしている: {x}")
    for x in notes_weak:
        print(f"  [参考] 件数が一致するが判定力が無い（10未満）: {x}")
    if not leaks and not wrongs and not hidden and not notes:
        print("  漏れ・誤り・隠蔽なし")

    want = KNOWN.get(task_id)
    print()
    if want:
        got = {"leak": len(leaks), "wrong": len(wrongs), "note": len(notes)}
        if got == want:
            print(f"既知の欠陥を検出（この検査自身の較正）: "
                  f"漏れ{want['leak']} / 誤り{want['wrong']} / 課題文{want['note']}")
            print("  **記入例は直していない。**走行後に直すと、答案を見てから課題文を"
                  "書き換えたことになる。次版で作り直す。")
            return 0
        print(f"**較正に失敗。** 期待 {want} / 実際 {got}")
        return 1
    if leaks or wrongs or notes:
        print(f"**欠陥 {len(leaks)+len(wrongs)+len(notes)}件。**")
        return 1
    return 0


def main() -> int:
    tasks = sys.argv[1:] or [d.name for d in sorted((ROOT / "tasks").iterdir()) if d.is_dir()]
    bad = 0
    for i, t in enumerate(tasks):
        if i:
            print()
        bad += check(t)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
