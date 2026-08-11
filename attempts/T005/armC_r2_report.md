# T005 armC_r2 報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（`task.json` の `files` に挙がった1件のみ）

## どう読み取ったか

STEP / AP242 専用ライブラリは使っていない。Python 標準ライブラリ（`re`, `json`）だけで
自前のパーサを書いた。作業ファイルは
`/private/tmp/claude-501/.../scratchpad/T005_armC_r2/`（`parse.py` / `dump.py` / `dump2.py` / `build.py`）。

1. `DATA;` 〜 最後の `ENDSEC;` を取り出し、文字列リテラル（`''` エスケープ込み）と
   `/* */` コメントを考慮して `;` で実体に分割。`#N = ...` を辞書化（10,034 実体）。
2. 単純実体 `TYPE(...)` と複合実体 `( TYPE(...) TYPE(...) )` の両方を展開。複合は 165 件。
3. 幾何公差は「葉の型」で拾った。
   - 複合実体: `GEOMETRIC_TOLERANCE` + `GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE`
     (+ `GEOMETRIC_TOLERANCE_WITH_MODIFIERS`) + `POSITION_TOLERANCE` / `SURFACE_PROFILE_TOLERANCE`
   - 単純実体: `FLATNESS_TOLERANCE`（4 引数）、`PERPENDICULARITY_TOLERANCE`（5 引数）
   - `PERPENDICULARITY_TOLERANCE` は Part 47 で `geometric_tolerance_with_datum_reference` の
     サブタイプなので、単純実体でも第5引数が `datum_system` のリストになる。ここをそう解釈した。
4. 公差値は第3引数 `#N = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(x), #10033)`。
   `#10033 = CONVERSION_BASED_UNIT('inch', #9962)`、`#9962 = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4), #9960)`、
   `#9960 = SI_UNIT(.MILLI., .METRE.)`。この 25.4 を**ファイル内から**取り出して換算した
   （25.4 を外から持ち込んでいない。SI 接頭辞 `.MILLI.` も一般化して処理している）。
   28 件すべての magnitude が `#10033`（inch）を指す。
5. データムは `DATUM_SYSTEM.constituents` の並び順 →
   `DATUM_REFERENCE_COMPARTMENT.base` → `DATUM.identification`。
6. 公差域の形は `TOLERANCE_ZONE(..., (公差の集合), #form)` → `TOLERANCE_ZONE_FORM.name` を
   **そのままの文字列**で入れた（`cylindrical or circular` / `spherical`）。
7. 複合公差は `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',relating,related)` の
   relating を `upper`、related を `lower` とした（記入例 #486/#487 の対応と、
   値の大小（上段 0.05 / 下段 0.01 inch）が一致する）。

### grep による独立クロスチェック
パーサのバグ避けに `grep` でも数えた。一致した。
`POSITION_TOLERANCE()` 11、`SURFACE_PROFILE_TOLERANCE()` 12、`FLATNESS_TOLERANCE` 3、
`PERPENDICULARITY_TOLERANCE` 2 → 計 28。`GEOMETRIC_TOLERANCE` 23（複合分）+ 5（単純分）= 28。
`.MAXIMUM_MATERIAL_REQUIREMENT.` は 4 個だけ。`TOLERANCE_ZONE` / `TOLERANCE_ZONE_FORM` は各 9。
`DATUM('...')` は A,B,C,D,E,F,G,H,J,K の 10 個ちょうど（`I` は欠番）。

### 判断に迷った箇所
- **浮動小数の桁**。ファイルの値は `0.0250000000001` `0.01000000000004` `0.0100000000000401`
  のようにノイズが乗っている（mm 原図を inch で書き出した往復誤差と見られる）。
  規則「ファイルに実際に入っている」に従い、**丸めずに生の値**を `value` に入れ、
  `value_mm` も `生値 × 25.4` の全桁を入れた。丸め済みの意図値は
  0.01 / 0.012 / 0.015 / 0.02 / 0.025 / 0.04 / 0.05 inch
  （= 0.254 / 0.3048 / 0.381 / 0.508 / 0.635 / 1.016 / 1.27 mm）である。
  参照解が丸め済みでも、1e-13 桁の差なので許容比較なら一致するはず。
- **`unit` の表記**。`CONVERSION_BASED_UNIT` の name をそのまま `"inch"`（小文字）にした。
- `label` は日本語の一般名（位置度／平面度／面の輪郭度／直角度）。記入例に無い
  `PERPENDICULARITY_TOLERANCE` は「直角度」とした。

## 答案様式に無いが設問で訊かれているフィールド

**あった。`zone_form` である。**`answer_format` の記入例には `zone_form` キーが存在しないが、
`asked` の (2) が「公差域の形（TOLERANCE_ZONE_FORM の名前をそのまま）」を明示的に訊いている。
`answer_format_note` も「設問が訊いているので、答案には入れること」と書いている。
そこで **`zone_form` というキー名で、`modifiers` と `projected_length_mm` の間に**追加した。
該当が無いものは `""`（空文字）とした——`unit_area_shape` が記入例で `""` を使っており、
文字列フィールドの「該当なし」は空文字、数値フィールドの「該当なし」は `null` という
記入例の流儀に合わせた。9 件が値を持ち、19 件が空。

## corpus 配下で開いたファイル

**対象の STEP ファイル 1 本だけ。**
`NIST-FTC-PMI-Definitions.xlsx` と `NIST-README.txt` は開いていない。
他の corpus の STEP ファイル（ctc_*, stc_*, 他の ftc_*）も開いていない。
`ls -la corpus/nist/` でディレクトリ一覧は見たので、xlsx / README の**ファイル名とサイズは
目に入った**（中身は見ていない）。
`reference/` `bench/` `checker/` `out/` `README.md` `arms/` `docs/` `attempts/` の既存物、
`tasks/T005/FROZEN_T005.json`、過去課題の `tasks/` `attempts/` はいずれも開いていない。
`ls -la` でリポジトリ直下の一覧は見た（ディレクトリ名のみ）。

## 読めなかった箇所

無し。28 件すべての公差について、種別・値・単位・データム・修飾子・公差域の形を解決できた。
未解決の参照や、リンク先が欠けている参照は出なかった。

## 課題文が決めていないと思った箇所

1. **`zone_form` のキー名**。設問は日本語で「公差域の形」としか言わず、記入例にはキーが無い。
   `answer_format_note` が地の文で `zone_form` と呼んでいるので、それを採った。
   採点器が別名（`tolerance_zone_form` など）を期待していると落ちる。
2. **`zone_form` の「該当なし」の表現**。空文字か `null` か明示が無い。空文字を採った（上記理由）。
3. **公差値の丸め**。生の値か意図値かの指定が無い。生の値を採った。
4. **`label` の語彙**。日本語ラベルの正解表が無い。記入例に無い直角度は推定。
5. **`datums` に修飾子が付く場合の書き方**（このファイルには出なかったので実害なし）。
6. **`unit` の大小文字**。`CONVERSION_BASED_UNIT` の name は `'inch'` だが `'MILLIMETRE'` は
   大文字。記入例は `"millimetre"` と小文字なので、記入例は name をそのままではなく
   正規化している疑いがある。今回は inch なので偶然どちらでも同じ。

## 課題／記入例の側の欠陥だと思った点

1. **記入例の 2 ファイルには `zone_form` を持つ行が 1 つも無い**。意図的にキーごと省いたと
   書いてあるので設計どおりだが、結果として「キー名」も「該当なしの表現」も
   例示ゼロになった。設問が訊いているフィールドの**型と欠損表現**が課題文のどこにも
   書かれていないのは、`zone_form` だけの穴である。他のフィールドは記入例で両方（値ありと空）
   が示されている。
2. **`unit` の値が正規化なのか原文なのか不明**（上記 6）。`MILLIMETRE` → `millimetre` は
   正規化なので、原文主義の他フィールドと不整合。
3. **記入例の `file` 名が対象ファイルと紛らわしい**。`nist_stc_10_...` と `nist_ctc_03_...` は
   corpus に実在する。注意書きがあるので誤読はしなかったが、対象が
   `nist_ftc_06_...` 1 本なのに例が 2 本あるので、答案の `results` 配列の要素数を
   間違える余地がある（1 要素にした）。
4. `grade_levels_note` は「複合公差（Q6）は採点しない」と言うが、記入例には
   `composite_role` / `composite_partner` が必須キーとして入っている。書いても書かなくても
   点は変わらないと明記されているので埋めたが、「訊いていないものを記入例に載せる」のは
   T005 の実験（記入例の効果を測る）と方向が逆で、交絡になりうる。

## ファイルの内部矛盾

1. **`GLOBAL_UNIT_ASSIGNED_CONTEXT` は mm、PMI の値は inch**。
   `#9953` のコンテキストは `#10032 = CONVERSION_BASED_UNIT('MILLIMETRE', #9961)` を長さ単位に
   指定しているのに、28 件の公差値はすべて `#10033 = CONVERSION_BASED_UNIT('inch', #9962)` を
   指す。矛盾ではないが（measure が自前の単位を持つのは規格上正しい）、
   「ファイルの単位系は inch」という課題文の断定は**幾何形状には当てはまらない**。
   形状は mm、PMI は inch である。
2. `#9961 = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.), #9959)` — 換算係数 1.0 の
   `CONVERSION_BASED_UNIT('MILLIMETRE')` が、実体は `SI_UNIT(.MILLI., .METRE.)` そのもの。
   冗長（`#9959` と `#9960` も同一内容の重複実体）。
3. **公差値の浮動小数ノイズ**。`0.0250000000001`、`0.01000000000004`、
   さらに同じ 0.01 inch のはずの平面度が `#9981 = 0.01000000000004` と
   `#9983 = 0.0100000000000401` で桁が違う。同一の設計値が別の丸め結果になっている。
4. `#111` の `Position.21` と `#112` の `Position.1` が別物なのに、`#133` にも `Position.1` が
   ある（`name` が一意でない）。`Position.1` は 2 実体（#112 と #133）で共有され、
   値もデータムも違う。`name` を主キーにできない。
5. データム `K` は `#324` 経由で `Datum System .12`（#336）から参照されるだけで、
   `DATUM_FEATURE` が 6 件しかないのに `DATUM` は 10 件ある。データム記号の一部は
   フィーチャに結び付いていない（`PLACED_DATUM_TARGET_FEATURE` が 6 件別にある）。
   設問は「定義されているデータム記号」なので 10 件すべてを挙げた。

## 制約違反

無し。STEP / AP242 専用ライブラリは使っていない（`re` / `json` のみ）。
一時ファイルは指定されたスクラッチパッド配下だけを使った。
