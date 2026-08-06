# 出典

## テストデータ（入力と照合先）

**NIST MBE PMI Validation and Conformance Testing Project / MBx Interoperability Forum**
- https://www.nist.gov/ctl/smart-connected-systems-division/smart-connected-manufacturing-systems-group/mbe-pmi-0
- https://www.mbx-if.org/home/cax/resources/

利用条件は原文で次のとおり。

> The test cases, CAD models, and STEP files can be used without any restrictions.
> Their use in other software or hardware products does not imply a recommendation
> or endorsement of those products by NIST or the MBx-IF.

出典表示が望ましいとされ、NIST ロゴを宣伝素材に使うことは認められていない。
`corpus/nist/` 以下は上記から取得したものである。

収録:

| 種別 | 内容 |
|---|---|
| FTC-06 〜 FTC-11 | Fully-Toleranced Test Cases |
| STC-06 〜 STC-10 | Simplified Test Cases（2023年、複雑な PMI を削ったもの） |
| CTC-01 〜 CTC-05 | Combined Test Cases |
| `NIST-FTC-PMI-Definitions.xlsx` | FTC の PMI 定義。64行、ASME Y14.5 の項番つき |

NIST の README より:

> The '_ap203' and '_ap242' files have graphical PMI. The '_ap242' files have semantic PMI.
> AP242 files are identified by '_ap242-e1' or '_ap242-e2' for the edition 1 or 2 of AP242.
> FTC 8 also has a file '_ap242-e1-tg' where the part geometry uses tessellated (faceted)
> surfaces instead of exact b-rep geometry. **There is no semantic PMI in this file.**

抽出器がこの `-tg` ファイルで幾何公差 0 件を返すことは、動作の裏付けになっている。

## 形式

**ISO 10303-21**（STEP Part21 交換ファイル）
**ISO 10303-242**（AP242 Managed Model-based 3D Engineering）
本 corpus のスキーマ識別子は `AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF { 1 0 10303 442 3 1 4 }`。

実物から確定させた経路は `bench/pmi.py` の docstring に書いてある。仕様書からの推測では書いていない。

## 基準

**ASME Y14.5**（Dimensioning and Tolerancing）— NIST のテストケースが準拠している。
定義 xlsx の "Standards Mapping" 列に項番が入っている（例: `Y14.5: P 7.4.6`）。

**JIS B 0060 シリーズ**（デジタル製品技術文書情報）— 日本側の対応規格。
2021年に発行完了。JAMA/JAPIA 3DAモデルガイドラインはこれを受けて発行された。
引用のみで、本ベンチのデータには使っていない。

## 使わなかったもの

**JAMA（日本自動車工業会）3D図面お手本データ**
https://www.jama.or.jp/operation/it/dg_egr/3d_drawing.html

STEP AP242 P21/XML を含み、幾何公差の解説書まで付く優れた資料だが、
自由ダウンロードできる解説書PDFの2ページ目に次の使用許諾事項がある。

> • お手本データと、付随する説明資料の全ての著作権は、一般社団法人日本自動車工業会に帰属します。
> • 本データを、そのまま、あるいはご利用者の創意とは見なし得ない軽微な変更のみを加えたものを、
>   営利・非営利を問わず、本会の許諾なしに、公開・配布・販売することを禁じます。

corpus に同梱できないため採用しなかった。データ本体の取得も Microsoft Forms 経由である。

なお同じ解説書の p.8 には、本ベンチが測ろうとしている空席そのものが書かれている（README 参照）。
