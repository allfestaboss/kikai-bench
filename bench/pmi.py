"""AP242 の semantic PMI を取り出して正規化する。

実物（NIST の AP242 ファイル）で確認した経路だけを実装している。

  公差値   GEOMETRIC_TOLERANCE(.., #magnitude, ..)
           -> LENGTH_MEASURE_WITH_UNIT('LENGTH_MEASURE(v)', #unit)
           -> CONVERSION_BASED_UNIT('inch', #factor, ..) -> SI_UNIT(*, MILLI, METRE)

  データム GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE((#datum_system))
           -> DATUM_SYSTEM(.., (#compartment, ..))
           -> DATUM_REFERENCE_COMPARTMENT(.., #datum, ..) -> DATUM(.., 'A')

複合実体では公差の種別が「葉」の型として入る。
  (GEOMETRIC_TOLERANCE(..) GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE(..) POSITION_TOLERANCE())
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .step import Entity, Model, Ref

# 幾何公差の種別。ASME Y14.5 の記号との対応も持たせる。
TOLERANCE_KINDS = {
    "ANGULARITY_TOLERANCE": "角度",
    "CIRCULAR_RUNOUT_TOLERANCE": "円周振れ",
    "COAXIALITY_TOLERANCE": "同軸度",
    "CONCENTRICITY_TOLERANCE": "同心度",
    "CYLINDRICITY_TOLERANCE": "円筒度",
    "FLATNESS_TOLERANCE": "平面度",
    "LINE_PROFILE_TOLERANCE": "線の輪郭度",
    "PARALLELISM_TOLERANCE": "平行度",
    "PERPENDICULARITY_TOLERANCE": "直角度",
    "POSITION_TOLERANCE": "位置度",
    "ROUNDNESS_TOLERANCE": "真円度",
    "STRAIGHTNESS_TOLERANCE": "真直度",
    "SURFACE_PROFILE_TOLERANCE": "面の輪郭度",
    "SYMMETRY_TOLERANCE": "対称度",
    "TOTAL_RUNOUT_TOLERANCE": "全振れ",
}

_MEASURE = re.compile(r"[A-Z_]+\(([-+0-9.eE]+)\)")
# COMMON_DATUM_LIST((#76,#77)) のような型付き値から参照を拾う
_TYPED_REFS = re.compile(r"#(\d+)")


def _measure_value(v) -> float | None:
    """'LENGTH_MEASURE(0.01)' や素の数値から値を取る。"""
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        m = _MEASURE.search(v)
        if m:
            return float(m.group(1))
    return None


@dataclass
class Unit:
    name: str  # 'inch' / 'millimetre'
    mm_per: float  # mm への換算係数


def _unit(model: Model, ref) -> Unit | None:
    e = model.get(ref)
    if e is None:
        return None
    if "CONVERSION_BASED_UNIT" in e.types:
        args = e.parts.get("CONVERSION_BASED_UNIT") or e.args
        name = args[0] if args else ""
        factor = model.get(args[1]) if len(args) > 1 else None
        mm = 1.0
        if factor is not None:
            mm = _measure_value(factor.args[0]) or 1.0
        return Unit(name=str(name), mm_per=mm)
    if "SI_UNIT" in e.types:
        args = e.parts.get("SI_UNIT") or e.args
        prefix = args[1] if len(args) > 1 else None
        mm = 1.0 if prefix == "MILLI" else 1000.0  # METRE のとき
        return Unit(name=f"{prefix or ''}{args[2] if len(args) > 2 else 'METRE'}".lower(), mm_per=mm)
    return None


def _magnitude(model: Model, ref) -> tuple[float | None, Unit | None]:
    e = model.get(ref)
    if e is None:
        return None, None
    val = _measure_value(e.args[0]) if e.args else None
    unit = _unit(model, e.args[1]) if len(e.args) > 1 else None
    return val, unit


def _datums(model: Model, systems) -> tuple[str, ...]:
    """DATUM_SYSTEM の並びから記号（A/B/C…）を順に取る。"""
    out: list[str] = []
    if not systems:
        return ()
    for sref in systems if isinstance(systems, list) else [systems]:
        ds = model.get(sref)
        if ds is None:
            continue
        comps = ds.args[4] if len(ds.args) > 4 else None
        if not isinstance(comps, list):
            continue
        for cref in comps:
            comp = model.get(cref)
            if comp is None:
                continue
            base = comp.args[4] if len(comp.args) > 4 else None
            for label in _compartment_labels(model, base):
                out.append(label)
    return tuple(out)


def _datum_label(model: Model, ref) -> str | None:
    d = model.get(ref)
    if d is None:
        return None
    label = d.args[4] if len(d.args) > 4 else None
    return str(label) if label else None


def _compartment_labels(model: Model, base) -> list[str]:
    """区画1つ分の記号。共通データムは 'A-B' のように連結する。

    COMMON_DATUM_LIST((#76,#77)) は2つのデータムが1つの区画として働く形で、
    ASME Y14.5 では A-B と書く。実物（FTC-08）で出てきた。
    """
    if isinstance(base, str) and "COMMON_DATUM_LIST" in base:
        labels = [
            _datum_label(model, Ref(int(n))) for n in _TYPED_REFS.findall(base)
        ]
        joined = "-".join([x for x in labels if x])
        return [joined] if joined else []
    label = _datum_label(model, base)
    return [label] if label else []


@dataclass
class Tolerance:
    """幾何公差1件。"""

    id: int
    kind: str  # POSITION_TOLERANCE など
    label: str  # 日本語の呼び名
    name: str  # 'Position.21'
    value: float | None
    unit: str
    value_mm: float | None
    datums: tuple[str, ...] = ()
    modifiers: tuple[str, ...] = ()

    def key(self) -> tuple:
        """突き合わせ用。名前は CAD 由来で揺れるので使わない。"""
        return (self.kind, round(self.value_mm, 6) if self.value_mm is not None else None, self.datums)


@dataclass
class Datum:
    id: int
    label: str


@dataclass
class Extract:
    schema: str
    tolerances: list[Tolerance] = field(default_factory=list)
    datums: list[Datum] = field(default_factory=list)

    @property
    def has_semantic_pmi(self) -> bool:
        return bool(self.tolerances or self.datums)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in self.tolerances:
            out[t.kind] = out.get(t.kind, 0) + 1
        return dict(sorted(out.items()))


def _leaf_kind(e: Entity) -> str | None:
    for t in e.types:
        if t in TOLERANCE_KINDS:
            return t
    return None


def extract(model: Model) -> Extract:
    out = Extract(schema=model.schema)

    seen: set[int] = set()
    for kind in TOLERANCE_KINDS:
        for e in model.of(kind):
            if e.id in seen:
                continue
            seen.add(e.id)
            leaf = _leaf_kind(e) or kind
            base = e.parts.get("GEOMETRIC_TOLERANCE") or e.args
            if len(base) < 3:
                continue
            name = str(base[0] or "")
            val, unit = _magnitude(model, base[2])
            mods = e.parts.get("GEOMETRIC_TOLERANCE_WITH_MODIFIERS") or []
            modifiers = tuple(str(x) for x in (mods[0] if mods and isinstance(mods[0], list) else []))
            dref = e.parts.get("GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE") or []
            datums = _datums(model, dref[0] if dref else None)
            out.tolerances.append(
                Tolerance(
                    id=e.id,
                    kind=leaf,
                    label=TOLERANCE_KINDS[leaf],
                    name=name,
                    value=val,
                    unit=unit.name if unit else "",
                    value_mm=(val * unit.mm_per) if (val is not None and unit) else None,
                    datums=datums,
                    modifiers=modifiers,
                )
            )

    for e in model.of("DATUM"):
        label = e.args[4] if len(e.args) > 4 else None
        if label:
            out.datums.append(Datum(id=e.id, label=str(label)))

    out.tolerances.sort(key=lambda t: (t.kind, t.value_mm or 0, t.datums))
    out.datums.sort(key=lambda d: d.label)
    return out
