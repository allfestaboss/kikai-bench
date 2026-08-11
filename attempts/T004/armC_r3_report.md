# T004 / armC_r3 報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（1 ファイルのみ）
答案: `attempts/T004/armC_r3.json`（JSON 構文検証済み、公差 28 件）

## どう読み取ったか

STEP 専用ライブラリは使っていない。Python 標準ライブラリだけで自前パーサを書いた。

1. `DATA;` 〜 最後の `ENDSEC;` を切り出し、`#N = ... ;` を、文字列リテラル（`''` エスケープ含む）と
   括弧の深さを見ながら走査してインスタンス表に分解（10,034 実体）。
2. 実体名を集計して型一覧を作り、公差・データム関係の型だけを抜いた。
3. 幾何公差の抽出:
   - 複合実体（`( GEOMETRIC_TOLERANCE(...) ... POSITION_TOLERANCE() )` 等）は
     部分実体ごとに分解し、葉の型（POSITION / SURFACE_PROFILE）を `kind` にした。
   - 単純実体 `FLATNESS_TOLERANCE`（4 引数）と `PERPENDICULARITY_TOLERANCE`（5 引数）は
     引数個数で判別。**判断が要ったのはここ。** `PERPENDICULARITY_TOLERANCE` は
     `GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE` の subtype なので第5引数が datum_system 集合、
     `FLATNESS_TOLERANCE` は `GEOMETRIC_TOLERANCE` 直下なので4引数、と読んだ（スキーマ知識に依拠）。
4. 公差値: `magnitude` → `LENGTH_MEASURE_WITH_UNIT` → `#10033 =
   (CONVERSION_BASED_UNIT('inch',#9962) LENGTH_UNIT() NAMED_UNIT(#10031))`、
   `#9962 = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960)`、`#9960` は SI `.MILLI. .METRE.`。
   よって換算係数 25.4 は**同ファイル内から取得**した（外から 1 inch = 25.4 mm を持ち込んでいない）。
   28 件すべて `#10033`(inch)。
5. データム: `DATUM_SYSTEM` の第5引数の並び順 →
   `DATUM_REFERENCE_COMPARTMENT` → `DATUM` の第5引数（identification）を並び順のまま採用。
6. 公差域の形: `TOLERANCE_ZONE(name,desc,of_shape,prod_def,defining_tolerance,form)` の
   `form` → `TOLERANCE_ZONE_FORM` の文字列をそのまま。9 件だけ存在。
7. 複合公差: `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',relating,related)` の
   relating を upper、related を lower とした（値が上段 0.05 / 下段 0.01 で整合）。採点対象外の由。

## corpus 配下で開いたファイル

**対象 STEP 1 本以外は一切開いていない。**
`NIST-FTC-PMI-Definitions.xlsx` と `NIST-README.txt` は開いていない（`ls` もしていない）。
`reference/` `bench/` `checker/` `out/` `README.md` `arms/` `docs/` `attempts/` の他走行、
および `tasks/T001` `T002` `T003` も開いていない。

## 読めなかった箇所

なし。28 件すべてについて全フィールドを決定できた。

## 課題文が決めていないと思った箇所（こちらでこう決めた）

1. **公差値の丸め。** ファイル内の値は浮動小数のノイズを持つ
   （`0.0250000000001`, `0.01000000000004`, `0.0100000000000401`, `0.0500000000002` 等）。
   規則は「ファイルに実際に入っているもの」だが、リテラルをそのまま出すか公称値に丸めるかは
   決まっていない。**小数第9位で丸めた**（`value: 0.025`, `value_mm: 0.635`）。
   リテラルとの差は最大 1e-10 なので、数値許容つき採点ならどちらでも通るはず。
   厳密一致採点だと、参照解がリテラル側なら落ちる。
2. **`file` フィールドの書式。** 記入例に倣ってベース名 `nist_ftc_06_asme1_ap242-e2.stp` にした
   （`corpus/nist/...` のパスではない）。
3. **`tolerances` 配列の並び順。** 指定がないので実体番号の昇順にした。
4. **同一 `TOLERANCE_ZONE_FORM` が複数ある公差の扱い。** 本ファイルでは 1:1 なので発生せず。

## 課題・記入例の側の欠陥だと思った箇所

1. **`asked` がまだ `answer_format` の全フィールドを覆っていない。**
   T004 は「設問を採点対象に揃えた」とあるが、`name`（公差の名前文字列, 例 `Position.21`）と
   `label`（日本語名, 例「位置度」）は `asked` のどこでも訊かれていない。
   Q1 が訊くのは「実体番号・種別・公差値・単位」の4つだけで、`name`/`label` は含まれない。
   T001〜T003 で指摘された「訊いていないものを採点する」構造が、この2フィールドについては残っている。
   `label` に至っては STEP から読み取るものですらなく、種別名の和訳という別の知識である。
2. **記入例の非空フィールドが本課題ファイルに存在しない種類のもの。**
   `answer_format_note` は「採点対象のフィールドが全て非空で現れるように選んである」と書くが、
   その結果、本ファイルには 1 件も無い `projected_length_mm`（3.2）、`unit_length_mm`（15.0, 6.35）、
   `unit_area_shape`（"RECTANGULAR"）が例には出ている。
   例を見た腕が「探すべき値がある」と誤誘導される余地がある（＝T004 の答案は Q4 の 5 項目のうち
   3 項目が全件 null/空になる）。逆に言えば Q4 は本ファイルでは (1) 修飾子と (2) 公差域の形しか分離しない。
3. **記入例の `datums` が実ファイルの実物だと明記されている**ため、
   例の 2 ファイル（stc_10 / ctc_03）についてはデータム一覧が完全に配られている。
   本課題の対象ファイルではないので直接の漏洩ではないが、同系ファイルの命名規則（A..J 連番、I を飛ばす）は
   例から推測できてしまう。実際、本ファイルも A,B,C,D,E,F,G,H,J,K と I を飛ばしている。

## ファイルの内部矛盾・気になった点

1. **幾何コンテキストの単位は mm、PMI の公差値の単位は inch。**
   `#9953` の `GLOBAL_UNIT_ASSIGNED_CONTEXT((#10032,#9958,#9955))` の `#10032` は
   `CONVERSION_BASED_UNIT('MILLIMETRE',#9961)`（係数 1.0 → SI mm）である。
   一方、28 件の公差 magnitude はすべて `#10033 = CONVERSION_BASED_UNIT('inch',...)` を指す。
   課題文の「ファイルの単位系は inch」は PMI 側についてのみ正しい。
2. **`Position.1` という名前が 2 つある。** `#112`（0.02 in, データム F, MMC）と
   `#133`（0.015 in, データム E,A,B, 修飾子なし）。別の公差なのに name が衝突している。
   `name` を同定キーにする採点器があると壊れる。
3. **データム系の並びが辞書順でないものがある。**
   `#329 = DATUM_SYSTEM('Datum System .5',...,(#308,#309,#310))` は C, A, B の順、
   `#328` は E, A, B の順。規則どおり「区画の並び順＝優先順位」としてそのまま報告した。
4. **`POSITION_TOLERANCE` なのに `TOLERANCE_ZONE` を持たないものが 2 件**（`#138 Position.9`,
   `#139 Position.8`）。他の 9 件の位置度には zone があるので、作成側の抜けに見える。
   `zone_form` は空で報告した。
5. `DATUM` は 10 個（A〜H, J, K）あるが `DATUM_FEATURE` は 6 個しかない。
   残りは `PLACED_DATUM_TARGET_FEATURE`（6 個、識別子は '1'/'2' の datum target index）経由。
   Q5 は「データム記号」なので `DATUM.identification` の 10 個を報告した
   （datum target の '1'/'2' は記号ではないと判断）。

## 制約違反

なし。STEP/AP242 専用ライブラリは不使用（Python 標準ライブラリ + 自作パーサ + grep のみ）。
一時ファイルはすべて
`/private/tmp/claude-501/-Users-boss-dev-01-projects/826e8fde-631a-4aed-a5c1-124ba794daae/scratchpad/T004_armC_r3/`
配下（`parse.py` `ents.json` `types.py` `alltypes.txt` `tol.py` `look.py` `dump.py` `extract.py` `build.py`）。
