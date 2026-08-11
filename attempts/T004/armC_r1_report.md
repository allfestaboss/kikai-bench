# T004 armC_r1 報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（1件のみ）
答案: `attempts/T004/armC_r1.json`（幾何公差 28件 / データム記号 10件）

## どう読み取ったか

自作の ISO 10303-21 パーサ（標準ライブラリのみ、STEP/AP242 専用ライブラリ不使用）を
scratchpad に書いて読んだ。作業ファイルは
`/private/tmp/.../scratchpad/T004_armC_r1/` の `stepparse.py`（Part21 物理ファイルの
字句解析: 文字列リテラル・`''` エスケープ・`/* */` コメント・複合実体 `#N=(A(..) B(..))`・
入れ子集約・型付きパラメータ `LENGTH_MEASURE(...)` を処理）と `extract.py`（意味抽出）。

経路:

- 幾何公差の同定: 実体型名の集合に `*_TOLERANCE`（ISO 10303-47 の geometric_tolerance
  の葉型15種）が含まれる実体を全列挙 → 28件。ファイル自身の
  `#9948=INTEGER_REPRESENTATION_ITEM('number of geometric tolerances',28.)` と一致。
- 公差値: `GEOMETRIC_TOLERANCE` の magnitude → `LENGTH_MEASURE_WITH_UNIT` →
  単位実体。全28件が `#10033=(CONVERSION_BASED_UNIT('inch',#9962) LENGTH_UNIT() NAMED_UNIT(#10031))`。
- mm 換算: `#9962=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960)`、`#9960` は
  `SI_UNIT(.MILLI.,.METRE.)`。つまりファイル内の換算係数 25.4 mm/inch を再帰的に解決して使った
  （25.4 を外から持ち込んでいない）。
- データム: `GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE.datum_system` → `DATUM_SYSTEM`
  の `constituents`（LIST なので並び順＝優先順位）→ `DATUM_REFERENCE_COMPARTMENT.base`
  → `DATUM.identification`。
- 修飾子: `GEOMETRIC_TOLERANCE_WITH_MODIFIERS` の列挙値。
- 公差域の形: `TOLERANCE_ZONE.defining_tolerance` から逆引きして `TOLERANCE_ZONE_FORM.name`。
- データム記号一覧: `DATUM` 実体の identification。

### 判断に迷った箇所

1. **`PERPENDICULARITY_TOLERANCE` の属性数（最も危なかった箇所）**
   `#107=PERPENDICULARITY_TOLERANCE('Perpendicularity.1','',#10003,#993,(#331));` は
   単純実体なのに属性が5個ある。最初は複合実体でないためデータム無しと出力してしまった。
   ISO 10303-47 で angularity / parallelism / perpendicularity / circular_runout /
   total_runout / coaxiality / concentricity / symmetry は
   `geometric_tolerance_with_datum_reference` の直接の下位型なので、第5属性が継承された
   `datum_system` である。これを踏まえて #107→A、#108→A,B と修正した。
   （position / flatness / straightness / roundness / cylindricity / line_profile /
   surface_profile は `geometric_tolerance` の直接下位型なので、データム参照が要るときだけ
   複合実体になる。実際この2型がファイル内で混在している。）

2. **数値の精度**
   ファイル内の値は浮動小数の雑音を含む（例 `0.012000000000048` inch）。
   - `value` は**ファイルの記載どおり**そのまま入れた（規則「ファイルに実際に入っているもの」に従う）。
   - `value_mm` は `value * 25.4` を小数第10位で丸めた（例 0.3048、0.635、0.381、0.254、
     1.27、0.508、1.016）。厳密積との差は最大 5e-12。丸めるか否かは課題文が決めていないので、
     読める数にする側に倒した。厳密積が要るなら `value * 25.4` を再計算すれば得られる。

3. **Q5 のデータム記号を 6 とするか 10 とするか**
   `DATUM` 実体は10個（A,B,C,D,E,F,G,H,J,K。ID属性 `datum.1`〜`datum.10`）。
   うち6個（A,B,C,D,E,F）は `SHAPE_ASPECT_RELATIONSHIP` で `DATUM_FEATURE` に、
   残り4個（G,H,J,K）は `PLACED_DATUM_TARGET_FEATURE` に結び付いている。
   ファイル自身の検証プロパティは `number of datums` = 6、`number of datum targets` = 6 と
   言っており、10 とは合わない。**10 を採った。**理由は、#136〜#139 が実際に H,G,J,K を
   データムとして参照しており、6 に絞ると Q3 の答えと矛盾するため。

4. **空の表し方**
   「該当が無いものは空で報告する」の"空"の型は記入例に従った。文字列欄（`zone_form`,
   `unit_area_shape`, `composite_role`）は `""`、数値欄（`projected_length_mm`,
   `unit_length_mm`, `composite_partner`）は `null`、配列欄（`datums`, `modifiers`）は `[]`。

5. **並び順**（課題文が決めていない）
   `tolerances` は実体番号の昇順、`datums` はアルファベット順（記入例がそう見えるため）にした。

6. **複合公差の上下**（Q6 は採点外だが欄があるので埋めた）
   `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',relating,related)` の relating を
   `upper`、related を `lower` とした。本ファイルでは relating 側が常に大きい値（1.27mm）で
   related 側が小さい値（0.254mm）なので、意味的にも整合する。4組すべてこの向き。

## corpus 配下で開いたファイル

**対象の STEP 1本のみ。**
`NIST-FTC-PMI-Definitions.xlsx` と `NIST-README.txt` は開いていない
（`ls -la` でディレクトリ一覧に名前が出ただけで、中身は読んでいない）。
`corpus/nist/` の他の STEP ファイルも開いていない。
`reference/` `bench/` `checker/` `out/` `README.md` `arms/` `docs/` `attempts/`（他走行）、
過去課題の `tasks/T001-T003` も開いていない。
`tasks/T004/FROZEN_T004.json` は指示上の許可範囲（tasks/T004/）だったので読んだが、
中身はハッシュ一覧のみで答えの漏洩はなかった。

## 読めなかった箇所

なし。10,034 実体すべてパースできた（パースエラー 0）。
答案の全欄をファイルから決定できた。

## 課題文が決めていないと思った箇所

- **`value` の数値精度**（ファイル記載のまま／丸め）。→ 記載のまま。
- **`value_mm` の丸め**。→ 小数第10位で丸め。
- **`tolerances` と `datums` の並び順**。→ 実体番号昇順／アルファベット順。
- **`label`（日本語名）の語彙**。`asked` は日本語名を訊いていないが記入例に欄がある。
  本ファイルに必要なのは直角度・位置度・平面度・面の輪郭度で揺れの少ない語だけだったが、
  同軸度／同心度のように JIS 訳が割れる型が出るファイルでは採点が不安定になりうる。
- **`name` の出所**。記入例は `Feature Control Frame (157)` と `Flatness.1` が混在しており、
  どちらも `GEOMETRIC_TOLERANCE.name` と解釈した（本ファイルでは `Position.21` 等）。
- **複合公差の upper/lower の定義**（採点外だが欄はある）。
- **Q4(1) の「材料状態の修飾子」の範囲**。公差側（`GEOMETRIC_TOLERANCE_WITH_MODIFIERS`）と
  データム側（`DATUM_REFERENCE_COMPARTMENT.modifiers`）の2箇所がありうるが、答案形式には
  データム側の欄がない。本ファイルは全区画が `$`（修飾子なし）なので実害なし。

## 課題・記入例の側の欠陥だと思ったところ

1. **Q4 の (3)(4)(5) は本ファイルでは全件が空になる。**
   `PROJECTED_ZONE_DEFINITION`、`GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT`、
   `GEOMETRIC_TOLERANCE_WITH_DEFINED_AREA_UNIT`、`.RECTANGULAR./.SQUARE./.CIRCULAR.` の
   いずれもファイル内に存在しない（テキスト検索で 0 件）。したがって
   突出公差域の突出長さ・単位あたりの長さ・単位あたりの領域の形は 28件すべて空が正解になる。
   これらの欄は「腕が幻覚を出すか」しか測れず、抽出能力の差は付かない。
   T004 の狙い（訊いていなかったから空欄だったのか、を切り分ける）に対して、
   単一ファイル ftc_06 では Q4 の5項目中3項目が定数（全部空）なので、
   **設問を揃えても分離しないことが構造的に確定している。**
   分離を見たいなら、その3項目が非空になるファイル（記入例に使われている stc_10 / ctc_03 の
   ような）を対象に加えないと測れない。

2. **`zone_form` も 28件中 9件しか非空にならない**（残り19件は `TOLERANCE_ZONE` を持たない）。
   Q4 の5項目のうち実質的に差が付くのは (1) 修飾子（4件が MMR）と (2) 公差域の形（9件）だけ。

3. **記入例に「per unit length」の罠に見える素材がある**（欠陥というより注意点）。
   本ファイルには `REPRESENTATION_ITEM('affected curve length')` を持つ
   `MEASURE_REPRESENTATION_ITEM` が 24 件あり（例 `#106` = 1.250000000005 inch）、
   長さ付きの measure なので「単位あたりの長さ」に見える。実際は
   `#106` → `#9683=REPRESENTATION` → `#9536=PROPERTY_DEFINITION_REPRESENTATION` →
   `#9869=PROPERTY_DEFINITION('pmi validation property','',#76)` で、#76 は
   `PLACED_DATUM_TARGET_FEATURE`。NIST の PMI プレゼンテーション検証プロパティであって
   幾何公差の属性ではない。テキスト近傍検索で答案を作る腕はここで誤答しうる。
   参照解がこれを含めていないことは確認できないので、念のため記録する。

4. **Q5 の「データム記号」の定義が曖昧**（上の判断3）。
   `DATUM` 実体を数えるのか、データム測定対象（datum feature）に紐づくものだけを数えるのかで
   6 と 10 に割れる。しかもファイル自身の検証プロパティが 6 と言っている。
   課題文が「DATUM 実体の identification を全て」と書いていれば割れない。

## ファイルの内部矛盾・気になった点

1. `#9950=INTEGER_REPRESENTATION_ITEM('number of datums',6.)` に対し、`DATUM` 実体は **10個**。
   6 はデータム測定対象由来のもの（A,B,C,D,E,F）だけを数えている。
   一方 `number of geometric tolerances`=28、`number of composite tolerances`=4 は
   実体数と一致する。
2. 公差値に浮動小数の雑音が残っている。とくに **Flatness.1 (`0.01000000000004`) と
   Flatness.3 (`0.0100000000000401`) は図面上は同じ 0.010 in のはずなのに格納値が違う。**
   Flatness.2 は Flatness.1 と同じ値。公差値を厳密一致で照合する採点器だと、
   同じ公差が別値として扱われうる。
3. 28件の公差値すべてに `VALUE_FORMAT_TYPE_QUALIFIER('NR2 1.2')`（小数2桁表示）が
   付いているが、実際の inch 値は3桁公称（0.025, 0.015, 0.012, 0.010, 0.020, 0.040, 0.050）。
   表示書式どおりなら 0.025 → 0.03 になってしまう。出力器の取り違えと思われる。
4. `GEOMETRIC_TOLERANCE.name` は一意でない。`#112` と `#133` はどちらも `'Position.1'`
   だが値もデータムも違う（0.020 in / F と 0.015 in / E,A,B）。
   名前で突き合わせる採点は壊れる。実体番号で突き合わせるべき。
5. `INTEGER_REPRESENTATION_ITEM` の値が実数リテラル（`28.`, `4.`, `6.`）で書かれている。
   Part 21 としては型不一致だが、パースには支障なし。
6. データムの並び順が図面慣習と違う組み合わせがある（例 `#111` = C,A,B、`#133` = E,A,B、
   `#134` = C,A,B）。規則どおり `DATUM_SYSTEM` の区画順をそのまま採用した。

## 制約遵守

- STEP/AP242 専用ライブラリは使用していない（`stepparse.py` を自作、Python 標準ライブラリのみ）。
- 一時ファイルは指定された `scratchpad/T004_armC_r1/` の下だけに置いた。
- 見てはいけないディレクトリ・ファイルは開いていない。
