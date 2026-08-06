"""AP242 の semantic PMI を取り出して正規化する。

実物（NIST の AP242 ファイル）で確認した経路だけを実装している。

  公差値   GEOMETRIC_TOLERANCE(.., #magnitude, ..)
           magnitude は書き出したCADによって3通りの形が出る（実物で確認）:
             (a) LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(v), #unit)          FTC-06/09
             (b) 複合実体で MEASURE_WITH_UNIT(POSITIVE_LENGTH_MEASURE(v), #unit) FTC-08/11
           単位も2通り:
             (c) CONVERSION_BASED_UNIT('inch'|'INCH', #factor, ..)  -> factor が mm 換算
             (d) 複合 SI_UNIT。パートは [prefix, name] の2つで、
                 単純形の SI_UNIT(dim, prefix, name) と索引が違う。ここを取り違えると
                 MILLI を読み落として換算が1000倍狂う（実際に踏んだ）

  複合公差 GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',#上段,#下段)
           1つの公差記入枠が上下2段になっている形。上段は完全なデータム系に対する
           位置を、下段はその部分集合に対する姿勢・形状を規制する。
           STEP 上は別々の公差実体として現れるので、関係を見ないと
           「同じ名前の公差が2つある」ようにしか見えない。

  突出公差域 PROJECTED_ZONE_DEFINITION(#tolerance_zone, (), #projection_end, #length)
           ASME Y14.5 の Ⓟ。ねじ穴などで、公差域を部品の外へ突き出させる指定。
           突出長さは公差記入枠に Ⓟ.260 のように書かれる。
           公差そのものではなく TOLERANCE_ZONE 側にぶら下がるので、
           公差の実体だけ見ていると丸ごと落ちる。

  公差域   TOLERANCE_ZONE('',$,#shape,.F.,(#tolerance),#form)
           -> TOLERANCE_ZONE_FORM('spherical' | 'cylindrical or circular')
           円筒か球かで意味が全く違う（ASME Y14.5 の ⌀ と S⌀）。
           NIST の定義 xlsx との突き合わせで、ここが抜けていることが分かった。

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
            src = factor.args or factor.parts.get("MEASURE_WITH_UNIT") or []
            mm = (_measure_value(src[0]) if src else None) or 1.0
        return Unit(name=str(name).lower(), mm_per=mm)
    if "SI_UNIT" in e.types:
        # 複合実体のパートは (prefix, name)。単純形は (dimensions, prefix, name)。
        args = e.parts.get("SI_UNIT")
        if args is None:
            args = e.args[1:] if len(e.args) > 2 else e.args
        prefix = args[0] if len(args) > 0 else None
        name = args[1] if len(args) > 1 else "METRE"
        mm = {"MILLI": 1.0, "CENTI": 10.0, "MICRO": 0.001}.get(str(prefix or ""), 1000.0)
        return Unit(name=f"{prefix or ''}{name}".lower(), mm_per=mm)
    return None


def _magnitude(model: Model, ref) -> tuple[float | None, Unit | None]:
    e = model.get(ref)
    if e is None:
        return None, None
    # 単純形なら args、複合形なら値と単位を持つパートを探す
    src = e.args
    if not src:
        for part in ("MEASURE_WITH_UNIT", "LENGTH_MEASURE_WITH_UNIT"):
            cand = e.parts.get(part)
            if cand and len(cand) >= 2:
                src = cand
                break
    if not src:
        return None, None
    val = _measure_value(src[0])
    unit = _unit(model, src[1]) if len(src) > 1 else None
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


def _datum_label(model: Model, ref, depth: int = 0) -> str | None:
    """データム記号を取る。間に1段はさまる形（DATUM_REFERENCE_ELEMENT 等）もある。

    記号の位置に参照が入っていたら、もう一段たどる。
    ここで str() を通してしまうと Ref が '#437' という文字列になり、
    解決に失敗したことが値のように見えてしまう（実際に踏んだ）。
    """
    if depth > 3:
        return None
    d = model.get(ref)
    if d is None:
        return None
    label = d.args[4] if len(d.args) > 4 else None
    if isinstance(label, Ref):
        return _datum_label(model, label, depth + 1)
    if isinstance(label, str) and label:
        return label
    return None


def _compartment_labels(model: Model, base) -> list[str]:
    """区画1つ分の記号。共通データムは 'A-B' のように連結する。

    COMMON_DATUM_LIST((#76,#77)) は2つのデータムが1つの区画として働く形で、
    ASME Y14.5 では A-B と書く。実物（FTC-08）で出てきた。
    """
    if isinstance(base, str) and "COMMON_DATUM_LIST" in base:
        labels = [
            _datum_label(model, Ref(int(n))) for n in _TYPED_REFS.findall(base)
        ]
        labels = [x for x in labels if isinstance(x, str)]
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
    zone_form: str = ""  # 'spherical' / 'cylindrical or circular' / 未指定なら空
    projected_length: float | None = None  # 突出公差域の長さ（ファイルの単位）
    projected_length_mm: float | None = None
    composite_role: str = ""  # 'upper' / 'lower' / 単独なら空
    composite_partner: int | None = None  # 対になるもう一段の実体ID

    def key(self) -> tuple:
        """突き合わせ用。名前は CAD 由来で揺れるので使わない。"""
        return (
            self.kind,
            round(self.value_mm, 6) if self.value_mm is not None else None,
            self.datums,
            self.zone_form,
            round(self.projected_length_mm, 6) if self.projected_length_mm is not None else None,
            self.composite_role,
        )


@dataclass
class Datum:
    id: int
    label: str


@dataclass
class Extract:
    schema: str
    tolerances: list[Tolerance] = field(default_factory=list)
    datums: list[Datum] = field(default_factory=list)
    composites: list[tuple[int, int]] = field(default_factory=list)  # (上段, 下段)

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


def _composites(model: Model) -> tuple[list[tuple[int, int]], dict[int, tuple[str, int]]]:
    """複合公差の対。関係実体の第3引数が上段、第4引数が下段。"""
    pairs: list[tuple[int, int]] = []
    role: dict[int, tuple[str, int]] = {}
    for r in model.of("GEOMETRIC_TOLERANCE_RELATIONSHIP"):
        if len(r.args) < 4 or str(r.args[0] or "") != "composite":
            continue
        up, low = model.get(r.args[2]), model.get(r.args[3])
        if up is None or low is None:
            continue
        pairs.append((up.id, low.id))
        role[up.id] = ("upper", low.id)
        role[low.id] = ("lower", up.id)
    return pairs, role


def _zone_info(model: Model) -> tuple[dict[int, str], dict[int, tuple[float, Unit | None]]]:
    """公差 -> (公差域の形, 突出長さ)。どちらも TOLERANCE_ZONE 側にぶら下がる。"""
    forms: dict[int, str] = {}
    zone_to_tols: dict[int, list[int]] = {}
    for z in model.of("TOLERANCE_ZONE"):
        if len(z.args) < 6:
            continue
        targets = z.args[4]
        ids = []
        for t in targets if isinstance(targets, list) else [targets]:
            e = model.get(t)
            if e is not None:
                ids.append(e.id)
        zone_to_tols[z.id] = ids
        form = model.get(z.args[5])
        if form is not None and form.args:
            name = str(form.args[0] or "")
            for i in ids:
                forms[i] = name

    projected: dict[int, tuple[float, Unit | None]] = {}
    for pz in model.of("PROJECTED_ZONE_DEFINITION"):
        if len(pz.args) < 4:
            continue
        zone = model.get(pz.args[0])
        if zone is None:
            continue
        val, unit = _magnitude(model, pz.args[3])
        if val is None:
            continue
        for i in zone_to_tols.get(zone.id, []):
            projected[i] = (val, unit)
    return forms, projected


def extract(model: Model) -> Extract:
    out = Extract(schema=model.schema)
    forms, projected = _zone_info(model)
    out.composites, roles = _composites(model)

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
            # データム参照は2通りの入り方がある（実物で確認）:
            #   複合形 GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE((#datum_system))
            #   単純形 XXX_TOLERANCE(name, desc, #mag, #aspect, (#datum_system))
            # 後者は第5引数。複合形だけ見ていると単純形のデータムを丸ごと落とす。
            # 突出公差域は projected_length_* が持つ。修飾子には合成しない。
            # 公差記入枠では Ⓟ として現れるが、ファイルの
            # GEOMETRIC_TOLERANCE_WITH_MODIFIERS にその列挙値は入っていない。
            # 「ファイルに実際に入っているものを報告する」という規則を
            # 参照解自身が破ってはいけない。
            proj = projected.get(e.id)

            dref = e.parts.get("GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE") or []
            systems = dref[0] if dref else None
            if systems is None and len(e.args) > 4:
                systems = e.args[4]
            datums = _datums(model, systems)
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
                    zone_form=forms.get(e.id, ""),
                    projected_length=proj[0] if proj else None,
                    projected_length_mm=(proj[0] * proj[1].mm_per) if (proj and proj[1]) else None,
                    composite_role=roles.get(e.id, ("", None))[0],
                    composite_partner=roles.get(e.id, ("", None))[1],
                )
            )

    for e in model.of("DATUM"):
        label = e.args[4] if len(e.args) > 4 else None
        if label:
            out.datums.append(Datum(id=e.id, label=str(label)))

    out.tolerances.sort(key=lambda t: (t.kind, t.value_mm or 0, t.datums))
    out.datums.sort(key=lambda d: d.label)
    return out
