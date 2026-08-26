## 1. 準備とベースライン

- [x] 1.1 実装対象を `openspec/changes/spec-driven-qa-reviewer-case-lifecycle/stage/spec-driven-qa-review/lifecycle.py` と `stage/tests/` に固定し、現状の pytest が通ることを `pytest openspec/changes/spec-driven-qa-reviewer-case-lifecycle/stage/tests -q` で確認する
- [x] 1.2 Evidence 用ディレクトリ `openspec/changes/reviewer-verification-integrity-hardening/evidence/` を作成し、ベースラインの pytest 件数をメモしたファイルを置く

## 2. digest ヘルパの集約

- [x] 2.1 handoff 生成と verify が同一入力で digest を再計算するヘルパを抽出し、`render_handoff` がヘルパ経由で digest を書くことをコード参照で確認する
- [x] 2.2 ヘルパ入力（少なくとも `case_id` / open Finding IDs / `cycle`）をコメントまたは短い docstring で固定し、Schema・digest アルゴリズム自体を変えていないことを確認する

## 3. stale digest 拒否

- [x] 3.1 `verify_submission` で handoff の `content_digest` / `semantic_digest` を正本再計算値と照合し、不一致時は例外で拒否・正本非更新とすることを実装する
- [x] 3.2 stale `semantic_digest` の negative テストを追加し、拒否と Finding 非更新を pytest で確認する
- [x] 3.3 stale `content_digest`（semantic 一致・content 不一致）の negative テストを追加し、拒否を pytest で確認する
- [x] 3.4 鮮度一致 handoff では digest 理由で拒否されない golden を pytest で確認する

## 4. Evidence パス実在

- [x] 4.1 `test_evidence` の相対パス判定ヒューリスティックを実装し、絶対パス／`file://` を拒否することを pytest で確認する
- [x] 4.2 存在する相対パス Evidence を受理する golden を pytest で確認する
- [x] 4.3 存在しない相対パス Evidence を拒否する negative を pytest で確認する
- [x] 4.4 非パスの非空自由記述はパス実在検査せず受理（他条件充足時）することを pytest で確認する

## 5. modified_files 厳密化

- [x] 5.1 fix 提出（技術検証を進める提出）で `modified_files` 欠落または空配列を拒否する実装を入れ、pytest negative で確認する
- [x] 5.2 列挙パスの欠落を拒否する既存／追加 negative を pytest で確認する
- [x] 5.3 全パス実在の `modified_files` を受理する golden を pytest で確認する
- [x] 5.4 既存 verify／close 系テストが新必須に合わせて更新され、`pytest .../stage/tests -q` が全件成功することを確認する

## 6. Evidence 記録と完了境界

- [x] 6.1 本 Change `evidence/` に pytest 出力と、C2/C3（stale digest・Evidence/`modified_files`）消化メモを記録する
- [x] 6.2 lifecycle Change の task 5.2／残余表記を、本 hardening のテスト結果に合わせて更新するか、未消化なら `evidence-gap` のまま残す（過大完了にしない）
- [x] 6.3 Schema／共有 digest アルゴリズムを変更していないこと、および外部 Skill 配備・旧版削除・commit／push を行っていないことを作業メモで確認する
