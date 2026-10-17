# spec-review r1: add-slugify

- Gate: **FAIL**（FAIL: T-1.1, T-1.2, S-text-utils-1.2, CHK-UNITTEST）
- base SHA: `080f88450384cfe927c3bfe398afcc7f201e837a`
- round SHA: `ce25449c63349650709973a4c0ee3ab78a8b3f1e`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6-luna
- 停止判定: 継続

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | FAIL | round SHAの`textutils.py`は`slugify`を定義している（関数本体は`re.sub(r'[^a-z0-9]+', '-', title.lower())`）。一方、CLI提示の必須check `CHK-UNITTEST` はexit_code 5でFAILし、「Ran 0 tests」「NO TESTS RAN」と記録されており、指定の検証は成功していない。 |
| T-1.2 | FAIL | round SHAの変更一覧に`test_textutils.py`は含まれず、`git show ce25449c63349650709973a4c0ee3ab78a8b3f1e:test_textutils.py` はpath not foundで失敗した。実装報告も未着手・テスト未作成としている。 |
| S-text-utils-1.1 | PASS | round SHAの`textutils.py`では入力を小文字化し、`[^a-z0-9]+`に一致する空白・記号の連続をハイフンに置換する。この実装から`Hello, World!`は`hello-world`となる。 |
| S-text-utils-1.2 | FAIL | round SHAの`textutils.py`の置換は入力の先頭・末尾の非英数字もハイフンにする。`  Spec Review  `は`-spec-review-`となり、期待値`spec-review`と一致しない。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-UNITTEST | FAIL | 5 | 期待 0・実際 5: ----------------------------------------------------------------------<br>Ran 0 tests in 0.000s<br><br>NO TESTS RAN |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 新規 | high | missing | T-1.1 | openspec/changes/add-slugify/review/checks.json:1 | 指定された`python3 -m unittest test_textutils`が成功していない。CLI記録では0件のテストしか検出されず、必須checkがFAILしている。 | `test_textutils.py`を追加してテストを検出可能にし、必須checkを成功させる。 |
| F-002 | 新規 | high | missing | T-1.2 | textutils.py:4 | 受入基準で求められるテストファイルと、各Scenarioに対応するテストがround SHAに存在しない。 | 空白・記号・大文字・前後空白を含む入力を網羅し、各Scenarioに対応するテストを`test_textutils.py`に追加する。 |
| F-003 | 新規 | medium | defect | S-text-utils-1.2 | textutils.py:5 | 前後の空白が置換結果の先頭・末尾にハイフンとして残り、指定Scenarioの期待値`spec-review`を返さない。 | 置換後に先頭・末尾のハイフンを除去し、前後空白のScenarioを満たす。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

指定基準と必須checkに未達があり、Gate規則上FAIL。テストが未作成で必須unittest checkが失敗し、前後空白のScenarioでもslugifyの返値が期待値と異なる。
