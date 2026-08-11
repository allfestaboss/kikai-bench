# T004 armB_r3 作業報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（10,970行）

## どう読み取ったか

Read だけで読んだ。コード実行・シェル・Grep/Glob は一切使っていない。

経路:

1. 先頭 1〜1332行を自分で通読。この AP242 ファイルは semantic PMI が
   低い実体番号側（#10〜#348）にまとまっており、ここに
   幾何公差・TOLERANCE_ZONE・TOLERANCE_ZONE_FORM・DATUM・
   DATUM_REFERENCE_COMPARTMENT・DATUM_SYSTEM・GEOMETRIC_TOLERANCE_RELATIONSHIP
   が全部入っていた。
2. 末尾 10600〜10970行を自分で読み、単位と公差値を取得。
   - `#10033=(CONVERSION_BASED_UNIT('inch',#9962) LENGTH_UNIT() NAMED_UNIT(#10031))`
   - `#9962=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960)`、`#9960` は SI ミリメートル。
     よって換算係数 25.4 は**このファイル内から**採った（外から 1 inch = 25.4 mm を持ち込んでいない）。
   - 公差値は全て `#9963`〜`#10028` の `LENGTH_MEASURE_WITH_UNIT(...,#10033)`＝inch。
3. 残り 1333〜10620行は下請け8体に分割して走査させ、PMI 系の実体型が
   紛れていないかを確認した（結果: 全レンジで該当ゼロ。B-rep 幾何と
   presentation/styling とプレースメントだけ）。

### 裏取り（内部整合の相互検証）

- `#688`〜`#726` の `DESCRIPTIVE_REPRESENTATION_ITEM('datum references', ...)`
  が presentation 側にあり、`'D,B,C'` `'A,B,C'` `'E,A,B'` `'C,A,B'` `'F'`
  `'A'` `'A,B'` `'D,H'` `'D,G'` `'D,C,J'` `'D,C,K'` `'none'` の**28件**。
  これを semantic 側（DATUM_SYSTEM #325〜#336 の区画順）から復元した
  データム列と1件ずつ突き合わせ、**28件すべて一致**した。
  `'none'` 3件は平面度3件に対応。
- `#9948=INTEGER_REPRESENTATION_ITEM('number of geometric tolerances',28.)`。
  自分が拾った幾何公差も 28 件（位置度11・直角度2・平面度3・面の輪郭度12）。一致。
- `#9949=... ('number of composite tolerances',4.)`。
  `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite',...)` も #284〜#287 の4件。一致。
- 下請けが 2500〜3660行で拾った `ID_ATTRIBUTE` の索引が、
  `tolerance_zone.1`〜`.9` → #124〜#132、`datum.1`〜`.10` → #288〜#297、
  `datum_system.1`〜`.12` → #325〜#336、`datum_reference_compartment.1`〜`.27` → #298〜#324
  を列挙していた。**個数が自分の読みと完全一致**しており、
  TOLERANCE_ZONE は9個しか存在しないこと、DATUM は10個しか存在しないことが独立に裏付けられた。

### 判断に迷った箇所

- **公差値の桁**。ファイルの数値リテラルが `0.0500000000002` のように
  浮動小数ノイズを含む。記入例は `0.005 / 0.127` のように綺麗な値だった。
  「ファイルに実際に入っているもの」を報告せよという規則に従い、
  `value` はリテラルをそのまま、`value_mm` はリテラル×25.4 の
  full precision（例: `1.27000000000508`）とした。丸めていない。
- **突出長さ・単位あたり長さ・単位あたり領域の形**が全件空になった件。
  PROJECTED_ZONE_DEFINITION / TOLERANCE_ZONE_DEFINITION /
  GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT / _DEFINED_AREA_UNIT は
  ファイル中に1件も存在しない。9個の TOLERANCE_ZONE は全て素の
  `TOLERANCE_ZONE(...)` である。**未記入ではなく本当に空**である。
  紛らわしい近縁として `#2936=DERIVED_UNIT((#2930))`（`NAME_ATTRIBUTE('square inch',#2936)`）と
  `MEASURE_REPRESENTATION_ITEM('affected area',AREA_MEASURE(...),#2936)` が64件あるが、
  これはデータムターゲット等の「影響面積」であって単位あたり公差ではない。
- **公差域の形が9件だけ埋まる**件。TOLERANCE_ZONE が9個しかないため、
  #138(Position.9) / #139(Position.8) を含む19件は `zone_form` が空になる。
  位置度なのに公差域の形が無いのは一見不自然だが、ファイルがそう書いてある。

## corpus/ 配下で対象 STEP 以外に開いたもの

**なし。** `NIST-FTC-PMI-Definitions.xlsx` と `NIST-README.txt` は開いていない。
`tasks/T004/FROZEN_T004.json` も開いていない。
`reference/` `bench/` `checker/` `out/` `arms/` `docs/` `attempts/`（他走行）
`README.md`、および T001/T002/T003 の `tasks/` `attempts/` も開いていない。
下請け8体にも同じ禁止リストを明文で渡し、対象 STEP 1ファイルのみを読ませた。

## 下請けと待ち

- 8体（それぞれ 1333-2500 / 2500-3660 / 3660-4820 / 4820-5980 / 5980-7140 /
  7140-8300 / 8300-9460 / 9460-10620 行を担当）。
- 全体を並列で投げ、待ちは最短 21秒・最長 65秒程度。打ち切りは発生していない。
- 8体とも「該当ゼロ」を返し、担当レンジの先頭/末尾の実体番号を申告したので
  1333〜10620行の連続被覆が確認できた。

## 読めなかった箇所

**1763〜1965行のうち約197行（実体 #1374〜#1576 相当）が逐語では読めなかった。**
理由は Read の1回あたりトークン上限で、この帯は1行が極端に長い。
担当した下請けの実測で、1763行**単独で約81,000トークン**、
1960行付近の7行窓が**約262,000トークン**あり、
offset/limit をどう刻んでも返せない。

ただしこの帯は PMI ではないと判断してよい根拠がある:

- 直前の #1373 は `COMPLEX_TRIANGULATED_SURFACE_SET`、直後の #1578 は `TESSELLATED_CURVE_SET`。
- 帯の内部を7点（1800, 1801, 1850, 1900, 1901, 1935, 1966行）抜き取ったところ
  **全て `COORDINATES_LIST`**（ラベルは `'position'` `'linear dimension'` 等の小文字文字列）。
- この区間は実体番号が1行1実体で連番かつ欠番なしであることが確認できている。

すなわち三角形分割された注記の**座標データ**の塊であり、
公差やデータムの実体が紛れる余地は実質ない。
とはいえ「実際に目で見た」わけではないので、ここだけは
他の10,773行と同じ確度では断言できない。**唯一の未読部分である。**

これ以外は、ヘッダから `END-ISO-10303-21;` まで自分の直読と下請けの分担で
全行が誰かの目を通っている。

## 課題文が決めていないと思った箇所

1. **公差値の丸め方**。上記のとおり丸めなしを選んだ。
2. **ファイル単位の `datums` の並び順**。課題文は指定していない。
   記入例がアルファベット順に見えたのでアルファベット順（A,B,C,D,E,F,G,H,J,K）にした。
   ファイル出現順なら D,B,C,A,E,F,H,G,J,K になる。
3. **「データム記号」の定義**。DATUM 実体の識別子（10個）か、
   DATUM_FEATURE（6個）かが決まっていない。DATUM 実体の識別子を採った。
   記入例の2ファイルもその読みと矛盾しない。
4. **`unit` に何を書くか**。CONVERSION_BASED_UNIT の名前をそのまま
   （`'inch'`）とした。記入例と一致する。
5. **同名公差の扱い**。`Position.1` という name の公差が #112 と #133 の2件ある
   （値もデータムも違う別物）。実体番号で区別されるので統合していない。

## 課題や記入例の側の欠陥だと思ったもの

1. **`answer_format` に、`asked` が訊いていないフィールドがまだ残っている。**
   T004 は「訊いていないものを採点しない」ために Q4 を追加した趣旨だが、
   `label`（和名）・`name`（実体の name 属性）・`composite_role`・`composite_partner`
   の4フィールドは `asked` のどの設問でも訊かれていない。
   `composite_role`/`composite_partner` は `grade_levels_note` で
   明示的に採点対象外と書かれているので既知だが、
   **`label` と `name` については「採点対象外」という断りが無い**。
   `asked`(1) は「実体番号・種別・公差値・単位」としか言っておらず、
   name も label も含まれない。T001〜T003 で問題になったのと同じ構造
   （記入例が要求するが設問が訊いていない）が2フィールド残っている。
2. **`answer_format_note` の「採点対象のフィールドが全て非空で現れるように選んである」
   が、対象ファイルの実態と乖離している。** 記入例では
   `zone_form` / `projected_length_mm` / `unit_length_mm` / `unit_area_shape`
   が非空の行が並ぶが、実際の T004 対象ファイルでは
   `projected_length_mm` と `unit_length_mm` と `unit_area_shape` は
   **28件すべて空**であり、`zone_form` も 28件中9件しか埋まらない。
   Q4 は5項目を名指しで訊くようになったが、そのうち3項目は
   このファイルでは「全件空」しか正解が無く、腕を分離しない。
   （空を正しく空と報告できるかの検査にはなるが、記入例の見た目が
   「埋まるはず」と示唆してしまうので、埋めたがる腕を誘発する形になっている。）
3. **記入例に `STRAIGHTNESS_TOLERANCE` の `unit_length_mm: 15.0` があるが、
   対応する STEP 表現（GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT）が
   どの実体から来るのかは課題文のどこにも書かれていない。**
   `rules` は種別・データム順・共通データム・単位換算の4点しか規定しておらず、
   Q4 の(3)(4)(5)をどの実体から取るかは腕の STEP 知識に委ねられている。
   `zone_form` だけは「TOLERANCE_ZONE_FORM の名前をそのまま」と実体名が
   示されているので、(3)(4)(5)にも同じ配慮があってよいはず。
4. `rules` の「共通データム（COMMON_DATUM_LIST）は 'A-B' のように連結」は、
   この対象ファイルには COMMON_DATUM_LIST が1件も無いので発火しない規則である
   （欠陥ではないが、T004 では死んだ規則）。

## ファイルの内部矛盾

1. **`#9950=INTEGER_REPRESENTATION_ITEM('number of datums',6.)` と、
   ファイルに実在する DATUM 実体10個（A,B,C,D,E,F,G,H,J,K）が食い違う。**
   6 は DATUM_FEATURE（#140〜#145）の個数と一致するので、
   NIST の validation property が「datum」と呼んでいるものは
   DATUM_FEATURE であり、DATUM 実体ではない。
   Q5 を「validation property を読む」で解こうとすると 6 になり、
   DATUM 実体を数えると 10 になる。**同じファイル内で「データムの数」が
   2通りに読める。** 自分は DATUM 実体の識別子を採った。
2. 位置度 #138(Position.9)・#139(Position.8) に TOLERANCE_ZONE が付いていない。
   同種の位置度9件には付いているので、エクスポートの取りこぼしの可能性がある。
   ただし推測せず、ファイルどおり空で報告した。
3. `#9952=('number of semantic pmi elements',67.)` に対し
   `#9944=('number of annotations',67.)` が一致しており、
   semantic と presentation が1対1で対応する作りになっている。
   これ自体は矛盾ではないが、28公差＋14寸法＋10位置寸法＋6データム＋
   6データムターゲット＋注記 の内訳が 67 になるかの検算は行っていない。
