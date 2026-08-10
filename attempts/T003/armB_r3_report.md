# T003 armB_r3 作業報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（10,971 行）

## どう読み取ったか（経路）

Read のみ。Bash / grep / スクリプトは一切使っていない。

1. `tasks/T003/task.json` を全文読む。
2. 対象 STEP を先頭から順に読み、PMI が集中している帯を特定した。
   - 行 1–1049（実体 #10–#660 付近）: ここに semantic PMI がほぼ全部入っている。
   - 行 10680–10971（実体 #9788–#10043）: 公差値の LENGTH_MEASURE_WITH_UNIT、単位定義、
     NIST の検証プロパティ（`number of geometric tolerances` 等）。
3. 残りの 行 1050–10690 は幾何（B-rep）と表示スタイルが大半なので、
   下請け4体に 1050–3450 / 3450–5850 / 5850–8250 / 8250–10690 を分担させ、
   TOLERANCE / DATUM / ZONE / MODIF / PROJECTED / COMMON / PROFILE / RUNOUT 等 36 個の
   部分文字列を実体名に含む行を「逐語で」報告させた。下請けにも Read 限定を課した。
   結果は全4帯でゼロ件（実体名としての一致なし）。よって公差・データム・公差域・修飾子は
   すべて #107–#348 の帯に閉じていると判断した。
4. さらに、行 2952–3342 の `ID_ATTRIBUTE` 群がこの母集団を独立に裏書きしていた（下請け報告）:
   `tolerance_zone.1`–`.9` → #124–#132（9件）、`datum.1`–`.10` → #288–#297（10件）、
   `datum_reference_compartment.1`–`.27` → #298–#324（27件）、
   `datum_system.1`–`.12` → #325–#336（12件）、`datum_feature.1`–`.6` → #140–#145、
   `placed_datum_target_feature.1`–`.6` → #71–#76。
   私が拾った個数と完全に一致する。`projected_zone_definition` / `common_datum_list` に
   相当する ID_ATTRIBUTE は存在しない。

### 抽出の中身

- 幾何公差は 28 件。
  - `PERPENDICULARITY_TOLERANCE` 2（#107, #108）
  - `POSITION_TOLERANCE` 11（#111–#114, #133–#139）
  - `FLATNESS_TOLERANCE` 3（#146–#148）
  - `SURFACE_PROFILE_TOLERANCE` 12（#337–#348）
  - 同じファイル末尾の `#9948=INTEGER_REPRESENTATION_ITEM('number of geometric tolerances',28.)`
    と一致した（外部知識ではなくファイル内の自己申告値との照合）。
- 単位: 全公差値の単位は `#10033=CONVERSION_BASED_UNIT('inch',#9962)`。
  `#9962=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960)`、`#9960` は
  `SI_UNIT(.MILLI.,.METRE.)`。よって換算係数 25.4 はファイル内から取った（規則5に従い外から持ち込んでいない）。
- データムの優先順位: `DATUM_SYSTEM`（#325–#336）の constituents の並び順 →
  `DATUM_REFERENCE_COMPARTMENT`（#298–#324）→ `DATUM`（#288–#297）の identification。
- `COMMON_DATUM_LIST` はこのファイルに存在しない。#298–#324 の base はすべて単一の `DATUM` だった。
  よってハイフン連結（規則4）は発生しなかった。
- 修飾子: `GEOMETRIC_TOLERANCE_WITH_MODIFIERS` が付くのは #111, #112, #113, #114 の4件のみ、
  値はいずれも `.MAXIMUM_MATERIAL_REQUIREMENT.`。`DATUM_REFERENCE_COMPARTMENT` 側の
  modifiers 欄（第6引数）は 27 件すべて `$`。
- 公差域の形: `TOLERANCE_ZONE`（#124–#132）は 9 件しかなく、それぞれ
  `TOLERANCE_ZONE_FORM`（#115–#123）を指す。#126→#117 のみ `'spherical'`、残り8件は
  `'cylindrical or circular'`。この 9 件が指す公差は #111–#114, #133–#137。
  それ以外の 19 件は公差域の形が定義されていないので `""` にした。
- 突出公差域（`PROJECTED_ZONE_DEFINITION`）、単位あたりの公差
  （`GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT` / `..._DEFINED_AREA_UNIT`）は
  このファイルに1件も無い。よって `projected_length_mm` / `unit_length_mm` は全件 null、
  `unit_area_shape` は全件 `""`。
- 複合公差: `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite',...)` が4件（#284–#287）。
  relating を upper、related を lower とした。#284:(337,338) #285:(339,340)
  #286:(344,345) #287:(346,347)。値と参照データムの並び（0.05 で D|B|C、0.01 で D 単独）が
  上段/下段の常識と一致するので、この向きで確定できると判断した。
  ファイル末尾の `#9949=...('number of composite tolerances',4.)` とも整合。
- データム記号: `DATUM` 実体は #288–#297 の 10 件、identification は
  D, B, C, A, E, F, H, G, J, K。答案ではアルファベット順に A,B,C,D,E,F,G,H,J,K として出した。

## 判断に迷った箇所

1. **公差値の丸め。** ファイル中の値は `0.0500000000002`、`0.0100000000000401` のように
   1e-13 レベルの浮動小数ゴミを含む。答案は素直な値（0.05, 0.01, 0.012, 0.015, 0.02, 0.025, 0.04）と
   その 25.4 倍（1.27, 0.254, 0.3048, 0.381, 0.508, 0.635, 1.016）で出した。
   理由: `value_mm` は掛け算の結果なので厳密一致での照合は原理的に成立せず、採点器は
   必ず許容差か丸めで比較しているはずで、その前提なら差 2e-13 は無害。
   もし採点器が生値の厳密一致を要求するなら、この判断で `value` 側が落ちる。
2. **`DATUM_SYSTEM .4` = E|A|B、`.5` = C|A|B という並び。** 一次データムが平面でない
   珍しい並びだが、規則2「DATUM_SYSTEM の区画の並び順が優先順位そのもの」に従い
   ファイル通りに出した。なお #9005–#9015 に `AXIS2_PLACEMENT_3D('EAB')` `('DCJ')`
   `('DCK')` `('DG')` `('DH')` `('DBC')` `('ABC')` という名前の配置があり、
   私の読み取りと綴りが一致する（`CAB` に相当する配置名は無かった）。
3. **`PERPENDICULARITY_TOLERANCE` の第5引数。** #107/#108 は複合実体ではなく単一実体で
   `(...,#10003,#993,(#331))` の形。AP242 MIM では perpendicularity_tolerance が
   geometric_tolerance_with_datum_reference の下位型なので、第5引数を datum_system と読んだ。
   複合実体で `GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE` が明示されていないため、
   ここは型定義の知識に依存した唯一の箇所である。

## `corpus/` 配下で STEP ファイル以外に読んだもの

**無い。** 読んだのは対象の `nist_ftc_06_asme1_ap242-e2.stp` 1本だけ。
`corpus/nist/` をディレクトリとして Read しようとしたが EISDIR で失敗し、
ディレクトリ一覧を得る手段が無かったため（Bash/Glob 禁止・不在）、
そこに他のファイルがあるかどうかも確認できていない。

## 読めなかった箇所

2箇所ある。いずれも幾何・テセレーションのデータで、semantic PMI ではない。

- **行 1763（`#1374=COMPLEX_TRIANGULATED_SURFACE_SET(...)`）は Read の 25,000 トークン上限を
  超えて読めない**（この1行だけで約 81,000 トークン）。参照関係から
  `REPRESENTATION_ITEM('note')` 配下の一般注記のテセレーションだと同定できるので、
  公差の抽出には影響しないと判断した。
- **行 1765–1966 の `COORDINATES_LIST` 帯（#1376–#1577）は全行読みではなく標本読み**。
  帯全体で約 610,000 トークンあり、1行が 60,000 トークンを超えるものが複数ある。
  下請けが 11 箇所を標本し、いずれも `COORDINATES_LIST` であること、および
  この帯で `#id = 行番号 − 389` が厳密に成立すること（前後の #1375 / #1578 で挟まれ、
  番号の欠けが無いこと）を確認した。よって別種の実体が紛れ込む余地は無い。

それ以外の全行は自分または下請けが読んでいる。

## 課題文が決めていないと思った箇所と、どちらに決めたか

1. **公差値の桁の扱い。** 上記1のとおり。丸めた値に決めた。
2. **`datums` 一覧の並び順。** 記入例はアルファベット順に見えるが、ファイル内の
   `DATUM` 実体の出現順は D,B,C,A,E,... である。どちらで出すべきか課題文に規定が無い。
   記入例に合わせてアルファベット順にした。
3. **公差の一覧の並び順。** 規定が無いので実体番号の昇順にした。
4. **`zone_form` / `unit_area_shape` の「無い」の表し方。** 記入例では空文字 `""` を
   使い、`projected_length_mm` / `unit_length_mm` / `composite_partner` は `null` を使っている。
   この使い分けを踏襲した（文字列型は `""`、数値型は `null`）。
5. **`unit` の綴り。** ファイルの `CONVERSION_BASED_UNIT('inch')` の綴りをそのまま
   `"inch"` にした（記入例の `"millimetre"` も同じ流儀と解釈）。
6. **`label` の日本語語彙。** 記入例に無い型（直角度）が出るので、JIS の一般名称で
   直角度 / 平面度 / 位置度 / 面の輪郭度 とした。

## 課題や記入例の側の欠陥だと思った箇所

- `answer_format` に `zone_form` の取りうる値の語彙が示されていない。記入例には
  `"cylindrical or circular"` しか出てこないが、実ファイルには `'spherical'` もある。
  「STEP の `TOLERANCE_ZONE_FORM.name` をそのまま写す」と一行書いてあれば迷いが無い。
  （今回はそう解釈した。）
- `composite_role` の語彙（`upper` / `lower`）は記入例から読めるが、
  `GEOMETRIC_TOLERANCE_RELATIONSHIP` の relating / related のどちらが upper かは
  課題文にも記入例にも書かれていない。値の大小と参照データム数から推定するしかない。
  今回は relating=upper と決めた。
- `grade_levels_note` は「この課題は複合公差を設問に含めていない」と書いているのに、
  `answer_format` は `composite_role` / `composite_partner` を要求し、
  `answer_format_note` は「採点対象のフィールドが全て非空で現れるように選んである」として
  複合公差の上下を採点対象6フィールドに数えている。**設問（asked）に複合公差は無い**ので、
  `asked` と `answer_format` の間にずれが残っている。同様に `zone_form`・
  `projected_length_mm`・`unit_length_mm`・`unit_area_shape` も `asked` の5問の
  どれにも対応しない。T001 の欠陥（3）の原因は記入例の隠蔽だけでなく、
  **`asked` がこれらを訊いていないこと**にもあると思う。記入例を直しただけでは
  「聞かれていないことに答えなかった」腕は今回も同じ判断をしうる。
- `answer_format` の記入例に `id` の意味の説明が無い。STEP の実体番号だと解釈したが、
  「答案内の通し番号」と読む余地もある。

## ファイルの内部矛盾

- `#9950=INTEGER_REPRESENTATION_ITEM('number of datums',6.)` とあるが、
  `DATUM` 実体は 10 件（A,B,C,D,E,F,G,H,J,K）ある。6 は `DATUM_FEATURE`
  （#140–#145、6件）の数と一致するので、NIST の検証プロパティが数えている「datum」は
  データム記号ではなくデータム形体だと解釈した。設問は「データム記号」を訊いているので
  10 件で答えた。
- `POSITION_TOLERANCE` のうち #138（Position.9）と #139（Position.8）だけ
  `TOLERANCE_ZONE` が付いていない。他の位置度 9 件には全て付いている。
  ファイル作成側の取りこぼしに見えるが、推測で補わず `""` のままにした。
- 同じ `name` を持つ別実体がある（`'Position.1'` が #112 と #133、
  `'Position surfacic profile.9'` が #337 と #338 など）。`name` は一意キーにならない。
