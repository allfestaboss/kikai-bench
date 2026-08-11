# T005 armC_r3 報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（1ファイル）
出力: `attempts/T005/armC_r3.json`

## どう読み取ったか

STEP 専用ライブラリは使っていない。Python 標準ライブラリだけで Part 21 の
トークナイザ／パーサを自作した（`parse.py`）。

1. `DATA;` 〜 `ENDSEC;` を切り出し、文字列リテラル（`''` エスケープ込み）の外側の
   `;` で文に分割。`#id=` を剥がして、単純実体は `NAME(args)`、複合実体は
   `(NAME(args) NAME(args) ...)` として型名ごとに分解。パラメータは括弧の深さと
   文字列を見てトップレベルのカンマで分割。実体 10034 件、うち複合 165 件。
2. 幾何公差は「葉の型」（`POSITION_TOLERANCE` などのリーフ名）を持つ実体として収集。
   複合実体では `GEOMETRIC_TOLERANCE` 部分から name/magnitude を、
   `GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE` から datum_system を、
   `GEOMETRIC_TOLERANCE_WITH_MODIFIERS` から修飾子を取った。
   単純実体（`PERPENDICULARITY_TOLERANCE`, `FLATNESS_TOLERANCE`）は継承順の
   属性位置（name, description, magnitude, toleranced_shape_aspect [, datum_system]）で読んだ。
3. 単位はファイル内で解決した。`#10033=(CONVERSION_BASED_UNIT('inch',#9962) LENGTH_UNIT() NAMED_UNIT(#10031))`、
   `#9962=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960)`、`#9960` は
   `SI_UNIT(.MILLI.,.METRE.)`。よって 1 inch = 25.4 mm を**この2実体から**得ている
   （外部知識としての 25.4 は持ち込んでいない）。全公差の magnitude は `#10033`（inch）参照。
4. データムは `DATUM_SYSTEM` の第5属性（区画リスト）の順に `DATUM_REFERENCE_COMPARTMENT`
   → `DATUM` の identification（第5属性）を並べた。`COMMON_DATUM_LIST` は
   このファイルには存在しない（実装は入れてあるが発火せず）。
5. 公差域の形は `TOLERANCE_ZONE(name, desc, of_shape, product_definitional, defining_tolerance, form)`
   の第5属性から公差実体へ逆引きし、第6属性の `TOLERANCE_ZONE_FORM` の name 文字列を
   そのまま入れた（`cylindrical or circular` / `spherical`）。
6. 複合公差は `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite',...,relating,related)` の
   relating を upper、related を lower とした（記入例の 486/487 の並びに合わせた）。

### 判断に迷った箇所

- **値の丸め**。ファイルの inch 値には浮動小数の残差がある（例 `0.0250000000001`,
  `0.0100000000000401`, `0.012000000000048`）。生値をそのまま出すか丸めるか迷い、
  小数9桁で丸めた（→ 0.025 / 0.01 / 0.012）。`value_mm` は**生値 × 25.4** を計算してから
  同じく9桁で丸めた。差は 1e-13 オーダーなので採点許容差には入るはずだが、
  生値一致を要求する採点器だと落ちる可能性がある。
- **公差の並び順**。設問も記入例も順序を指定していないので、実体番号の昇順にした。
- **データム記号の並び順**。記入例が A,B,C… とアルファベット順だったのでそれに倣った。

## 答案様式に無いが設問で訊かれているフィールド

**あった。`zone_form`（公差域の形）**。記入例の各公差オブジェクトには
`modifiers` の次が `projected_length_mm` で、公差域の形に相当するキーが無い。
一方 `asked` の4番目は「(2) **公差域の形**（円筒か球かなど。TOLERANCE_ZONE_FORM の名前をそのまま）」と
明示的に訊いている。

扱い: `answer_format_note` が「`zone_form` は意図的に記入例から外してある」「設問が訊いて
いるので答案には入れること」と書いているので、**キー名を `zone_form`** とし（task.json の
note / answer_format_note がこの名前で呼んでいるため）、`asked` の列挙順に合わせて
`modifiers` と `projected_length_mm` の**あいだ**に挿入した。値は
`TOLERANCE_ZONE_FORM` の name 文字列そのまま、該当が無いものは空文字 `""`
（「該当が無いものは空で報告する」という指示に従い、`null` ではなく空文字にした。
`projected_length_mm` / `unit_length_mm` は記入例が `null` を使っているのでそちらに合わせた）。

## corpus 配下で開いたファイル

**対象の STEP ファイル 1 本のみ**。
`corpus/nist/NIST-FTC-PMI-Definitions.xlsx` と `corpus/nist/NIST-README.txt` は**開いていない**。
他の STEP ファイルも開いていない（`ls -la corpus/nist/` でディレクトリ一覧は見たが、
中身は読んでいない）。`reference/` `bench/` `checker/` `out/` `README.md` `arms/` `docs/`、
`attempts/` の他の答案、`tasks/T005/FROZEN_T005.json`、過去課題の `tasks/` `attempts/` は
いずれも開いていない。

## 読めなかった箇所

無し。公差 28 件すべてについて、種別・値・単位・データム・修飾子・公差域の形を解決できた。
ファイル自身のメタデータ `#9948=INTEGER_REPRESENTATION_ITEM('number of geometric tolerances',28.)` と
`#9949=(...'number of composite tolerances',4.)` が、抽出した 28 件・複合4組と一致している。

`projected_length_mm` / `unit_length_mm` / `unit_area_shape` は「読めなかった」のではなく
**ファイルに該当実体が存在しない**。実体型の全数え上げで確認済み:
`PROJECTED_ZONE_DEFINITION`、`GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT`、
`GEOMETRIC_TOLERANCE_WITH_DEFINED_AREA_UNIT`、`RUNOUT_ZONE_DEFINITION`、
`COMMON_DATUM_LIST`、`UNEQUALLY_DISPOSED_GEOMETRIC_TOLERANCE` はいずれも 0 件。
よって全公差で `projected_length_mm=null`, `unit_length_mm=null`, `unit_area_shape=""`。

## 課題文が決めていないと思った箇所

1. **`zone_form` のキー名**。設問は日本語で「公差域の形」としか言わず、様式にキーが無い。
   `note` / `answer_format_note` が `zone_form` と呼んでいるのでその綴りを採用した。
2. **`zone_form` の挿入位置**。`asked` の列挙順（modifiers の次）に置いた。
   JSON なのでキー順は本来意味を持たないはずだが、明示が無い。
3. **`zone_form` の「該当なし」の表現**。空文字 `""` にした（1. の理由は上記）。
4. **値の丸め方針**（上記「判断に迷った箇所」）。
5. **公差の並び順**（実体番号昇順にした）。
6. **`label`（日本語名）の語彙**。記入例には 位置度 / 真直度 / 面の輪郭度 / 平面度 しか
   出てこない。このファイルにしか出ない `PERPENDICULARITY_TOLERANCE` の label を
   「直角度」とした。語彙表が示されていないので、採点が文字列一致なら揺れうる。
7. **`datums` に何を挙げるか**。「ファイルに定義されているデータム記号」を
   `DATUM` 実体の identification 全件と解釈した（後述の内部矛盾も参照）。

## 課題／記入例の側の欠陥だと思った箇所

1. **記入例の 2 ファイルが対象ファイルと紛らわしい。**`answer_format` の
   `results[].file` が `nist_stc_10_...` と `nist_ctc_03_...` で、どちらも実在して
   `corpus/nist/` に置いてある。`answer_format_note` で打ち消してはいるが、
   様式と対象の取り違えを誘う形にはなっている。
2. **`composite_role` / `composite_partner` は様式にあるのに `asked` が訊いていない。**
   `grade_levels_note` は「訊いていないものを採点しないため Q6 は採点しない」と言うが、
   だとすると様式にキーが残っているのは矛盾している。T005 は「訊けば埋まるか」を測る
   課題なので、逆方向（**様式にあるが訊かれていない**）のフィールドが同居しているのは
   交絡になりうる。今回は両方埋めた。
3. **`asked` (4) の「(5) 単位あたりの領域の形」の値域が未定義。**記入例の
   `unit_area_shape` は `"RECTANGULAR"`（STEP の enum 名）だが、`zone_form` は
   「TOLERANCE_ZONE_FORM の名前をそのまま」＝生の文字列。同じ設問の中で
   enum 名と自由文字列が混在しており、どちらの流儀かは各キーの実装依存になっている。
4. **単位換算の指示と `unit` フィールドの関係が未定義。**記入例には
   `"unit": "millimetre"` の行がある。`CONVERSION_BASED_UNIT` の name は
   `'MILLIMETRE'`（大文字）で入っていることがある（このファイルの `#10032` がそう）。
   「名前をそのまま」なのか正規化するのかが `unit` については書かれていない。
   今回は該当が `'inch'`（小文字）だけだったので実害は無かった。

## ファイルの内部矛盾

1. **`'number of datums'` が 6 だが `DATUM` 実体は 10 件。**
   `#9950=INTEGER_REPRESENTATION_ITEM('number of datums',6.)`。
   実際の `DATUM` は A,B,C,D,E,F,G,H,J,K の 10 件。内訳を追うと、
   A/B/C/D/E/F は `DATUM_FEATURE`（6件）から `SHAPE_ASPECT_RELATIONSHIP` で来ており、
   G/H/J/K は `PLACED_DATUM_TARGET_FEATURE`（6件、`'number of datum targets',6.` と一致）
   から来ている。つまり NIST 側の「6」はデータムフィーチャ由来のものだけを数えている。
   設問は「ファイルに定義されているデータム記号を全て」なので **10 件すべて**を出した。
2. **位置度 11 件のうち 2 件に `TOLERANCE_ZONE` が無い。**
   `#138`(Position.9, データム D,C,K) と `#139`(Position.8, データム D,C,J) だけ
   `TOLERANCE_ZONE` から参照されていない。他の 9 件の位置度にはすべて zone がある
   （`TOLERANCE_ZONE` は 9 件ちょうど）。この 2 件だけ公差域の形が引けないのは
   モデル側の取りこぼしに見える。答案では `zone_form: ""` とした。
3. **プレゼンテーション側の `DESCRIPTIVE_REPRESENTATION_ITEM('datum references', ...)` は
   セマンティック側と一致していた。**（矛盾ではないが照合として記す。）
   例: `#698='C,A,B'` は `#111` の `DATUM_SYSTEM #329` = C,A,B と一致、
   `#717='D,H'` は `#136` と一致、`#719='D,C,J'` は `#138` と一致。
   規則どおり答案はセマンティック側（`DATUM_SYSTEM`）のみから作っている。
4. **同名の幾何公差が複数ある。**`'Position.1'` が `#112` と `#133` の 2 件、
   複合公差の上下は同じ name を共有する（`'Position surfacic profile.9'` が `#337`/`#338`）。
   name は一意識別子として使えない。答案では `id`（実体番号）で区別している。

## 制約違反

無し。STEP/AP242 専用ライブラリは使用していない（Python 標準ライブラリの
`json` / `re` / `sys` / `os` のみ）。一時ファイルは
`/private/tmp/claude-501/-Users-boss-dev-01-projects/826e8fde-631a-4aed-a5c1-124ba794daae/scratchpad/T005_armC_r3/`
の下だけに置いた。
