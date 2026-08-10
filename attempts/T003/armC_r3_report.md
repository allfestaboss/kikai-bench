# T003 armC_r3 報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（1 ファイル）

## どう読み取ったか

自作の Part 21 パーサ（Python 標準ライブラリのみ、正規表現＋手書きトークナイザ）を書いて読んだ。
STEP / AP242 専用ライブラリは一切使っていない。

1. `DATA;` 〜 最後の `ENDSEC;` を切り出し、文字列リテラル（`''` エスケープ）と `/* */`
   コメントを尊重しながら `;` で実体レコードに分割。
2. `#id = TYPE(args)` の単純実体と `#id = ( TYPE(args) TYPE(args) ... )` の複合実体の
   両方を、深さ付きのカンマ分割で引数リストに落とした。
3. 幾何公差の抽出は「葉の型を持つ実体」または「GEOMETRIC_TOLERANCE を含む複合実体」。
   結果 28 件（POSITION 11 / SURFACE_PROFILE 12 / FLATNESS 3 / PERPENDICULARITY 2）。

### 判断に迷った箇所

**(1) 単純実体の第5引数がデータム系だと気づくまで**

`#107=PERPENDICULARITY_TOLERANCE('Perpendicularity.1','',#10003,#993,(#331))` が
引数 5 個で、GEOMETRIC_TOLERANCE の 4 属性より 1 個多い。
AP242 MIM では姿勢公差（perpendicularity 等）が `geometric_tolerance_with_datum_reference`
の subtype なので、単純実体として書かれると継承属性 `datum_system` が第5引数に出る、と解釈した。
中身が DATUM_SYSTEM (#331/#332) を指していることで裏取りした。
一方 FLATNESS_TOLERANCE は引数 4 個（`geometric_tolerance` 直下の subtype）で整合する。

**(2) データムの順序**

規則3 に従い `DATUM_SYSTEM` の constituents（LIST）の並び順をそのまま優先順位とした。
並べ替えは一切していない。結果として A→B→C 以外の順（例: #111/#134 が `C,A,B`、
#133 が `E,A,B`、#135 が `D,B,C`）が出ているが、これはファイルの区画順そのものである。
「図面としてはこうあるべき」で直したくなる箇所だが、規則1 に従い直していない。

**(3) 公差値の丸め ← 課題文が決めていない（下記「課題が決めていない箇所」参照）**

**(4) 複合公差の上下**

`GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',relating,related)` が 4 組。
`relating` 側の公差値が大きく（0.05 in）、`related` 側が小さい（0.01 in）ので、
記入例の上下（upper が 1.2、lower が 0.2）と同じ向きと判断し、
relating=upper / related=lower とした。
なお本課題は複合公差を設問に含めていない（Q6 除外）が、記入例にフィールドがあるので埋めた。

## 読めなかった箇所

なし。28 件すべてについて 15 フィールドを埋めた。欠損申告はゼロ。

参考までに、以下は**ファイルに存在しないので** null / 空にした（読めなかったのではない）:

- `projected_length_mm`: 全件 null。`PROJECTED_ZONE_DEFINITION` が 0 件。
- `unit_length_mm`: 全件 null。`GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT` が 0 件。
- `unit_area_shape`: 全件 ""。`GEOMETRIC_TOLERANCE_WITH_DEFINED_AREA_UNIT` が 0 件。
- 共通データム: `COMMON_DATUM_LIST` が 0 件。全 27 区画の base は単一 DATUM 直参照。
  規則4 のハイフン連結は適用対象なし。
- `zone_form`: `TOLERANCE_ZONE` は 9 件しかなく、#138 / #139 と輪郭度 12 件・平面度 3 件・
  直角度 2 件には対応する zone がないので ""。存在する 9 件のうち #135 だけが `spherical`、
  残り 8 件が `cylindrical or circular`。
- データム区画の modifiers（`DATUM_REFERENCE_COMPARTMENT` 第6引数）は全件 `$`。

（これらは前回 T001 で 6 走が揃って null にした「聞かれていないフィールド」に相当するが、
今回は記入例に全フィールドが出ているので、存在しないことを確認したうえで明示的に埋めた。）

## 単位換算

規則5 に従い、外から 25.4 を持ち込まず、ファイル内の連鎖だけで係数を導いた:

```
#10033 = ( CONVERSION_BASED_UNIT('inch',#9962) LENGTH_UNIT() NAMED_UNIT(#10031) )
#9962  = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960)
#9960  = ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) )
```

→ 1 inch = 25.4 millimetre。公差 28 件の magnitude はすべて `#10033`（inch）を参照している。
`unit` は CONVERSION_BASED_UNIT の name 属性そのまま `"inch"`（記入例の ctc_03 と同じ表記）。

## 課題文が決めていないと思った箇所

**(A) 公差値を丸めるかどうか。**これが一番大きい。
このファイルの `LENGTH_MEASURE` はエクスポータの浮動小数ノイズを含んでいる:

| 生値 | 明らかな設計意図 |
|---|---|
| `0.012000000000048` | 0.012 |
| `0.0250000000001` | 0.025 |
| `0.01500000000006` | 0.015 |
| `0.01000000000004` | 0.010 |
| `0.0100000000000401` | 0.010 |
| `0.02000000000008` | 0.020 |
| `0.04000000000016` | 0.040 |
| `0.0500000000002` | 0.050 |

一方 `0.02` `0.01` `0.05` はきれいに入っている（同じファイル内で両方混在）。
規則1「ファイルに実際に入っているものを報告する」に従い、**丸めずに生値のまま**出した。
`value_mm` も生値 × 25.4 を IEEE double でそのまま計算した値（例 `0.3048000000012192`）。
課題文は有効数字にも丸めにも触れていない。採点が完全一致なら参照解も同じパーサ由来のはずで
生値が正解、丸めありなら丸めた値が正解になる。**どちらに転んでもおかしくない箇所**なので、
許容誤差付き比較でないと腕の実力ではなく丸め方針の一致を測ることになる。

**(B) `datums` 一覧の並び順。**記入例（A..J / A..F）はアルファベット順とも
ファイル内出現順とも読める。このファイルは実体 id 順だと `D,B,C,A,E,F,H,G,J,K` で
アルファベット順と一致しないため、どちらか決めないといけない。
記入例に合わせて**アルファベット順**（A,B,C,D,E,F,G,H,J,K の 10 個）にした。
（I は ASME 慣行どおり欠番。K まであるのは実際にファイルにある。）

**(C) `tolerances` 配列の並び順。**記入例は id 昇順でもファイル出現順でもない
（99, 176, 96, 486, 487）。id で突き合わせる前提と読み、**id 昇順**にした。

**(D) `file` フィールドがパスかベース名か。**`files[].path` は `corpus/nist/...` だが
記入例はベース名なので、**ベース名**にした。

## 課題・記入例の側の欠陥だと思ったもの

**1. `zone_form` に記入例が示していない値 `"spherical"` が実在する。**
記入例は `"cylindrical or circular"` と `""` の 2 通りしか見せていない。
本ファイルの #135（Position.15）は `TOLERANCE_ZONE_FORM('spherical')` である。
文字列をそのまま写すのが正解だと推測して `"spherical"` としたが、
記入例に列挙がない以上、正規化語彙（例えば `"spherical"` か `"SPHERICAL"` か）は課題文からは決まらない。
`unit_area_shape` の記入例が `"RECTANGULAR"` と**大文字**なのに `zone_form` が
**小文字の英文フレーズ**という不揃いがあり、片方だけ見て大文字化してしまう腕が出そうな形になっている。
（実際はどちらもファイルの文字列そのままで、`TOLERANCE_ZONE_FORM` の name が小文字英文、
`AREA_UNIT_TYPE` の enum が大文字、というだけの違いである。）

**2. 記入例のファイル選択で `PERPENDICULARITY_TOLERANCE` の形が見えない。**
記入例 2 ファイルは POSITION / STRAIGHTNESS / SURFACE_PROFILE / FLATNESS の 4 種で、
すべて `GEOMETRIC_TOLERANCE` 直下の subtype か複合実体である。
本ファイルにある姿勢公差は**単純実体なのに第5引数にデータム系を持つ**という別の形をしていて、
これは記入例からは推測できない。ここを取りこぼすと 2 件のデータムが丸ごと空になる。
（「記入例で全フィールドを非空にした」という修正は効いているが、
「全**実体形**を見せた」わけではない、という残りの穴。）

**3. 記入例の `label`（日本語名）に語彙表がない。**
本ファイルに必要な `直角度`（PERPENDICULARITY）は記入例にない。
`label` が採点対象なら、腕ごとに `直角度` / `垂直度` などブレる。
`kind` が STEP 実体名で一意に決まる以上、`label` は冗長で、
採点すると読解力ではなく訳語の一致を測ることになる。

**4. 設問文と `answer_format` のフィールドが対応していない。**
`asked` は 5 問（種別・値・単位／mm 換算／データム優先順／材料状態修飾子／データム記号一覧）だが、
`answer_format` には `zone_form` `projected_length_mm` `unit_length_mm` `unit_area_shape`
`composite_role` `composite_partner` `name` `label` が追加で入っている。
T001 のときに 6 走が揃って null にしたのはこれらであり、
`answer_format_note` は「記入例に非空で出しておいた」ことで手当てしているが、
**`asked` 側は一字も直っていない**（設問・規則は T001 と同一と明記されている）。
つまり「訊かれていないが採点される」という構造自体は残っている。
記入例を読まずに `asked` だけを読む腕は、今回も同じ 6 フィールドを落とす。
なお `grade_levels_note` で Q6（複合公差）は除外されているのに
`composite_role` / `composite_partner` は記入例に残っており、
「採点しないが書かせる」フィールドになっている。

**5. `answer_format_note` の「採点対象のフィールドが全て非空で現れるように選んである」が、
本ファイルでは 3 フィールドが構造的に全件空になる。**
`projected_length_mm` / `unit_length_mm` / `unit_area_shape` は本ファイルに該当実体が
1 件も存在しない。記入例で非空を見せた効果は「そのフィールドの存在に気づかせる」ことまでで、
本番の答えは全件 null / "" になる。ここは欠陥というより、
「記入例で埋まったから本番も埋まるはず」という診断の検証にはならない箇所である旨の注意書き。
（診断の検証に効くのは `zone_form` と `composite_role` / `composite_partner` の 3 つだけ。）

## ファイルの内部矛盾

**1. 浮動小数の書き出しが同一ファイル内で不統一。**上記 (A) の表のとおり、
同じ 0.010 in が `0.01000000000004`（#9981, #10006）と `0.0100000000000401`（#9983）の
2 通りで書かれている。同じ 0.05 in も `0.0500000000002`（#9963 等）と `0.05`（#10028）の 2 通り。
セマンティックには同一の公差値が、ビット列としては別物になっている。
値でグルーピングする実装は、ここで同じ公差を別扱いにする。

**2. 単位実体が重複定義されている。**
`#9959` と `#9960` はどちらも `SI_UNIT(.MILLI.,.METRE.)` の同一内容で、別 id で 2 つある。
さらに `CONVERSION_BASED_UNIT('MILLIMETRE',#9961)`（#10032、係数 1.0）もあり、
「ミリメートル」を表す実体が 3 つ存在する。
公差の magnitude が参照するのは `#10033`（inch）のみなので実害はないが、
`GLOBAL_UNIT_ASSIGNED_CONTEXT` が指すのは `#10032`（MILLIMETRE）の方であり、
**コンテキストの長さ単位（mm）と公差値の単位（inch）が食い違っている。**
課題文の「ファイルの単位系は inch」はコンテキストではなく公差の magnitude を指していると読んだ。

**3. `TOLERANCE_ZONE` が一部の公差にしかない。**
位置度 11 件のうち #138 / #139 には zone がなく、他 9 件にはある。
輪郭度・平面度・直角度には 1 件もない。
公差域の形が本来定義されるべき公差（特に位置度 #138/#139）で欠けているので、
ファイル側の記述漏れの可能性がある。推測で補わず "" にした。

**4. 公差名の重複。**`'Position.1'` が #112 と #133 の 2 件にある（値もデータムも異なる）。
`name` をキーにする実装は衝突する。

## 制約違反

なし。

- 見た範囲: `tasks/T003/task.json`、`tasks/T003/FROZEN_T003.json`（tasks/T003/ 配下として許可範囲と判断）、
  `corpus/nist/`（ディレクトリ一覧と対象 1 ファイル、および `head -c 1500` でヘッダ）。
  `FROZEN_T003.json` の中身はハッシュのみで、参照解の内容は漏れていない。
- `reference/` `bench/` `checker/` `out/` `README.md` `arms/` `docs/` は開いていない。
  `attempts/` は自分の出力 2 ファイルを書いただけで、一覧も読み取りもしていない。
- `tasks/T001` `tasks/T002` は開いていない。
- 使用ツール: Python 3 標準ライブラリのみ（`re` `json` `sys` `collections` `os`）。
  STEP / AP242 専用ライブラリ（steputils, pythonocc, ifcopenshell 等）は不使用。
  シェルは `ls` `grep` `wc` `head` `find` のみ。
- 一時ファイルは
  `/private/tmp/claude-501/-Users-boss-dev-01-projects/826e8fde-631a-4aed-a5c1-124ba794daae/scratchpad/T003_armC_r3/`
  の下のみ（`stepparse.py` `dump.py` `mag.py` `extract.py` `emit.py` `dump.txt` `rows.json`）。
