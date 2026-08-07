"""抽出器を NIST のテストケース定義で外から検算する。

    python -m bench.crosscheck

較正（bench/selfcheck.py）は自分の手読みとの突き合わせなので、
こちらが同じ思い込みをしていれば一緒に間違える。
この検算は照合先が外部にあるので、その思い込みごと検査できる。

定義に挙がっている項目が STEP ファイルの中に見つからなければ、
(a) 抽出器の抜け か (b) モデルが定義と違う のどちらかである。
NIST 自身が (b) はありうると断っているので、出た差は両方の可能性で読む。
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import spec
from .pmi import extract
from .step import load as load_step

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "nist"
VALUE_TOL = 1e-6


def _files_for(ftc: str) -> list[Path]:
    """FTC 番号に対応する AP242 ファイル。e2 を優先し、無ければ e1。"""
    cands = sorted(CORPUS.glob(f"nist_ftc_{int(ftc):02d}_*ap242*.stp"))
    cands = [c for c in cands if "-tg" not in c.name]  # テセレーション版は semantic PMI 無し
    return cands


def _matches(claim: spec.Claim, t) -> tuple[bool, list[str]]:
    """定義1件が公差1件と一致するか。合わない項目名を返す。"""
    bad: list[str] = []
    if claim.kind != t.kind:
        bad.append("kind")
    if claim.value is not None:
        if t.value is None or abs(claim.value - t.value) > VALUE_TOL:
            bad.append("value")
    if claim.datums and tuple(claim.datums) != tuple(t.datums):
        bad.append("datums")
    if claim.zone_form and claim.zone_form != t.zone_form:
        bad.append("zone_form")
    for m in claim.modifiers:
        # Ⓟ は記入枠上の記号で、ファイルでは突出公差域の実体として表れる。
        # 修飾子の列挙値としては入っていないので、そちらで見る。
        if m == "PROJECTED_TOLERANCE_ZONE":
            if t.projected_length_mm is None:
                bad.append("projected")
                break
            continue
        if m not in t.modifiers:
            bad.append("modifiers")
            break
    return (not bad), bad


def main() -> int:
    table = spec.load()
    print(f"=== NIST テストケース定義との突き合わせ ===")
    print(f"定義: {table.rows}行 / うち幾何公差として読めた {len(table.claims)}件"
          f" / 記号はあるが読めなかった {len(table.unparsed)}件")
    print()

    hit = miss = 0
    by_ftc: dict[str, list[spec.Claim]] = {}
    for c in table.claims:
        by_ftc.setdefault(c.ftc, []).append(c)

    for ftc in sorted(by_ftc, key=int):
        files = _files_for(ftc)
        if not files:
            print(f"FTC-{ftc}: 対応する AP242 ファイルが corpus に無い")
            continue
        f = files[-1]
        tols = extract(load_step(f)).tolerances
        print(f"--- FTC-{ftc}  ({f.name}, 公差{len(tols)}件) ---")
        best_score = 999
        for c in by_ftc[ftc]:
            best_score = 999
            best_bad: list[str] | None = None
            best_t = None
            ok = False
            for t in tols:
                good, bad = _matches(c, t)
                if good:
                    ok = True
                    break
                # 同種の公差の中で最も近いものを候補に選ぶ（種別違いは論外なので後回し）
                score = (0 if t.kind == c.kind else 10) + len(bad)
                if best_bad is None or score < best_score:
                    best_bad, best_t, best_score = bad, t, score
            if ok:
                hit += 1
                print(f"  OK   ATC{c.atc:<4} {c.raw[:52]}")
            else:
                miss += 1
                print(f"  MISS ATC{c.atc:<4} {c.raw[:52]}")
                print(f"       求めた: kind={c.kind} value={c.value} "
                      f"datums={'|'.join(c.datums) or '－'} zone={c.zone_form or '－'} "
                      f"mods={','.join(c.modifiers) or '－'}")
                if best_t is not None:
                    print(f"       近い候補: {best_t.kind} value={best_t.value} "
                          f"datums={'|'.join(best_t.datums) or '－'} "
                          f"zone={best_t.zone_form or '－'} "
                          f"mods={','.join(best_t.modifiers) or '－'}  不一致={best_bad}")
        print()

    if table.unparsed:
        print("=== 記号はあるが読めなかった定義（要確認） ===")
        for ftc, atc, raw in table.unparsed:
            print(f"  FTC-{ftc} ATC{atc}: {raw[:80]!r}")
        print()

    total = hit + miss
    print(f"定義との突き合わせ: {hit}/{total} 一致"
          + (f" / 未解釈 {len(table.unparsed)}件" if table.unparsed else ""))
    print()
    ng = check_declared()
    return 0 if miss == 0 and not table.unparsed and ng == 0 else 1




# ---------------------------------------------------------------------------
# ファイル自身が持つ検証プロパティとの突き合わせ
#
# STEP AP242 のファイルには、書き出した側が数え上げた検証用の値が入っている。
#   #9948=INTEGER_REPRESENTATION_ITEM('number of geometric tolerances',28.);
#   #689=DESCRIPTIVE_REPRESENTATION_ITEM('datum references','D,B,C');
# xlsx の定義（45件）より照合先として強く、corpus のほぼ全ファイルを覆う。
#
# この存在は腕(armB)が見つけた。こちらは10,970行を読み通しておらず、
# 気づいていなかった。
# ---------------------------------------------------------------------------

import re as _re

_DECL = _re.compile(r"INTEGER_REPRESENTATION_ITEM\('([^']*)',(\d+)\.?\)")
_DATUM_STR = _re.compile(r"DESCRIPTIVE_REPRESENTATION_ITEM\('datum references','([^']*)'\)")


def declared(path: Path) -> dict[str, int]:
    """ファイルが自分で宣言している検証値。"""
    s = path.read_text(errors="replace")
    return {m.group(1): int(m.group(2)) for m in _DECL.finditer(s)}


def check_declared() -> int:
    """全ファイルについて、抽出件数が宣言と合うか見る。"""
    print("=== ファイル自身の検証プロパティとの突き合わせ ===")
    print(f"{'ファイル':<36}{'宣言':>6}{'抽出':>6}  判定")
    print("-" * 62)
    ok = ng = skip = 0
    for f in sorted(CORPUS.glob("*ap242*.stp")):
        d = declared(f)
        want = d.get("number of geometric tolerances")
        if want is None:
            skip += 1
            continue
        x = extract(load_step(f))
        got = len(x.tolerances)
        # 数え方の規約が2通りある。複合公差の上下2段を2件と数えるファイルと、
        # 1件と数えるファイルがある。後者は 'number of composite tolerances' を
        # そもそも宣言しない（宣言の組自体が違う生成器の出力）。
        folded = got - len(x.composites)
        has_comp_decl = "number of composite tolerances" in d
        if want == got:
            ok += 1
            mark = "OK"
        elif not has_comp_decl and want == folded:
            ok += 1
            mark = f"OK（複合を1件と数える規約。{got}件 - 複合{len(x.composites)}対）"
        else:
            ng += 1
            mark = f"不一致（差 {got - want:+d}）"
        print(f"{f.name:<36}{want:>6}{got:>6}  {mark}")
    print(f"\n  一致 {ok} / 不一致 {ng} / 宣言なし {skip}")

    # 参照切れの検出。宣言と中身が食い違う原因がこれのことがある。
    dangling = []
    for f in sorted(CORPUS.glob("*ap242*.stp")):
        model = load_step(f)
        for r in model.of("GEOMETRIC_TOLERANCE_RELATIONSHIP"):
            if len(r.args) < 4:
                continue
            for side, ref in (("上段", r.args[2]), ("下段", r.args[3])):
                if model.get(ref) is None:
                    dangling.append((f.name, r.id, side, int(ref)))
    if dangling:
        print("\n  参照切れ（存在しない実体を指している）:")
        for name, rid, side, ref in dangling:
            print(f"    {name} の #{rid} が {side} #{ref} を指しているが実体が無い")
    if ng:
        print("  ※ 不一致は必ずしもこちらの誤りではない。実体を数え直して")
        print("     宣言側が中身と合っていないことを確かめること。")
    return ng


if __name__ == "__main__":
    sys.exit(main())
