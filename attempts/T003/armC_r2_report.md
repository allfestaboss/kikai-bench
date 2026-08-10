# T003 / armC_r2 報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（1件）
答案: `attempts/T003/armC_r2.json`（28公差 / データム記号10種）

## どう読み取ったか

STEP 専用ライブラリは使わず、Python 標準ライブラリだけで自作パーサを書いた（作業ディレクトリ:
`/private/tmp/.../scratchpad/T003_armC_r2/parse.py`, `build.py`）。

1. DATA セクションを文字単位でスキャンし、文字列リテラル（`'...'`、`''` エスケープ）と
   括弧の深さを見ながら深さ0の `;` で実体を切り出した。`#N = 本体` を 10034 件取得。
2. 複合実体 `#N=( A(...) B(...) )` は「深さ1に並ぶ `NAME(...)` の列」として分解し、
   葉の型（POSITION_TOLERANCE 等）と GEOMETRIC_TOLERANCE 部分を別々に引けるようにした。
3. 幾何公差 = 葉の型が15種の公差実体のいずれか、で列挙 → 28件
   （POSITION 11 / SURFACE_PROFILE 12 / FLATNESS 3 / PERPENDICULARITY 2）。
4. 公差値は `GEOMETRIC_TOLERANCE` の第3引数 → `LENGTH_MEASURE_WITH_UNIT`。
   単位は全件 `#10033 = CONVERSION_BASED_UNIT('inch', #9962)`、
   `#9962 = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4), #9960)`、
   `#9960 = SI_UNIT(.MILLI.,.METRE.)`。
   よって換算係数 25.4 は**このファイル内から**取った（外部から 1 inch = 25.4 mm を持ち込んでいない）。
5. データムは `DATUM_SYSTEM` → `DATUM_REFERENCE_COMPARTMENT`（区画の並び順そのまま）→ `DATUM`
   の第5引数（識別文字）。`COMMON_DATUM_LIST` はこのファイルには1件も無い（grep で0件）。
6. 公差域の形は `TOLERANCE_ZONE`（9件）の defining_tolerance から公差実体へ逆引きし、
   `TOLERANCE_ZONE_FORM` の名前をそのまま入れた。
7. 複合公差は `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',上,下)` 4組。
   relating 側を upper、related 側を lower とした（値も上段0.05 > 下段0.01 で整合）。

### 判断に迷った箇所

- **単純実体形の継承属性。** 最初 `PERPENDICULARITY_TOLERANCE('...','',#10003,#993,(#331))` の
  第5引数を見落とし、#107/#108 のデータムを空で出しかけた。
  `perpendicularity_tolerance` は `geometric_tolerance_with_datum_reference` の subtype なので、
  複合実体でない書き方では継承属性 `datum_system` が第5引数として並ぶ。修正済み。
  `FLATNESS_TOLERANCE` は4引数（データム参照を持たない subtype）で整合。
- **公差値の桁。** ファイルの実値は `0.012000000000048` `0.0250000000001` `0.0100000000000401` の
  ように CAD 由来の浮動小数ノイズが乗っている。記入例は `0.005` のような公称値で書かれていた。
  **公称値側に倒して小数9桁で丸めた**（0.012 / 0.025 / 0.01）。ずれは 1e-12 以下で、
  生値でも丸め値でもどんな許容比較でも同じ判定になるはずだが、決めたのはこちらである旨を記す。
  `value_mm` は「丸めた value × 25.4」ではなく「生値 × 25.4 を9桁丸め」で、結果は同じ。
- **`value` に入れるのは inch 値。** 記入例の1件目は `unit: millimetre` で value と value_mm が同値、
  2件目は `unit: inch` で value=0.005 / value_mm=0.127。よって `value` はファイル記載の生の数値、
  `unit` はその単位名（ここでは CONVERSION_BASED_UNIT の名前 `inch`）と解釈した。
- **データム一覧の並び。** 記入例が A,B,C,... の辞書順だったので辞書順にした
  （ファイル内の `DATUM` 実体の出現順は D,B,C,A,E,F,H,G,J,K）。
- **公差の並び順。** 指定が無いので実体番号の昇順にした。

## 読めなかった箇所

なし。28件すべて種別・値・単位・データム・修飾子を確定できた。
以下は「読めなかった」ではなく「このファイルに存在しない」ことを確認したもの
（いずれも grep で出現0件）:
`PROJECTED`（突出公差域）/ `GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT`（単位あたりの長さ）/
`GEOMETRIC_TOLERANCE_WITH_DEFINED_AREA_UNIT`（単位あたりの形）/ `COMMON_DATUM_LIST` /
`UNEQUALLY_DISPOSED` / `FREE_STATE` / `TANGENT_PLANE` / `STATISTICAL` / `LEAST_MATERIAL`。
したがって `projected_length_mm` / `unit_length_mm` は全件 null、`unit_area_shape` は全件 空文字。
記入例で新たに示された6フィールドのうち、このファイルで実際に非空になるのは
**修飾子（4件）・公差域の形（9件）・複合公差の上下（8件=4組）**の3種だけである。

## 課題文が決めていないと思った箇所

1. **公差値の丸め方**（上記）。生値をそのまま出すのか公称値に丸めるのかが規則にない。公称値に倒した。
2. **`unit` に入れる文字列**。`CONVERSION_BASED_UNIT` の name（`'inch'`）をそのまま使うのか、
   正規化した表記にするのかが不明。ファイル記載の `inch` をそのまま使った
   （なお同ファイルの `'MILLIMETRE'` は大文字だが記入例は `millimetre` と小文字なので、
   例の側は既に何らかの正規化をしている可能性がある。今回は inch なので影響なし）。
3. **`datums` に datum target を含めるか**。このファイルには
   `PLACED_DATUM_TARGET_FEATURE` が6件あり、`DATUM` の文字と index を組むと
   NIST の意図では G1/H1/J1/J2/K1/K2 という記号になる。
   設問は「データム記号」だが記入例は素の文字だけなので、**`DATUM` 実体の識別文字10種のみ**とした。
4. **公差の並び順**（実体番号昇順にした）。
5. **`composite_role` の upper/lower の決め方**。
   `GEOMETRIC_TOLERANCE_RELATIONSHIP` の relating/related のどちらが上段かは規則に書かれていない。
   値の大小（上段が大）で裏が取れたので relating=upper とした。

## 課題・記入例の側の欠陥だと思うもの

1. **`corpus/nist/NIST-FTC-PMI-Definitions.xlsx` が参照解の一部を含んでいる。**
   閲覧許可されている `corpus/` の中にあり、FTC-06 の行に
   `⌖ | S⌀ .025 | D | B | C`、`⌖ | ⌀.025Ⓜ | A | B | C`、`⌖ | ⌀.015 | C | A | B`、
   `⌖ | ⌀.02Ⓜ | F` などが**種別・値・修飾子・データム順まで平文で**書かれている。
   自分はパーサで独立に読んだあと、この表を突き合わせ検証に使った（申告）。
   STEP を読まずにこの xlsx と NIST-README だけで相当部分の答案が組める。
   ベンチの意図（規格から自力で読めるか）を壊しうるので、対象ファイルに対応する行は
   corpus から外すか、閲覧禁止側へ移すべきだと思う。
2. **記入例が「非空で全フィールドを見せる」ために2ファイルを混ぜた結果、`unit` の表記ゆれが露出している。**
   1件目 `millimetre`、2件目 `inch`。ファイル内の実体名は `MILLIMETRE` / `inch` なので、
   `millimetre` は正規化済み、`inch` は生。どちらの規則に従えばよいか例からは決まらない。
3. **`asked` に無いものが `answer_format` にある。**
   `asked` の5問は「種別・値・単位／mm 換算／データム順／材料状態修飾子／データム記号一覧」で、
   `zone_form`・`projected_length_mm`・`unit_length_mm`・`unit_area_shape`・
   `composite_role`・`composite_partner`・`label`・`name` は**設問文のどこにも要求されていない**。
   T003 の note は「記入例に出さなかったから落ちた」と診断しているが、
   実際には**課題文（asked）が今もこれらを訊いていない**。
   記入例を直しても `asked` と `answer_format` の不一致は残っている。
   （メモリにある「ベンチの盲点は課題文にある」がそのまま当てはまる。）
4. **`grade_levels_note` が「複合公差を設問に含めていない」と明記しているのに、
   記入例は複合公差の上下1組を非空で提示している。**
   採点しないのなら例に出す必要が無く、出すなら Q6 相当が採点されるように読める。規則と例の食い違い。
5. **`answer_format` の `file` がフルパスでなくベース名。** `files[].path` は
   `corpus/nist/...` 形式なので、答案側でどちらを書くのか厳密には決まらない。例に合わせてベース名にした。

## ファイルの内部矛盾

- **NIST の設計意図（xlsx）と STEP の中身が一致しない箇所がある。**
  ATC80 は `(⌀1.000) ⌖ | ⌀.025 | D | B | C` ×2 と `(1.106) ⌖ | .025 | A | B | C` ×2 を想定しているが、
  実ファイルの該当4件は `#136` 0.015 | D,H、`#137` 0.015 | D,G、`#138` 0.025 | D,C,J、`#139` 0.025 | D,C,K。
  値もデータムも合わない。規則どおり**ファイルの中身**を報告した。
  同様に ATC84（一般注記の輪郭度）は `.06` 想定だが実体 `#348` は 0.05。
- `#138` `#139` だけ `TOLERANCE_ZONE` が付いておらず公差域の形が無い。
  他の位置度9件には付いているので、CAD 出力側の取りこぼしに見える。
  規則どおり空のままにした。
- `TOLERANCE_ZONE` は9件すべて `TOLERANCE_ZONE_FORM` を持つが、うち8件が同じ文字列
  `'cylindrical or circular'`、1件（`#117`, 球位置度 `#135`）が `'spherical'`。
- ファイルのグローバル単位系（`GLOBAL_UNIT_ASSIGNED_CONTEXT`）は **MILLIMETRE** だが、
  PMI の公差値は全件 **inch** 単位の測度を参照している。
  課題文の「ファイルの単位系は inch」は PMI 側の話としては正しいが、
  形状幾何側は mm なので「ファイルの単位系」という言い方は曖昧である。

## 制約について（申告）

- STEP/AP242 専用ライブラリは使っていない（`re` / `json` / `pickle` / `zipfile` / `xml.etree` のみ）。
- 禁止ディレクトリ（`reference/` `bench/` `checker/` `out/` `README.md` `arms/` `docs/`、
  他走行の `attempts/`、T001/T002 の `tasks/`）は開いていない。
- ただし `ls -la attempts/T003/` を実行し、同ディレクトリに `armC_r3.json` が存在するという
  **ファイル名だけ**が目に入った。中身は開いていない。
- 記入例の2ファイルのうち `corpus/nist/nist_ctc_03_asme1_ap242-e2.stp` の `#37` 周辺と
  `corpus/nist/NIST-FTC-PMI-Definitions.xlsx`、`corpus/nist/NIST-README.txt` を読んだ。
  いずれも閲覧許可された `corpus/` 配下。前者は `id` / `name` / `unit_length_mm` /
  `unit_area_shape` がどの属性を指すのかの意味確認、後者は突き合わせ検証に使った。
- 一時ファイルは指定された `scratchpad/T003_armC_r2/` の下だけに置いた。
