# kikai-bench — AIは機械図面の幾何公差をどこまで読めるか

STEP AP242 に埋め込まれた **semantic PMI（機械可読な幾何公差・データム）** を
読み取る能力を、機械採点で測るベンチマーク。
[cad-bench](../cad-bench) / [sekisan-bench](../sekisan-bench) / [doboku-bench](../doboku-bench) /
[kanzei-bench](../kanzei-bench) / [jiban-bench](../jiban-bench) に続く AI実務到達度インデックスの6本目で、
**CAD横断シリーズの3業界目**（建築2D → 土木SXF → 機械STEP）。

## 測るのは「書けるか」ではなく「読めるか」

doboku-bench は SXF を**書けるか**を測った。こちらは**読めるか**を測る。

幾何公差を読み違えることは実務の事故に直結する。`⌖ ⌀.025 Ⓜ | C | A | B` の
データムの順序を入れ替えれば、測定の基準面が変わり、合否が変わる。
そして semantic PMI は正解が構造化されているので、採点が素直に作れる。

## 制度的な空席 — 業界が自分で書いている

土木では国交省が「電子納品チェックシステムでは成果品の内容を確認することはできません」と
自ら明記していた。機械はもっと直接的だった。

JAMA/JAPIA が2023年4月に参加各社（トヨタ・ホンダ・マツダ・スズキ・ダイハツ・いすゞ・
SUBARU・三菱・スタンレー電気ほか）へ行った課題ヒヤリングの結果、**第1位がこれである**。

```
   各社から提出された課題              課題への対応
1  効率的な検図方法が不明            (本書でのモデル作成の取組みとは、別に対応)
2  2D図面と比較すると、3D図面作成工数が増加   モデル作成工数課題を考慮したモデルを検討
```

（日本自動車工業会「3D図面お手本データの解説」2024-03-31, p.8）

**業界自身が「検図の方法が分からない」を筆頭に挙げ、標準化の取り組みからは棚上げしている。**

2009年の「3D単独図CAD機能検証結果レポート」を見ると、工程はこうなっている。

```
3Dモデル作成 → 3D単独図モデル作成 → 検図（紙出力）・承認
検証項目のひとつ：「3D単独図を三角法で2D展開して検図を行えるか」
```

**データには機械可読な幾何公差が入っているのに、検図は紙に出して人が見ている。
しかもその方法が2023年時点でまだ定まっていない。**

3業界を同じ物差しで測ると、「検査されていない」にも段階があることが見える。

| 業界 | 空席の形 |
|---|---|
| 建築2D | 検図はあるが基準の適用が属人的（証拠は弱い） |
| 土木 | **検査する仕組みはあるが、中身を見ない** |
| 機械・製造 | **データは機械可読なのに、検査方法が決まっていない** |

## 参照解は NIST が持っている

| | 出どころ | 誰が確定させたか |
|---|---|---|
| 入力 | NIST / MBx-IF のテストケース（FTC・STC・CTC） | 米国 NIST |
| 形式 | ISO 10303-21 / -242（AP242） | ISO |
| 基準 | ASME Y14.5 | ASME |
| 参照解 | STEP ファイルに実際に入っている semantic PMI | **こちらは何も決めていない** |

利用条件は原文で `The test cases, CAD models, and STEP files can be used without any restrictions.`。
**corpus をそのまま同梱できる**ので、検証可能性が保てる。

日本側の JAMA お手本データは幾何公差の解説まで付く優れた資料だが、
**再配布が明示的に禁止**されているため採用しなかった（[docs/SOURCES.md](docs/SOURCES.md)）。
同じ「業界標準化のための供試データ」で、日米で出し方が逆になっている。

## corpus — AP242 17ファイル、幾何公差 341件

```
ファイル                              公差  データム  種別内訳
nist_ftc_06_asme1_ap242-e2.stp        28    10  FLATNESS=3 PERPENDICULARITY=2 POSITION=11 SURFACE_PROFILE=12
nist_ftc_08_asme1_ap242-e2.stp        33    11  FLATNESS=3 PARALLELISM=5 PERPENDICULARITY=1 POSITION=13 …
nist_ftc_10_asme1_ap242-e2.stp        40    11  CYLINDRICITY=2 FLATNESS=1 PERPENDICULARITY=6 POSITION=19 …
nist_ftc_08_asme1_ap242-e1-tg.stp      0     0  （テセレーション版。NIST README のとおり semantic PMI 無し）
…
```

`-tg` ファイルで 0 件を返すことが、抽出器が「あるものを読んでいる」ことの裏付けになっている。

## 較正 — 生テキストの手読みと一致

`bench/selfcheck.py` は step.py も pmi.py も呼ばず、ファイルから直接読んだ行を
リテラルに書き下して突き合わせる。

```
$ python -m bench.selfcheck
--- #146 Flatness.1 ---
  kind       手=FLATNESS_TOLERANCE    抽出=FLATNESS_TOLERANCE
  value_mm   手=0.254000000001        抽出=0.254000000001        差=0.00e+00
--- #111 Position.21 ---
  datums     手=('C', 'A', 'B')       抽出=('C', 'A', 'B')
  value_mm   手=0.635000000003        抽出=0.635000000003        差=0.00e+00
  modifiers  手=('MAXIMUM_MATERIAL_REQUIREMENT',)  抽出=('MAXIMUM_MATERIAL_REQUIREMENT',)

較正: OK（手読みと一致）
```

単純実体（FLATNESS）と、データム参照＋MMC修飾子つきの複合実体（POSITION）の両方で一致する。

## 外部検算 — 採点器を作る前に、抽出器のバグを5件見つけた

`bench/crosscheck.py` が `NIST-FTC-PMI-Definitions.xlsx` と突き合わせる。
較正（`selfcheck.py`）は自分の手読みとの照合なので、同じ思い込みをしていれば一緒に間違える。
こちらは照合先が外部なので、その思い込みごと検査できる。

**jiban-bench では採点器と敵対テストを作り込んだ後に、腕が参照解の誤りを4件見つけた。**
今回は外部の照合先が最初からあるので、作り込む前に使った。結果、5件出た。

| # | 見つかった抜け | 影響 |
|---|---|---|
| 1 | 公差域の形（`TOLERANCE_ZONE_FORM`）を一切拾っていない | `⌀`（円筒）と `S⌀`（球）の区別が消える |
| 2 | 複合 `SI_UNIT` のパートは `(prefix, name)` なのに `[1],[2]` を見ていた | **mm 換算が1000倍狂う**（FTC-09/10） |
| 3 | magnitude が複合実体の形を扱えていない | FTC-08/11 の公差値が丸ごと `None` |
| 4 | 共通データムが `DATUM_REFERENCE_ELEMENT` を1段はさむ形に未対応 | `E-F` が `#437-#436` になる |
| 5 | **単純形の第5引数にあるデータム参照を見ていない** | **361件中48件（13%）のデータムが消える** |

一致率は 32/45 → 36/45 → **39/45** と上がった。

2 と 5 は静かに壊れる種類のバグである。値も種別も出るので、
一見それらしい参照解ができあがる。**採点器を先に作っていたら、この参照解を真として
敵対テストを全通過させ、「検証済み」と称して公開していた。**

較正が素通りした理由もはっきりしている。手読みしたのが FTC-06 だけで、
その公差がたまたま全て複合形・inch 系だった。**較正は形式の違う複数ファイルで取る**
必要がある。いまは3形式5ケースで取っている。

### 残っている6件

| 件数 | 内容 | 見立て |
|---|---|---|
| 1 | `Ⓟ.260`（突出公差域）を修飾子として拾えていない | **抽出器の抜け。未対応** |
| 3 | 値が定義と違う（`.020/.060` に対しモデルは `.01` 等） | モデル側の差の可能性 |
| 2 | データムが定義と違う（`D|B|C` に対し `A|B|C`） | モデル側の差の可能性 |

NIST 自身が「CAD がどうモデル化したか／どう STEP に書き出したかで差が出うる」と
断っているので、後者2つは断定しない。**差があること自体を記録する**のが正しい扱いで、
その差を測ること自体が結果になる。

未解釈が1件（FTC-11 ATC55 `⌢ (197.9)`）。公差値を持たない線の輪郭度で、
公差記入枠として読めない。**黙って捨てず、未解釈として数え上げている。**

## 実物から確定させた構文

仕様書からの推測では書いていない。実データで出てきた形だけを実装した。

```
単純     #146=FLATNESS_TOLERANCE('Flatness.1','',#9981,#2605);

複合     #111=(GEOMETRIC_TOLERANCE('Position.21','',#9987,#977)
               GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE((#329))
               GEOMETRIC_TOLERANCE_WITH_MODIFIERS((.MAXIMUM_MATERIAL_REQUIREMENT.))
               POSITION_TOLERANCE());

公差値   #9981=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.01000000000004),#10033);
         #10033=(CONVERSION_BASED_UNIT('inch',#9962,…)…);
         #9962=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#9960);

データム #329=DATUM_SYSTEM('Datum System .5',$,#9395,.F.,(#308,#309,#310));
         #308=DATUM_REFERENCE_COMPARTMENT('',$,#9395,.F.,#290,$);
         #290=DATUM('',$,#9395,.F.,'C');
```

区画の並び順がそのままデータムの優先順位になる。

**共通データム**は着手時に想定していなかった形で、FTC-08 で出てきた。
`COMMON_DATUM_LIST((#76,#77))` は2つのデータムが1つの区画として働くもので、
ASME Y14.5 では `A-B` と書く。**推測で潰さず、実物に合わせて対応した。**

## 構成

```
bench/step.py        STEP Part21 パーサ（複合実体・型付き値に対応）
bench/pmi.py         semantic PMI の抽出と正規化
bench/build_ref.py   参照解の生成
bench/selfcheck.py   生テキストの手読みとの較正
tasks/T001/          読解の課題
corpus/nist/         NIST のテストデータ（制限なく再配布可）
docs/SOURCES.md      全ての出典と、使わなかったものの理由
```

## これから

- 採点器（`bench/check.py`）と敵対テスト
- `NIST-FTC-PMI-Definitions.xlsx`（64行、ASME Y14.5 項番つき）を使った**抽出器の外部検算**。
  NIST 自身が「CAD がどうモデル化したか／どう書き出したかで差が出うる」と断っているので、
  定義と中身は必ずしも一致しない。その差を測ること自体が結果になる
- 腕の実走とコスト計測（jiban-bench の `bench/cost.py` を持ってくる）

## 出典

テストデータは NIST MBE PMI Validation and Conformance Testing Project および
MBx Interoperability Forum のものである。詳細は [docs/SOURCES.md](docs/SOURCES.md)。
