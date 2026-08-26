# QA-0008 Cycle 1 別コンテキスト独立レビュー

created: 2026-08-27 02:30 (JST)
update: 2026-08-27 02:30 (JST)
author: Lunaサブエージェント

## 実行情報

- ケースID: QA-0008
- サイクル: 1
- 行動: independent-review
- agent_id: `01a03f07-0a5b-79b3-9731-8cfb717f3605`
- 役割: reviewer
- 実行方式: Codexから分離した別コンテキストのLuna
- 対象: `openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/`
- 制約: 読み取り専用。ファイル編集、QAクローズ、配備、git操作なし

## 実行結果

- `python3 -B -m unittest discover -s stage/tests -p 'test_*.py'`: 43件成功
- pytest: 利用不可（`No module named pytest`）。環境制約として記録する
- 判定: `adjudication-required`
- compact無条件採用: 不可

## 確認済み事項（CONFIRMED）

- 43機能ID、Legacy互換24件、新規機能19件の台帳が存在する
- 三版BundleのManifest、SHA-256、fixture実行結果が保存されている
- Legacyの後発submission／digest／revision不在が意図的非互換として分離されている
- Candidate／compactの安全回帰EvidenceがObservedである
- `evidence-gap`、`unverified`、`intentional-noncompatibility`を全体合格へ昇格させていない
- サイズはCandidate 5,953行、compact 878行である。ただしサイズは安全性・互換性の証明ではない
- Legacy Bundle自体の改造は確認されなかった

## Finding

- QA-0008-F04（High、evidence-gap）: 集約済みJSONは5 Agent／Runを示すが、元Evidenceは現Changeの`stage/evidence/agents/`から再集約できない。標準Agent／Run保存ルート、または再現可能なSource Manifestが必要。
- QA-0008-F01（High、evidence-gap）: Candidateの空または欠落Evidence拒否が未実測である。
- QA-0008-F02（High、evidence-gap）: Candidate digest回帰範囲がcompactと同等でない。
- QA-0008-F05（Medium、contradictory-evidence）: tasks.mdの5.1／5.2完了表示が未検証Evidenceと不整合である。
- QA-0008-F03（Medium、evidence-gap）: Agent／Runの必須メタデータ保存粒度が不均一である。

## 人間裁定要求

Candidateの未検証契約を追加検証するか意図的非互換として受け入れるか、Agent Evidenceの保存方式を統一するか、未検証を残したままcompactを条件付き採用するかを人間が決定する。
