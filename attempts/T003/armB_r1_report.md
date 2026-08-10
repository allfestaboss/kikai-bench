# T003 armB_r1 作業報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（10,971 行）

## どう読み取ったか

Read だけで全行を走査した。Bash / grep / find / スクリプトは一切使っていない。

1. 自分で 1〜1320 行を読んだ。この範囲に semantic PMI がほぼ全部入っていた
   （`#65`〜`#1012` 付近）。
2. 末尾 10,620〜10,971 行を自分で読んだ。公差値の実体（`#9963`〜`#10028` の
   `LENGTH_MEASURE_WITH_UNIT`）と単位（`#10032` `#10033`）はここにある。
3. 残り（1320〜10,620 行）を下請け 8 体に分割して走査させた。各体には Read のみ、
   禁止ディレクトリ非閲覧を明示し、GD&T 系キーワードを含む行だけを逐語で返させた。
   全体が「Read のみを使用」と報告している。

結果、2600〜10,620 行には semantic GD&T 実体は 1 つも無く（幾何・トポロジー・
テセレーション表示・スタイルのみ）、1320〜2605 行は PMI の *presentation* 側
（テセレーション）と `GEOMETRIC_ITEM_SPECIFIC_USAGE` / `COMPOSITE_SHAPE_ASPECT` の
配線だけだった。

## 抽出が完全であることの内部裏取り

推測でなく、ファイル自身が持つ 3 系統の数と突き合わせて確認した。

- `#9948=INTEGER_REPRESENTATION_ITEM('number of geometric tolerances',28.)`
  → 自分が拾った幾何公差もちょうど 28 件（位置度 11・面の輪郭度 12・平面度 3・直角度 2）。
- `#9949=... ('number of composite tolerances',4.)`
  → `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite',...)` は `#284`〜`#287` の 4 件。
- `#9951=... ('number of datum targets',6.)` → `PLACED_DATUM_TARGET_FEATURE` は `#71`〜`#76` の 6 件。
- `ID_ATTRIBUTE` 群（`#2175`〜`#2544`）が `datum.1`〜`datum.10`、`datum_system.1`〜`.12`、
  `datum_reference_compartment.1`〜`.27`、`tolerance_zone.1`〜`.9` と連番で全部に付いており、
  自分が見つけた実体数（DATUM 10 / DATUM_SYSTEM 12 / 区画 27 / TOLERANCE_ZONE 9）と一致した。
  → 見落としたゾーンやデータムは無い。
- `DESCRIPTIVE_REPRESENTATION_ITEM('datum references', ...)` が 28 件あり、
  その内訳（`D,B,C`×5、`D`×4、`A,B,C`×6、`none`×3、`C,A,B`×2、`E,A,B` `F` `A` `A,B`
  `D,H` `D,G` `D,C,J` `D,C,K` 各 1）が、自分が `DATUM_SYSTEM` → `DATUM_REFERENCE_COMPARTMENT`
  → `DATUM` と辿って得た優先順位付きデータム列と 28/28 で完全一致した。
  presentation 側が representation 側の独立な検算になっている。

## 単位換算

外から 25.4 を持ち込んでいない。ファイル内の
`#10033=(CONVERSION_BASED_UNIT('inch',#9962) ...)` →
`#9962=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960)` →
`#9960=SI_UNIT(.MILLI.,.METRE.)` を辿って 1 inch = 25.4 mm を得た。

## 判断に迷った箇所と、どちらに決めたか

1. **公差値の桁**。ファイルの値は `0.0250000000001` のような CATIA 由来の浮動小数ノイズ付き。
   丸めて `0.025` と書くか迷ったが、「ファイルに実際に入っているものを報告する」という
   規則に従い**ファイルの literal をそのまま** `value` に入れ、`value_mm` はそれ×25.4 とした。
   （どちらでも差は 1e-12 以下なので、許容誤差のある採点器なら同値。）
2. **複合公差の上下**。`GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',#337,#338)` の
   第 1 引数（relating）を upper、第 2 引数（related）を lower とした。
   値と DRF の大小（`#337`=0.05/D,B,C, `#338`=0.01/D）が ASME の複合 FCF の上下段と
   整合するので、この向きで確定できる。記入例の上下（1.2/A,B,C が upper、0.2/A が lower）とも同じ向き。
3. **`datums`（ファイルに定義されているデータム記号）の母集団**。
   `DATUM` 実体は 10 個（A,B,C,D,E,F,G,H,J,K）だが、`DATUM_FEATURE` は 6 個しかない。
   設問が「データム記号」なので `DATUM` 実体の identification を全部（10 個）採った。
   下記「内部矛盾」も参照。
4. **`zone_form` が無い公差**。`TOLERANCE_ZONE` は 9 件しか無いので、残り 19 件は
   記入例の真直度と同じく `""`（空文字）にした。

## corpus/ 配下で STEP ファイル以外に読んだもの

**無し。** `corpus/` 配下で開いたのは対象の
`corpus/nist/nist_ftc_06_asme1_ap242-e2.stp` 1 ファイルだけ。README・目録・
ライセンス等は一切開いていない（下請けにも同ファイルだけを指定した）。

## 読めなかった箇所

- `#1374`（1763 行目）と `#1575`（1964 行目）の 2 行。いずれも 1 行が Read の
  出力上限（推定 8 万〜25 万トークン）を超えており、下請けが読み切れなかった。
  位置と参照関係（`#1747` の `TESSELLATED_GEOMETRIC_SET((#1374))` が
  `REPRESENTATION_ITEM('note')` 配下）から、それぞれ `COMPLEX_TRIANGULATED_SURFACE_SET`
  と `COORDINATES_LIST` のテセレーション座標データであり、semantic PMI ではない。
  **答案に影響は無い**（幾何公差 28 件という内部カウンタと一致しているため）。

## 課題文が決めていないと思った箇所

1. **`value` を丸めるか、ファイルの literal のままにするか**が課題文にも記入例にも無い。
   記入例（0.005 / 0.8 / 0.2 / 1.2）は元々きれいな値のファイルから採られているので、
   ノイズ付きの値をどう書くかの手本になっていない。**literal のまま**に決めた。
2. **`datums`（ファイル単位の一覧）の並び順**。課題文は指定していない。
   記入例が A,B,C… のアルファベット順に見えるので、それに合わせた。
   （出現順なら D,B,C,A,E,F,H,G,J,K になる。）
3. **`datums` が `DATUM` 実体を指すのか `DATUM_FEATURE` を指すのか**。
   このファイルは両者の個数が違う（10 対 6）ので、ここで解が割れうる。
   設問の語「データム記号」に従って `DATUM.identification` を採った。
4. **`name` の出所**。記入例の `"Feature Control Frame (157)"` は
   `GEOMETRIC_TOLERANCE` の第 1 引数（name）だと解釈した。本ファイルでは
   `Position.21` `Flatness.1` `Position surfacic profile.9` 等になる。
   ただし記入例の値は「FCF の通し番号」に見えるので、`name` が本当に
   GEOMETRIC_TOLERANCE.name なのか、別の識別子なのかは記入例からは断定できない。
5. **複合公差の `name` が上下で同一**（`Position surfacic profile.9` が `#337` と `#338` の
   両方）。課題文は name の一意性を要求していないので、そのまま重複させた。

## 課題・記入例の側の欠陥だと思ったところ

1. **記入例が inch と mm の 2 ファイルを混ぜているのは良いが、`unit` の綴りが
   `"millimetre"` / `"inch"` と、いずれも `CONVERSION_BASED_UNIT` の name 属性そのままである
   ことが明示されていない。** 本ファイルの `#10033` は `'inch'`（小文字）なので
   そのまま `"inch"` としたが、`"INCH"` や `"inches"` と書く腕が出うる。
2. **記入例に「浮動小数ノイズのある値」が 1 つも無い。** NIST の PMI 検証ファイルは
   ほぼ全部 `0.0250000000001` の形なので、記入例が現実の見た目を代表していない。
   T001 の欠陥（採点対象フィールドが例に出てこない）は直っているが、
   「値をどう書くか」については依然として例が手本になっていない。
3. **`composite_partner` は entity id、`id` も entity id、なのに `name` の括弧内数字
   （`Feature Control Frame (157)` の 157）も id に見える**ので、記入例だけを見ると
   `id: 99` と `(157)` の関係が読めない。混同を誘う。
4. **`unit_area_shape` の値域が示されていない。** 記入例では `"RECTANGULAR"`（大文字）
   だが、`zone_form` は `"cylindrical or circular"`（小文字・STEP の文字列そのまま）。
   同じ「ファイルの文字列をそのまま」なのか、片方は正規化するのかが読み取れない。
   本ファイルでは両方とも該当が無い／空なので実害は出なかった。

## ファイルの内部矛盾に気づいた点

1. **`#9950=INTEGER_REPRESENTATION_ITEM('number of datums',6.)` なのに、
   `DATUM` 実体は 10 個ある**（A,B,C,D,E,F,G,H,J,K）。6 は `DATUM_FEATURE` の個数
   （`#140`〜`#145`）と一致する。G,H,J,K はデータムターゲットで設定されるデータムで、
   `DATUM_FEATURE` を持たないためカウントから漏れている。
   「データムの数」をこのカウンタで検算しようとすると必ず食い違う。
2. **位置度のうち `#138`（Position.9）と `#139`（Position.8）だけ `TOLERANCE_ZONE` が無い。**
   他の 9 件の位置度には全て `TOLERANCE_ZONE` + `TOLERANCE_ZONE_FORM` が付いている
   （`#124`〜`#132`）。同じ図面上の同種の公差で公差域の形が片方だけ欠けているのは、
   出力側の取りこぼしに見える。答案では `zone_form: ""` とした。
3. **`#337`/`#338` のように、複合公差の上下 2 段が同じ name（`Position surfacic profile.9`）を
   共有している。** name だけでは上下を区別できず、`GEOMETRIC_TOLERANCE_RELATIONSHIP` を
   辿らないと分離できない。
4. `#725` の注記に `ASME Y14.5M-1994 APPLIES` とあり、`#9953` の文脈は AP242 ed.2。
   矛盾ではないが、意味論の版とスキーマの版は別物である点は記録しておく。

## 制約違反

**無し。** 使ったツールは Read と Write（答案・本報告の書き出し）と Agent（下請け 8 体）のみ。
Bash / Grep / Glob は 1 度も呼んでいない。一時ファイルは作っていない。
`reference/` `bench/` `checker/` `out/` `arms/` `docs/` `attempts/`（他走行）
`tasks/T001` `tasks/T002` は開いていない。
