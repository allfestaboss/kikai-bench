#!/usr/bin/env bash
# 使い方: ./run.sh [T001 T002 ...]   引数なしで全課題
#
# 採点の前に必ず (1)較正 (2)外部検算 (3)敵対テスト (4)記入例の照合 を通す。
# どれか落ちたら数字を出さない。
#
# (4) は他ベンチ(bim)で課題文に答えを印字したまま走らせた事故を受けて足した。
# (1)-(3) は参照解の関数なので、原理的に課題文と記入例を見ていない。
set -euo pipefail
cd "$(dirname "$0")"
PY=python3
TASKS=("$@")
if [ ${#TASKS[@]} -eq 0 ]; then
  TASKS=()
  for d in tasks/*/; do TASKS+=("$(basename "$d")"); done
fi
mkdir -p out

# 凍結／事後記録の検算。課題文・参照解・腕への文面が答案の後に動いていたら止める。
$PY -m bench.freeze > out/_freeze.txt 2>&1 || {
  echo "凍結が破れている。out/_freeze.txt を見ること。"; cat out/_freeze.txt; exit 1; }
echo "凍結OK: $(grep -c '^\[OK' out/_freeze.txt) 課題"


# (0) 参照解を作り直す
for T in "${TASKS[@]}"; do $PY -m bench.build_ref "$T" >/dev/null; done

# (1) 較正。生テキストの手読みと一致するか
$PY -m bench.selfcheck > out/_selfcheck.txt || {
  echo "較正に失敗。out/_selfcheck.txt を見ること。"; exit 1; }
echo "較正OK: $(grep '較正:' out/_selfcheck.txt)"

# (2) 外部検算。NIST の定義とファイル自身の検証プロパティ
$PY -m bench.crosscheck > out/_crosscheck.txt || true
echo "外部検算: $(grep '定義との突き合わせ' out/_crosscheck.txt)"
echo "          $(grep -E '^  一致 ' out/_crosscheck.txt)"

# (4) 記入例。漏れ・誤り・隠蔽を見る
$PY -m bench.leak > out/_leak.txt || {
  echo "記入例の照合に失敗。out/_leak.txt を見ること。"; exit 1; }
echo "記入例: $(grep -c '^  \[' out/_leak.txt) 件の既知の欠陥（未修正・凍結中）"

for T in "${TASKS[@]}"; do
  # (3) 敵対テスト
  $PY checker/adversarial.py "$T" > "out/${T}_adversarial.txt" || {
    echo "敵対テストに失敗。out/${T}_adversarial.txt を見ること。"; exit 1; }
  echo "敵対OK($T): $(grep -c '^\[OK' "out/${T}_adversarial.txt") ケース"

  FILES=("out/_calib_$(echo "$T" | tr 'A-Z' 'a-z').json")
  for f in attempts/$T/*.json; do
    case "$(basename "$f")" in cost.json) continue ;; esac
    [ -e "$f" ] && FILES+=("$f")
  done
  $PY bench/check.py "tasks/$T/task.json" "reference/$T.json" "${FILES[@]}" > "out/${T}.json"
  $PY -m bench.summary "$T"
done

echo
echo "詳細: out/<TASK>.json  敵対: out/<TASK>_adversarial.txt"
