# spec-review r1: add-slugify

- Gate: **FAIL**（FAIL: T-1.1, T-1.2, S-text-utils-1.1, S-text-utils-1.2）
- base SHA: `080f88450384cfe927c3bfe398afcc7f201e837a`
- round SHA: `26be2273f166787fa5c61ec4360f29fe1c31d1ed`
- Reviewer: cursor 2026.10.14-941492e ／ model: gpt-5.3-codex
- 停止判定: 継続

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | FAIL | `textutils.py:5` は `re.sub(r'[^a-z0-9]+', '-', title.lower())` のみで前後ハイフンを除去していない。実測でも `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q test_textutils` は失敗し、`test_textutils.py:8` で `hello-world-` と `hello-world` の不一致を確認。 |
| T-1.2 | FAIL | `test_textutils.py:7-12` には `Hello, World!`（空白・記号）と `ABC Def`（大文字）のテストはあるが、前後の空白入力（例: `"  Spec Review  "`）のテストが存在しない。 |
| S-text-utils-1.1 | FAIL | 実測コマンド `PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY' ...` で `slugify('Hello, World!')` の出力は `hello-world-`。期待値 `hello-world` を満たさない。根本原因は `textutils.py:5` の置換後トリム未実装。 |
| S-text-utils-1.2 | FAIL | 実測コマンド `PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY' ...` で `slugify('  Spec Review  ')` の出力は `-spec-review-`。期待値 `spec-review` を満たさない。`textutils.py:5` の実装が前後区切りを除去していない。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 新規 | high | defect | T-1.1, S-text-utils-1.1, S-text-utils-1.2 | textutils.py:5 | `slugify` が非英数字を `-` へ置換するのみで、先頭・末尾の `-` を除去していないため、受入シナリオの期待値と一致しない。 | 置換後に連続/端の `-` を正規化する（例: `strip('-')` を含む処理）実装へ修正し、`Hello, World!` と `  Spec Review  ` の期待値を満たすことをテストで確認する。 |
| F-002 | 新規 | medium | test-gap | T-1.2 | test_textutils.py:6 | 受入基準で要求される「前後の空白を含む入力」のテストケースが未追加。 | `slugify("  Spec Review  ") == "spec-review"` を検証するテストを追加し、各Scenarioに対応するテストが存在する状態にする。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

slugify実装が受入シナリオを満たしておらず、必須の前後空白ケースのテストも不足しているため、本roundは受入不可です。
