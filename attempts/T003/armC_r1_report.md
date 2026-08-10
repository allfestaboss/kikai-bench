# T003 armC_r1 報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`
答案: `attempts/T003/armC_r1.json`（幾何公差 28 件 / データム記号 10 件）

## どう読み取ったか

STEP/AP242 専用ライブラリは使っていない。標準ライブラリだけで
Part 21 物理ファイルの字句解析器を自作した（作業ファイルは scratchpad 下、
`stepparse.py` = トークナイザ、`extract.py` = 抽出）。

経路:

1. `DATA;` 〜 `ENDSEC;` を `#id = 本体 ;` に分割。文字列内の `'` 二重化、
   `/* */` コメント、深さ付き括弧を手で処理。複合実体
   `#111=(GEOMETRIC_TOLERANCE(...)GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE(...)...)`
   は「型名 → 引数」の並びに分解し、葉の型を別に持たせた。
2. 幾何公差 = 葉の型が `*_TOLERANCE`（`PLUS_MINUS_TOLERANCE` を除く）の実体。
   この file では `PERPENDICULARITY_TOLERANCE` 2、`POSITION_TOLERANCE` 11、
   `FLATNESS_TOLERANCE` 3、`SURFACE_PROFILE_TOLERANCE` 12 = 計 28。
   分類できなかった `GEOMETRIC_TOLERANCE` 系実体はゼロ（全数走査で確認）。
3. 公差値 = `GEOMETRIC_TOLERANCE.magnitude` → `LENGTH_MEASURE_WITH_UNIT`。
   単位は `#10033=CONVERSION_BASED_UNIT('inch', #9962)`、
   `#9962=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4), #9960)`、
   `#9960=SI_UNIT(.MILLI.,.METRE.)`。この鎖を辿って mm 係数を組み立てた
   （25.4 を外から持ち込んでいない。ただし後述の欠陥参照）。28 件すべて inch。
4. データムは `DATUM_SYSTEM.constituents`（=`DATUM_REFERENCE_COMPARTMENT` の並び）
   の順に `DATUM.identification` を取った。区画 27 個・データムシステム 12 個の
   参照関係は生テキストと突き合わせて全数照合済み。
5. 公差域の形は `TOLERANCE_ZONE.form` → `TOLERANCE_ZONE_FORM.name`。
6. 複合公差は `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',relating,related)`。

### 記入例2ファイルで較正した

`answer_format` が名指しした `nist_ctc_03_asme1_ap242-e2.stp` と
`nist_stc_10_asme1_ap242-e2.stp` は corpus/ にあり閲覧が許されているので、
自作抽出器をこの2ファイルに掛けて記入例と突き合わせた。
**記入例6行と datums 2件（A..F / A..J）が1文字も違わず再現した。**
これでフィールドの意味（`value` は換算前、`unit` は `CONVERSION_BASED_UNIT.name`
そのまま、`composite_role` の upper/lower の向き、`unit_length_mm` は
`GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT` の長さを mm 換算、など）を確定させた。
較正の過程で自作パーサのバグを2つ潰した（`PROJECTED_ZONE_DEFINITION` の
引数位置、`COMMON_DATUM_LIST` が inline typed value で中身が
`DATUM_REFERENCE_ELEMENT` である点）。どちらも対象ファイルには出現しない。

## 読めなかった箇所

なし。28 件すべてについて全フィールドを埋めた。欠損は出していない。

対象ファイルに存在しない構造（`PROJECTED_ZONE_DEFINITION`、`COMMON_DATUM_LIST`、
`GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT` / `..._DEFINED_AREA_UNIT`）は grep で
0件を確認したうえで、`projected_length_mm`=null、`unit_length_mm`=null、
`unit_area_shape`="" とした。「読めなかった」ではなく「無い」である。

## 課題文が決めていないと思った箇所（と、どちらに決めたか）

1. **浮動小数のノイズを丸めるか否か。**
   ファイルの生値は `LENGTH_MEASURE(0.0500000000002)`、`0.01000000000004` など
   CAD 出力由来のノイズを持つ。課題文にもルールにも丸め方の指定がない。
   記入例の ctc_03 の該当行は生値がちょうど `0.005` / `0.25` だったため較正できなかった。
   → **短い十進表記に丸めた**（0.05 / 0.635 など）。記入例の見た目が全部きれいな
   十進であることに合わせた。生値との差は最大 4e-13 なので、数値比較の採点なら
   どちらでも通る。厳密一致の採点だとここが分岐点になる。

2. **`tolerances` 配列の並び順。** 指定なし（記入例は 99,176,96,486,487 で非整列）。
   → 実体 ID の昇順にした。

3. **`datums` 配列の並び順。** 指定なし。→ アルファベット昇順にした
   （記入例2件もアルファベット順で矛盾しない）。

4. **`composite_role` の upper / lower がどちらの端を指すか。**
   `GEOMETRIC_TOLERANCE_RELATIONSHIP` の relating / related のどちらが上段かは
   課題文に書かれていない。→ **relating = upper、related = lower** とした。
   記入例（486 upper / 487 lower）と一致し、かつ値の大きい側が upper になる
   （上段が粗く下段が細かい＝複合 FCF の通例）ので二重に整合する。

5. **`label`（日本語名）の語彙。** ルールに一切定義がなく、記入例が示すのは
   位置度・真直度・面の輪郭度・平面度の4語だけである。対象ファイルには
   `PERPENDICULARITY_TOLERANCE` が2件あり、その日本語ラベルは課題文のどこにも
   拘束されていない。→ **「直角度」**とした（JIS B 0021 の呼称）。
   「垂直度」も日常的に使われるので、ここは腕の読解力と無関係に点が動く。

6. **データム参照側の修飾子を `modifiers` に入れるか。**
   `DATUM_REFERENCE_COMPARTMENT` の `modifiers`（`SIMPLE_DATUM_REFERENCE_MODIFIER`）は
   公差本体の修飾子とは別物である。記入例は公差本体
   （`GEOMETRIC_TOLERANCE_WITH_MODIFIERS`）だけを載せているように読めたので
   **公差本体のみ**とした。対象ファイルは 27 区画すべて modifiers が `$` なので
   この判断は結果に影響しない。

7. **`unit` 文字列の大小文字。** 対象は全件 `'inch'`（ファイル中の綴りのまま）で
   記入例と一致するので問題ないが、同じファイルは `'MILLIMETRE'` を**大文字で**
   定義しており、記入例は `"millimetre"` と**小文字**で書いている。
   mm 系の公差があるファイルでは「ファイルの綴りをそのまま」と
   「小文字に正規化」が食い違う。今回は影響なし。

## 課題や記入例の側の欠陥だと思った箇所

**(1) `note` が答えの件数を書いてしまっている。**
`task.json` の `note` に「**28件中1件を配っていた**」とある。T003 は
「対象ファイル・参照解は T001 と一字一句同じ」とも書いてあるので、これは
**この課題の採点対象が 28 件であることを課題文が明かしている**ことになる。
27 件や 29 件を数えた腕は、課題文を読んだだけで数え直せる。
同じ段落の「同じ**9箇所**を null で出した」も同様で、採点対象6フィールドのうち
非 null であるべきスロット数を示唆している（実際、私の抽出では `zone_form` が
非空になるのがちょうど 9 件だった）。記入例の欠陥を直す説明のなかで、
別種の情報が漏れている。

**(2) `asked` が訊いていないフィールドを、いまも採点対象にしている。**
`asked` は5問（種別・値・単位／mm 換算／データム順／材料状態修飾子／データム一覧）。
一方 `answer_format` は1公差あたり 15 フィールドある。`asked` のどの文にも
対応しないのは `id` `label` `name` `zone_form` `projected_length_mm`
`unit_length_mm` `unit_area_shape` `composite_role` `composite_partner`。
`note` はこれを「T001 では例に出ていなかったのが原因」と診断して**記入例だけを**
作り直したが、**`asked` の側は直していない**。したがって T003 が測れるのは
「記入例に出せば埋まるか」だけで、「そもそも `asked` が訊いていない」という
もう一方の原因を切り分けられない。両方が同時に成り立ちうるので、
「埋まらなければ診断が間違い」という `note` の対偶は成立しない
（埋まっても、`asked` が壊れている事実は残る）。

**(3) `grade_levels_note` と `answer_format` が食い違う。**
`grade_levels_note` は「この課題は複合公差を設問に含めていない（T002 で追加した）。
腕に訊いていないものを減点しないため Q6 を外す」と言う。ところが
`answer_format` には `composite_role` / `composite_partner` があり、
`answer_format_note` は「採点対象のフィールドが全て非空で現れるように選んである
（…複合公差の上下）」と、複合公差を**採点対象**と明言している。
「訊いていないから Q6 を外す」と「採点対象フィールドである」は両立しない。
対象ファイルには composite の関係が4組（8行）あるので、実害のある食い違いである。
私は `answer_format` に従って埋めた。

**(4) ルール5（換算係数を外から持ち込むな）は、この課題では検査不能。**
`#9962` の係数は厳密に `25.4` なので、ファイルを辿った腕と 25.4 を暗記していた腕の
出力が一致する。答案からは区別できない。ルールとしては正しいが、
この対象ファイルでは測定に反映されない。

**(5) 記入例2ファイルが corpus/ に同梱されているため、公開較正セットとして機能する。**
上に書いたとおり私は実際にそうした。記入例の6行を再現できるまで抽出器を直せる
ので、丸め方・ラベル語彙・upper/lower の向きといった「参照解の書式の癖」を
対象ファイルを見ずに合わせ込める。答えそのものの漏洩ではないが、
**書式一致の点数は読解力ではなく「較正したかどうか」で動く**。
較正した腕としない腕を比べていることになる。

## ファイルの内部矛盾に気づいた点

- **`POSITION_TOLERANCE` 11 件に対し `TOLERANCE_ZONE` は 9 件。**
  `#138`（Position.9、データム D|C|J）と `#139`（Position.8、データム D|C|K）だけ
  公差域が定義されていない。穴の位置度は普通は直径域を持つので、
  この2件はファイル側の取りこぼしに見える。私は推測で補わず `zone_form` を "" にした
  （ルール「図面としてこうあるべき、という推測ではない」に従った）。
- **`GEOMETRIC_TOLERANCE.name` が一意でない。** `#112` と `#133` がどちらも
  `'Position.1'`。複合公差の上下も同名（例: `#337`/`#338` が
  `'Position surfacic profile.9'`）。記入例の stc_10 も 486/487 が同名なので
  これは仕様どおりだが、`name` を鍵に照合すると壊れる。
- **データムは 10 個（A,B,C,D,E,F,G,H,J,K）定義されているのに、
  `DATUM_FEATURE` は 6 個、`PLACED_DATUM_TARGET_FEATURE` は 6 個しかない。**
  実体側との対応が全データムには張られていない。設問は「定義されている
  データム記号」なので `DATUM.identification` を全部挙げた（K を含む）。
  K は `#324` → `#336`（Datum System .12）→ `#139` の1経路でしか使われていない。
- `SURFACE_PROFILE_TOLERANCE` の `#348` だけ名前が `'Geometrical Tolerance.1'` で、
  他 11 件の `'Position surfacic profile.N'` という命名規則から外れている。

## 制約について

- STEP / AP242 専用ライブラリは**使っていない**。パーサは自作、
  標準ライブラリ（`re`, `json`, `os`, `sys`）のみ。
- 閲覧禁止ディレクトリ（`reference/` `bench/` `checker/` `out/` `README.md`
  `arms/` `docs/` `attempts/` の他走行、T001/T002 の `tasks/` と `attempts/`）は
  **一切開いていない**。
- `tasks/T003/FROZEN_T003.json` は許可範囲（`tasks/T003/`）内なので開いた。
  中身は SHA256 ハッシュ一覧のみで、答えは含まれていなかった。
- corpus/ 内の `nist_ctc_03_asme1_ap242-e2.stp` と
  `nist_stc_10_asme1_ap242-e2.stp` を読んだ（記入例の較正のため）。
  corpus/ は閲覧可、かつ `answer_format_note` がこの2ファイルを
  「採点対象ではない」と明記しているので違反ではないと判断したが、
  意図と違うなら上記(5)のとおり申告しておく。
- 一時ファイルは指定された `scratchpad/T003_armC_r1/` 下だけを使った。
