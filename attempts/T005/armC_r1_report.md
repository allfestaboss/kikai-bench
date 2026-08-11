# T005 / armC_r1 報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（AP242 MIM LF、単位系 inch）

## どう読み取ったか

Python 標準ライブラリだけで Part 21 リーダを自作した（STEP/AP242 専用ライブラリは不使用）。

1. `/* */` コメントを文字列リテラル外でのみ除去 → `DATA;`〜`ENDSEC;` を、文字列外の `;` で
   インスタンスに分割 → `#id = 本文` の辞書化（10,034 インスタンス）。
   このファイルは1インスタンスが複数行に折り返されているので、行単位の grep では読めない。
2. 単純実体は `NAME(params)`、複合実体は `( A(..) B(..) )` を型ごとに切り出す小関数を書き、
   パラメータは深さ0のカンマで分割（括弧・文字列を考慮）。
3. 全実体の型を集計して、幾何公差まわりに何が「無い」かを先に確定させた（下記）。

読み取り経路:

- 幾何公差 = 葉の型が `*_TOLERANCE` のもの。複合実体 23 件（POSITION 11 / SURFACE_PROFILE 12）
  ＋単純実体 5 件（FLATNESS 3 / PERPENDICULARITY 2）= **28 件**。
- 公差値 = `GEOMETRIC_TOLERANCE.magnitude` → `LENGTH_MEASURE_WITH_UNIT`。
- 単位 = `#10033 = ( CONVERSION_BASED_UNIT('inch',#9962) LENGTH_UNIT() NAMED_UNIT(#10031) )`、
  `#9962 = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960)`、`#9960` は `SI_UNIT(.MILLI.,.METRE.)`。
  換算係数 25.4 は**このファイル内から**取得（外から 1 inch = 25.4 mm を持ち込んでいない）。
  全 28 件が `#10033`（inch）を参照。
- データム = `DATUM_SYSTEM.constituents` の並び順 → 各 `DATUM_REFERENCE_COMPARTMENT.base` →
  `DATUM.identification`。並び替えはしていない（＝優先順位そのもの）。
- 修飾子 = `GEOMETRIC_TOLERANCE_WITH_MODIFIERS`（4 件のみ、いずれも `.MAXIMUM_MATERIAL_REQUIREMENT.`）。
- 公差域の形 = `TOLERANCE_ZONE.defining_tolerance` から公差へ逆引きし、`TOLERANCE_ZONE.form` →
  `TOLERANCE_ZONE_FORM.name` をそのまま文字列で。9 件（うち 1 件が `spherical`、8 件が
  `cylindrical or circular`）。
- 複合 = `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',#a,#b)` 4 組。`relating`(#a) を upper、
  `related`(#b) を lower とした（#a 側の公差値が常に大きいことで裏取り: 0.05 対 0.01）。

### 判断に迷った箇所

- **`PERPENDICULARITY_TOLERANCE` が単純実体で5属性**（`#107`, `#108`）。
  一見 Part 21 違反に見えるが、shape_tolerance schema では直角度は
  `geometric_tolerance_with_datum_reference` の SUBTYPE なので、単純実体のまま
  第5属性に datum_system リストを持つのが正しい。複合形にする必要があるのは
  position / surface_profile の側（実際ファイルもそうなっている）。矛盾ではないと判断した。
- **共通データム**は `COMMON_DATUM_LIST` が1件も無いので、'A-B' 形式の連結は発生しない
  （実装は入れてあるが未使用）。
- `#993` は `COMPOSITE_SHAPE_ASPECT('','multiple elements',...)` で、これは
  toleranced_shape_aspect が複数要素という意味であり、複合公差（composite FCF）とは別物。
  `composite_role` はあくまで `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite',...)` からのみ取った。

## 答案様式に無いが設問で訊かれているフィールド

**あった。`zone_form`（公差域の形）が記入例のどのレコードにも無い。**
課題の `answer_format_note` が「意図的に外してある。設問が訊いているので答案には入れること」と
明記し、かつ `zone_form` というキー名まで書いているので、その名前でキーを追加した。
配置は `modifiers` の後（設問の (1)(2)(3)(4)(5) の並びに合わせ、
`modifiers` → `zone_form` → `projected_length_mm` → `unit_length_mm` → `unit_area_shape`）。
該当が無いものは `""`（空文字列）とした。他フィールドの空表現（`unit_area_shape` が `""`、
`projected_length_mm` / `unit_length_mm` が `null`）に倣ったもの。

## corpus/ 配下で開いたファイル

**対象の STEP ファイル 1 本のみ。**
`corpus/nist/nist_ftc_06_asme1_ap242-e2.stp` だけを読んだ。
`NIST-FTC-PMI-Definitions.xlsx` と `NIST-README.txt` は開いていない。
他の STEP ファイルも開いていない（`ls` でディレクトリ一覧は見たが、中身は読んでいない）。
`reference/` `bench/` `checker/` `out/` `arms/` `docs/` `README.md` `attempts/`（他走行）
`tasks/T005/FROZEN_T005.json` および T001〜T004 の `tasks/` `attempts/` はいずれも開いていない。

## 読めなかった箇所

無し。28 件すべてについて全フィールドを解決できた。

このファイルに**存在しない**ことを型集計で確認した（＝欠損ではなく該当無し）:

- `PROJECTED_ZONE_DEFINITION` / `TOLERANCE_ZONE_DEFINITION` → 突出公差域は 1 件も無い。
  したがって `projected_length_mm` は全件 `null`。
- `GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT` / `..._DEFINED_AREA_UNIT` → 単位あたりの長さ・
  領域の形も 1 件も無い。`unit_length_mm` は全件 `null`、`unit_area_shape` は全件 `""`。
- 念のためファイル全文を `[A-Z_]*(TOLERANCE|ZONE|DATUM|MODIFIER)[A-Z_]*` で総なめし、
  上記以外の公差系実体型が無いことも確認した。

## 課題文が決めていないと思った箇所

1. **数値の丸め。** ファイルの値は CAD の mm→inch 逆変換のノイズを含む
   （例: `0.0250000000001`, `0.0100000000000401`）。課題文は丸めを規定していない。
   - `value` は**ファイルの記述をそのまま**（規則1「ファイルに実際に入っているもの」に従った）。
   - `value_mm` は `value × 25.4` を**小数9桁で丸めた**（ノイズは 1e-11 桁なので、
     丸めると 0.635 / 1.27 / 0.254 / 0.3048 のような素の値になる）。
   丸め規約が採点に効くなら、ここは課題文で決めるべき箇所。
2. **公差の並び順。** 実体番号の昇順にした（記入例は昇順でない）。
3. **`unit` に書く単位名。** `CONVERSION_BASED_UNIT` の name をそのまま `"inch"` とした
   （記入例も `"inch"` / `"millimetre"` なので同じ流儀）。
4. **`composite_role` の upper/lower の定義。** 記入例では値の大きい方が upper だが、
   STEP のどちらの属性が upper かは課題文に無い。`relating` 側 = upper と決めた
   （このファイルでは値の大小と一致するので、どちらの規則でも同じ結果になる）。
5. **ファイル全体の `datums` の並び順。** 記入例が A,B,C,... なのでアルファベット昇順にした。

## 課題・記入例の側の欠陥だと思ったもの

1. **記入例の `results` が2件あり、いずれも対象ファイルではない。**
   注記で3回打ち消してはいるが、答案の骨格（`results` が配列）と混ざりやすい。
   対象は1ファイルなので `results` は1件になる。
2. **`asked` の (2)「公差域の形」だけがキー名を持たない。**
   `answer_format_note` に「`zone_form` は意図的に外してある」と書かれているので
   キー名は復元できるが、これは注記に依存している。もし注記が無ければ、腕ごとに
   `zone_form` / `tolerance_zone_form` / `zone_shape` などバラバラのキー名になり、
   「訊けば足りるか」ではなく「キー名を当てられるか」を測ることになっていた。
   （この課題の主眼が「記入例に無くても訊けば埋まるか」である以上、
   注記でキー名を与えている時点で、記入例が見せる情報の一部を注記が肩代わりしている。）
3. **`asked` に無いフィールドが記入例にはある。**
   `label`（日本語名）と `name`（`GEOMETRIC_TOLERANCE.name`）と `composite_role` /
   `composite_partner` は `asked` の5項目のどれにも書かれていない。
   `grade_levels_note` は複合公差を採点しないと言うが、`label` と `name` については
   採点対象かどうかの言及が無い。記入例にあるので埋めた。
4. **`answer_format_note` に「一覧（datums）も省略していない」とあるが、記入例の
   `nist_stc_10...` の datums は A〜J で I が抜けている。** ASME Y14.5 では I, O, Q は
   データム記号に使わないので正しいはずだが、「省略していない」という文言と
   「見た目が飛んでいる」ことが読み手にはぶつかる。本ファイルも A〜H, J, K で I は無い。

## ファイルの内部矛盾

明確な矛盾は見つからなかった。気になった点を2つだけ:

1. **同名の公差が2つある。** `#112` と `#133` がどちらも `GEOMETRIC_TOLERANCE.name = 'Position.1'`
   （値も参照データムも異なる: `#112` は 0.02/データム F/MMR 付き、`#133` は 0.015/データム E,A,B）。
   `SURFACE_PROFILE_TOLERANCE` の側も複合の上下2段が同名（例 `'Position surfacic profile.9'` が
   `#337` と `#338`）だが、こちらは同じ FCF の2段なので同名で正しい。
   `#112` / `#133` は別々の FCF なので、name の重複は元 CAD 側の採番事故に見える。
   実体番号で区別できるので答案には影響しない。
2. `#147` の公差値だけ `0.0100000000000401`（他の平面度は `0.01000000000004`）で、
   同じ 0.01 inch に対して丸め誤差の桁が違う。値としては同一とみなせる。
