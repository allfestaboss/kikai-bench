# T004 armC_r2 報告

対象: `corpus/nist/nist_ftc_06_asme1_ap242-e2.stp`（10,970 行 / 10,034 実体）

## どう読み取ったか

自前の STEP Part21 パーサを Python 標準ライブラリのみで書いた（scratchpad の `parse.py`）。

1. `DATA;` 〜 最後の `ENDSEC;` を切り出し、**引用符の外の `;`** で実体に分割（`''` エスケープを処理）。
2. 各実体を「単純形 `#n=NAME(...)`」と「複合形 `#n=(NAME(...) NAME(...) ...)`」の両方でパースし、
   実体 ID → {サブ実体名 → パラメータ文字列} の表にした。
3. パラメータは括弧の深さと文字列状態を見て**トップレベルのカンマ**でのみ分割。
4. 幾何公差の葉の型 15 種（POSITION / FLATNESS / PERPENDICULARITY / SURFACE_PROFILE ほか）を
   名前で走査 → 28 件。grep でも同じ 28 件（POSITION 11 / SURFACE_PROFILE 12 / FLATNESS 3 /
   PERPENDICULARITY 2）であることを裏取りした。
5. 公差値は `GEOMETRIC_TOLERANCE` の第3属性 → `LENGTH_MEASURE_WITH_UNIT` → 単位実体。
6. データムは `GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE` → `DATUM_SYSTEM` の
   constituents の**リスト順**（＝優先順位）→ `DATUM_REFERENCE_COMPARTMENT.base` → `DATUM.identification`。
7. 公差域の形は `TOLERANCE_ZONE.defining_tolerance` から公差へ逆引きし、`TOLERANCE_ZONE_FORM` の名前をそのまま。

### 単位換算（規則5の遵守）

ファイル内で自己完結して換算した。25.4 を外から持ち込んでいない。

- `#10033 = (CONVERSION_BASED_UNIT('inch',#9962) LENGTH_UNIT() NAMED_UNIT(#10031))`
- `#9962 = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960)`
- `#9960 = (LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.))`

つまり 1 inch = 25.4 [MILLI・METRE] を**ファイルから読んだ**。公差値 122 件すべてが `#10033` を参照。

## 判断に迷った箇所（課題文が決めていないと思った箇所）

1. **公差値の浮動小数ノイズ。** ファイルの実値は `0.0500000000002` `0.01000000000004`
   `0.0100000000000401` のように CAD 由来の誤差を含む。記入例の値（0.005 など）はきれいなので、
   丸めるべきか迷った。**規則「ファイルに実際に入っているものを報告する」を優先し、`value` は
   ファイルの literal をそのまま**にした。`value_mm` だけは literal × 25.4 を 10 桁で丸めている
   （`0.254000000000018…` → `0.254`）。数値許容つきの比較ならどちらでも通るはずだが、
   丸め方針は課題文が決めていない。

2. **`unit` の表記。** `CONVERSION_BASED_UNIT` の name 属性そのまま `"inch"` とした
   （記入例と同じ綴り）。

3. **データム一覧（Q5）の順序。** 課題文は順序を決めていない。記入例が A..J の昇順だったので
   **アルファベット昇順**にした。ファイル内の `DATUM` 実体の出現順は D,B,C,A,E,F,H,G,J,K である。

4. **`composite_role` / `composite_partner`。** Q6 は採点対象外だが、記入例に欄があるので埋めた。
   `GEOMETRIC_TOLERANCE_RELATIONSHIP('composite','',#a,#b)` の relating(#a)=upper、related(#b)=lower
   と解釈した（記入例の 486/487 の向きに合わせた）。

5. **`label`（日本語名）。** 課題文にも記入例にも `PERPENDICULARITY_TOLERANCE` の訳が無いので
   「直角度」とした（JIS の通称）。採点対象かどうかも不明。

## corpus 配下で開いたファイル

**対象の STEP ファイル 1 本のみ。**
`corpus/nist/nist_ftc_06_asme1_ap242-e2.stp` を Read / grep / 自作パーサで読んだ。

- `NIST-FTC-PMI-Definitions.xlsx` は**開いていない。**
- `NIST-README.txt` は**開いていない。**
- 他の 17 本の STEP ファイルは**開いていない。**`ls -la corpus/nist/` でファイル名と
  サイズの一覧は見た（中身は読んでいない）。
- `reference/` `bench/` `checker/` `out/` `README.md` `arms/` `docs/` `attempts/` の中身、
  および T001〜T003 の `tasks/` は**開いていない。**
- STEP / AP242 専用ライブラリは**使っていない**（`re` `json` `sys` のみ）。

### 1件だけ申告

`tasks/T004/FROZEN_T004.json` は「tasks/T004/ は見てよい」に含まれると読んで開こうとしたが、
`answers_at_record` というキー名を見た時点で参照解が入っている可能性を疑い、
**トップレベルのキー名と型だけを出力して値は一切表示していない**（`/task` `/kind`
`/answers_at_record`(list) `/arms_prompt_recorded`(bool) `/hard`(dict) `/soft`(dict)）。
以後このファイルには触れていない。**「tasks/T004/ は見てよい」という指示と、
凍結ファイルが同じディレクトリにあることは、課題側の設計上の危険だと思う。**

## 読めなかった箇所

なし。28 件すべてについて種別・値・単位・データム・修飾子・公差域の形を確定できた。

## 課題・記入例の側の欠陥だと思った点

1. **`asked` の「（ファイルの単位系は inch）」が厳密には誤り。**
   このファイルの `GLOBAL_UNIT_ASSIGNED_CONTEXT` は `#10032 = CONVERSION_BASED_UNIT('MILLIMETRE',…)`
   を参照しており、**大域の長さ単位は mm** である。inch なのは幾何公差の
   `LENGTH_MEASURE_WITH_UNIT` が個別に参照する `#10033` の方。結果的に「公差値は inch」は
   正しいが、「ファイルの単位系は inch」は正しくない。素直に大域単位系を見に行った腕は
   「換算不要」と誤読しうる。

2. **記入例に採点対象の答えが実質的に混ざるリスク。** 記入例のファイル名は対象外だが、
   `zone_form` の値 `"cylindrical or circular"` は本ファイルでも 7 件で同じ文字列になる。
   `TOLERANCE_ZONE_FORM` の名前は事実上この 2〜3 種しかないので、Q4(2) は記入例を写すだけで
   相当数当たる。**Q4 を採点対象に加えた T004 では、記入例が Q4(2) の答えを部分的に配っている。**

3. **Q4(3)(4)(5) がこのファイルでは全件空。**
   `PROJECTED_ZONE_DEFINITION` も `GEOMETRIC_TOLERANCE_WITH_DEFINED_UNIT` /
   `..._DEFINED_AREA_UNIT` もこのファイルには 1 件も存在しない（grep で 0 件を確認）。
   したがって突出長さ・単位あたりの長さ・単位あたりの領域の形は 28 件すべて空になる。
   **「該当が無いものは空で報告する」という指示に素直に従うと、Q4 の 5 項目のうち 3 項目は
   `null`/`""` を 28 行並べるだけで満点になる。**T004 の狙い（設問を採点対象に揃える）に対して、
   対象ファイルの側にその 3 項目を分離する材料が無い。**記入例には 3.2 / 15.0 / RECTANGULAR という
   非空の値が載っているので、むしろ「例に値があるのに本体に無い」ことに気づけるかを測る形に
   なっており、意図と噛み合っていない可能性がある。**

4. **`label`（日本語名）と `name` が採点対象かどうか `asked` に無い。**
   `asked` が挙げるのは実体番号・種別・公差値・単位・データム・修飾子ほか 5 項目・データム記号で、
   `label` と `name` は訊かれていない。記入例には必須欄として存在する。
   T004 が直そうとした「訊いていないものを採点する」問題が、この 2 欄には残っている可能性がある。

5. **`grade_levels` に Q6 が無いのに記入例が複合公差を含む。** これは note で明示されているので
   欠陥ではないが、`composite_role` / `composite_partner` を空にしてよいのか埋めるべきなのかは
   書式としては不定。埋めた。

## ファイルの内部矛盾に気づいた点

1. **`#107` / `#108` の書き方が Part21 非準拠。**

   ```
   #107=PERPENDICULARITY_TOLERANCE('Perpendicularity.1','',#10003,#993,(#331));
   ```

   `PERPENDICULARITY_TOLERANCE` は `GEOMETRIC_TOLERANCE` の 4 属性しか持たないのに
   第5引数 `(#331)` がある。これは `GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE.datum_system` で、
   本来は他の 23 件と同様に複合実体 `(GEOMETRIC_TOLERANCE(...) GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE(...) PERPENDICULARITY_TOLERANCE())`
   で書かれるべきもの。同じファイル内で 23 件が複合形、2 件が平坦形という**書式の不統一**がある。
   意味は一意なので第5引数を datum_system として読んだ。
   **厳密な Part21 パーサ（既製ライブラリ含む）はここで属性数エラーを出す可能性がある。**

2. **公差域の形を持たない位置度が 2 件。**
   `TOLERANCE_ZONE` は 9 件しかなく、`#138`(Position.9) と `#139`(Position.8) には
   対応する `TOLERANCE_ZONE` が無い。他の 9 件の位置度にはすべて zone がある。
   位置度は本来円筒公差域を持つはずで、エクスポート漏れと思われる。**空で報告した。**

3. **同名の別実体が複数ある。**
   `Position.1` が `#112`（0.02 inch, F, MMR）と `#133`（0.015 inch, E/A/B, 修飾子なし）の 2 件、
   `Position surfacic profile.9/10/11/12` が複合公差の上下でそれぞれ同名。
   `name` はキーとして使えない。実体番号でしか一意化できない。

4. **公差値の浮動小数ノイズ。**
   `0.0100000000000401`（#9983）と `0.01000000000004`（#9981, #10006）は同じ 0.010 in の
   はずだが桁が違う。設計値は 0.010 / 0.012 / 0.015 / 0.020 / 0.025 / 0.040 / 0.050 in と読める。

5. **`DATUM` は 10 個（A〜H, J, K）定義され、10 個すべてが `DATUM_SYSTEM` から参照されている**が、
   `DATUM_FEATURE` は 6 個、`PLACED_DATUM_TARGET_FEATURE` は 6 個しかない。
   データム記号の数と、それを実現する形体の数が合っていない（K, J, G, H はデータムターゲット由来か）。
   Q5 は「定義されているデータム記号」なので 10 個すべてを報告した。
