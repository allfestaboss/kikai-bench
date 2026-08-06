"""参照解の較正。

PMI 抽出器を、生の STEP テキストを手で追った結果と突き合わせる。
手側は step.py も pmi.py も呼ばない。同じコードを呼んで比べても検査にならない。

    python -m bench.selfcheck
"""

from __future__ import annotations

import sys
from pathlib import Path

from .pmi import extract
from .step import load

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "corpus" / "nist" / "nist_ftc_06_asme1_ap242-e2.stp"


def hand_flatness() -> dict:
    """FTC-06 の Flatness.1 を手で追う。

    ファイルから直接読んだ行（2026-08-06 時点）:

        #146=FLATNESS_TOLERANCE('Flatness.1','',#9981,#2605);
        #9981=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.01000000000004),#10033);
        #10033=(CONVERSION_BASED_UNIT('inch',#9962,...)LENGTH_UNIT()NAMED_UNIT(#10031));
        #9962=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960);
        #9960=(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.));

    よって 0.01000000000004 inch。1 inch = 25.4 mm なので mm 換算は掛け算1つ。
    データム参照は無い（FLATNESS は単独形で第5引数を持たない）。
    """
    value_inch = 0.01000000000004
    mm_per_inch = 25.4
    return {
        "id": 146,
        "kind": "FLATNESS_TOLERANCE",
        "name": "Flatness.1",
        "value": value_inch,
        "unit": "inch",
        "value_mm": value_inch * mm_per_inch,
        "datums": (),
    }


def hand_position() -> dict:
    """FTC-06 の Position.21 を手で追う。データム参照を含む。

        #111=(GEOMETRIC_TOLERANCE('Position.21','',#9987,#977)
              GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE((#329))
              GEOMETRIC_TOLERANCE_WITH_MODIFIERS((.MAXIMUM_MATERIAL_REQUIREMENT.))
              POSITION_TOLERANCE());
        #9987=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.0250000000001),#10033);
        #329=DATUM_SYSTEM('Datum System .5',$,#9395,.F.,(#308,#309,#310));
        #308=DATUM_REFERENCE_COMPARTMENT('',$,#9395,.F.,#290,$);  #290=DATUM('',$,#9395,.F.,'C');
        #309=...#291=DATUM('',$,#9395,.F.,'A');
        #310=...#289=DATUM('',$,#9395,.F.,'B');

    区画の並び順がそのままデータムの優先順位なので C, A, B。
    """
    value_inch = 0.0250000000001
    return {
        "id": 111,
        "kind": "POSITION_TOLERANCE",
        "name": "Position.21",
        "value": value_inch,
        "unit": "inch",
        "value_mm": value_inch * 25.4,
        "datums": ("C", "A", "B"),
        "modifiers": ("MAXIMUM_MATERIAL_REQUIREMENT",),
    }


def hand_spherical() -> dict:
    """FTC-06 の Position.15 を手で追う。公差域が球形の唯一の例。

        #135=(GEOMETRIC_TOLERANCE('Position.15','',#10001,#991)
              GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE((#325))POSITION_TOLERANCE());
        #126=TOLERANCE_ZONE('',$,#9395,.F.,(#135),#117);
        #117=TOLERANCE_ZONE_FORM('spherical');

    NIST の定義 xlsx が FTC-06 について挙げている
    ATC72 "Symbol: Spherical Diameter Symbol"  ⌖ | S⌀ .025 | D | B | C
    がこれにあたる。値・データム・公差域の形の3つが揃って初めて仕様と一致する。
    """
    value_inch = 0.0250000000001
    return {
        "id": 135,
        "kind": "POSITION_TOLERANCE",
        "name": "Position.15",
        "value": value_inch,
        "unit": "inch",
        "value_mm": value_inch * 25.4,
        "datums": ("D", "B", "C"),
        "zone_form": "spherical",
    }


HANDS = [hand_flatness(), hand_position(), hand_spherical()]
TOL = 1e-9


def main() -> int:
    x = extract(load(TARGET))
    by_id = {t.id: t for t in x.tolerances}

    print(f"=== 較正 / {TARGET.name} ===")
    print(f"スキーマ: {x.schema}")
    print(f"抽出: 幾何公差 {len(x.tolerances)}件 / データム {len(x.datums)}件")
    print()

    ok = True
    for hand in HANDS:
        got = by_id.get(hand["id"])
        print(f"--- #{hand['id']} {hand['name']} ---")
        if got is None:
            print("  NG: 抽出側に存在しない")
            ok = False
            continue
        for key in ("kind", "name", "unit", "datums", "zone_form"):
            want = hand.get(key)
            if key not in hand:
                continue
            have = getattr(got, key)
            match = want == have
            ok = ok and match
            print(f"  {key:<10} 手={want!s:<34} 抽出={have!s:<34} {'' if match else '<-- NG'}")
        for key in ("value", "value_mm"):
            want, have = hand[key], getattr(got, key)
            diff = abs(want - have)
            ok = ok and diff <= TOL
            print(f"  {key:<10} 手={want:<34.12f} 抽出={have:<34.12f} 差={diff:.2e}"
                  + ("" if diff <= TOL else "  <-- NG"))
        if "modifiers" in hand:
            match = tuple(hand["modifiers"]) == tuple(got.modifiers)
            ok = ok and match
            print(f"  {'modifiers':<10} 手={hand['modifiers']!s:<34} 抽出={got.modifiers!s:<34}"
                  + ("" if match else "  <-- NG"))
        print()

    print("較正:", "OK（手読みと一致）" if ok else "NG（不一致あり）")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
