# QA-003 Cycle 3 独立QAレビュー

created: 2026-10-05 15:55 (JST)
update: 2026-10-05 15:55 (JST)
author: Codex (GPT-6)

## 結論

**Gate: FAIL**。Provenanceと全必須checkの最終有効実行はPASS。前回QA-F01（最終本文の走査結合）とQA-F02（必須checkの保護）は解消を確認した。ただしAC-003に、最終走査の停止境界と拒否後の状態保存・再試行の不一致が残る。Blocking 1件、Task 1件。OwnerのACCEPT/ARCHIVEや既存QA状態の変更は行わない。

## 対象とprovenance

- Repository: `syrius2000/qa-products`、branch: `codex/unify-qa-skill-workflow`。
- Baseline: `17bd3e7a3d81842bb5906ac7ab25329ec0be4ffb`（docs: add cross-device development handoff memo）。
- Reviewed: `47b6a58f3323d4fcd455d768314f2e4c97b88dfd`（Yip: fix QA-003 Cycle 2 findings）。
- 両commitはこのcloneに存在し、baselineはreviewedの祖先。originも指定repositoryと一致。別SHAへの置換なし。
- [保存済み依頼](00_invite.md)のSHA-256: `0043edf3f2396586de2afaa230d73801701948928e2cb9d99db41a2af393c153`。固定SHA・AC原文・資材hash・出力先をユーザー依頼と照合。
- 全差分は7ファイル、267追加/19削除、renameなし。計画036、OpenSpec、正本/配布runtime、公開手順、Reviewer契約、testを個別確認。差分のwhitespace検査も成功。
- 資材は `git show <SHA>:<path>` のraw bytesをSHA-256計算し、依頼値と照合した。

| 資材 | Reviewed SHAのSHA-256 | 結果 |
|---|---|---|
| quality-loop/skills/quality-qa/SKILL.md | `57bb58973476cb503c35ea2981c55908c245d8c6e34972385e4c987740bdc261` | 一致 |
| quality-loop/skills/quality-qa/references/reviewer_contract.md | `0a0cf6793197fedd16bd365b8d1b8280a790d77c83c8f3b7d1eda0338c6dec42` | 一致 |

Baseline契約も独立計算し、`84f11def7f338acbf91362bbd8ad62834cd195383830a8684ec7ec7f4d3bf8cc`と一致。Cycle 2のhash不一致HOLDは当時の記録として保持し、今回のhash一致でその記録を訂正しない。

Reviewed SHAのQuality QA SkillとReviewer契約を読んで適用した。通常の単一Markdown出力に対し、このユーザー依頼は4成果物を明示しているため、ユーザー指定を優先する。実装担当の説明や実装者検証結果を根拠の代用にしていない。独立性は本レビュー依頼の別担当セッションと実行Evidenceによる記録であり、モデル名だけで証明したとは扱わない。

## 隔離と既存変更

read-only preflightでHEAD=Reviewed、stagedなし、既存unstagedは `openspec/changes/unify-qa-skill-workflow/tasks.md`、既存untrackedは実装報告002、依頼00、Cycle 2報告、メモと確認。これらは今回の固定commit差分に混入させず保持した。

実行treeは `git archive Reviewed` の内容を出力DIR配下の一時領域へ展開。pytestの一時fixtureも同領域へ限定し、終了時に削除。共有worktreeの製品、OpenSpec、依頼、既存QA状態は変更していない。Git操作を伴うtestは合成repoとlocal bare remoteだけであり、本repositoryのcommit/push/merge、外部配置・旧版削除、ネットワーク・認証情報・依存導入は未実施。

## 受入基準の照合

### AC-001 / QA-F01

対象SHA確定後に生成された最終依頼本文と製品対象が走査され、最終依頼SHAが公開状態へ記録される。走査後の変更は招待commit前に拒否され、commit内blob hashと走査hashの一致をpush前に検証する。正常系・改変拒否・機密/個人パス拒否で、拒否時にremoteへ公開されないこと。

判定: **PASS**。根拠: workflow.py:291–315、tests/test_qa_workflow_contract.py:1078–1122。固定SHA正常系ではsnapshot/contract/招待blob/commit識別の全一致。未確定正常系はsuiteで確認。改変拒否、最終化後のsecret/個人パス拒否は独立fixtureでremote不変・対象外index不変。

### AC-002 / QA-F02

既存必須checkの削除、ID変更、`required=false`、argv/cwd/env/timeout/期待終了コード等の変更を承認文があっても拒否する。許される契約変更では旧新hashを明示承認へ結び付け、記録に旧新契約hashと構造化差分を保存する。

判定: **PASS**。根拠: workflow.py:162–198、tests/test_qa_workflow_contract.py:660–706。Python minimum・typeを含む20拒否fixture、hash不足/誤hash/他契約hash拒否、任意追加の旧新hashとadded/removed/changedを確認。

### AC-003 / 同期・仕様

正本runtimeと配布runtime、OpenSpec要件、公開手順、Reviewer契約が実装挙動と一致し、対象SHA上のReviewer資材hashが依頼記載値と一致する。

判定: **FAIL**。根拠: runtime全5モジュールraw bytes一致とReviewer資材hash一致はPASS。ただしspec.md:119、publish.md:21/29とworkflow.py:285–312の拒否境界・状態保存にQA-C3-F01の不一致。

### AC-004 / 回帰

対象SHAでF01/F02の正常系・拒否系を含む `quality-loop` の必須suiteが実行可能である。実行できない項目は結果と理由を残し、PASSにしない。

判定: **PASS**。根拠: 固定SHAの隔離tree、Python 3.12.3/pytest 7.4.4で174 passed、exit 0。同期6 passed、strict OpenSpec valid=true。初回実行の隔離条件不備と再実行を区別して記録。

## 根拠付きFinding

### QA-C3-F01 — 最終走査拒否時の対象commit/状態が公開停止・再試行契約と一致しない

- severity: **Medium**、status: **OPEN**、repair_surface: **code**、対応AC: **AC-003**。
- 一次根拠: `openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md:119` は「対象commit・依頼commit・remote更新の前に停止」。`quality-loop/skills/quality-qa/references/publish.md:21` は「commit/pushを開始しない」、同 `:29` は同じ操作の再試行を案内する。
- 実装: `quality-loop/qa_workflow/workflow.py:285` で対象commit、`:286` のfinalize（本文書換えは `:231`）、その後 `:300` で最終走査。状態保存は `:312` であり、最終走査拒否ではそこへ到達しない。配布runtimeも同じ。
- 期待動作: 最終走査拒否で何を作成・保持するか、対象確定後の状態/hash、原因解消後の再試行方法がruntime・OpenSpec・公開手順で一致すること。
- 観測: 未確定対象の正式本文生成へ合成secret/個人パスを注入し、最終走査が拒否。対象commitは既に作成され、保存stateは `reviewed=null` の旧下書きのまま。安全な正式本文へ戻しても保存invite_hashと一致せず、再試行は「下書き依頼が外部で変更されています」で拒否。
- 影響: 文書の無変更停止を満たさず、通常案内の再試行では作成済みcommitと依頼/stateの整合性を回復できない。**招待commit・remote更新はなく、対象外ユーザーindexは維持されている**。秘密情報の外部公開が起きたというFindingではない。
- 対応案: 停止境界を対象確定前/後で定義し直して採用契約へ実装と文書を揃え、最終走査拒否でも対象SHA・依頼hashと非公開状態を整合して保存/回復する。契約変更はOwner判断と実装承認の後に行う。
- 完了条件・検証: [T-C3-01](02_tasks.md)の拒否・回復・index保護fixtureと固定SHAの回帰checkが成功すること。

再現は依頼にある「最終化で依頼が更新される危険内容」の境界を検証するfault injection。通常の入力だけでこの危険本文が自動生成されると主張しない。生成直後の本文を危険値にしたときの明示されたscenarioの挙動と、コードの処理順序が根拠である。

再現手順:

1. Reviewed SHAのtest fixture `ExecutionContractIntegrationTests.setup_bare_remote` で未commit製品を含むtopic repoを作成し、cloud依頼をprepareする。
2. 対象外ファイルへユーザー変更をstageし、そのindex entryを記録する。
3. `review.invite` を一時的に包み、正式化時だけsecret様代入または合成個人パスを本文末尾へ付加する。
4. publishで最終走査拒否を観測し、HEAD、保存state、remote、対象外indexを読む。
5. 元generatorで安全な正式本文を復元し、同じpublishを再実行する。保存state/hashが旧下書きのため再試行が拒否される。
6. 全差替えをfinallyで戻し、合成repoは削除する。

```json
[
  {
    "case": "finalized-danger-and-recovery",
    "payload": "API_TOKEN=live-secret-value-123",
    "error": "QAError: 最終公開対象に機密情報または個人ローカルパスの疑いがあります",
    "target_commit_created": true,
    "unrelated_index_entry_unchanged": true,
    "staged_paths": "src/unrelated.txt",
    "remote_unchanged": true,
    "state_reviewed": null,
    "stored_invite_hash_matches_healthy_final": false,
    "retry_after_safe_regeneration": "QAError: 下書き依頼が外部で変更されています"
  },
  {
    "case": "finalized-danger-and-recovery",
    "payload": "path=/Users/real-person/private/data.csv",
    "error": "QAError: 最終公開対象に機密情報または個人ローカルパスの疑いがあります",
    "target_commit_created": true,
    "unrelated_index_entry_unchanged": true,
    "staged_paths": "src/unrelated.txt",
    "remote_unchanged": true,
    "state_reviewed": null,
    "stored_invite_hash_matches_healthy_final": false,
    "retry_after_safe_regeneration": "QAError: 下書き依頼が外部で変更されています"
  }
]
```

## 前回QA-F01/F02の再確認

- **QA-F01: 解消**。最終依頼生成後の走査（workflow.py:291–308）、走査snapshotを用いる招待commit（:314）、commit blob照合（:315–317）を確認。成功状態へ同じinvite_commitを保存（:325–326）。固定SHA正常系・未確定正常系・走査後本文改変・最終化後危険本文の拒否で確認した。元の「未走査の最終依頼が送出される」問題は再現しない。拒否境界と状態保存の別問題をQA-C3-F01として残す。
- **QA-F02: 解消**。既存必須checkはIDごとの辞書の完全一致を要求（:162–166）。承認の有無や正しい旧新hashの提示にかかわらず実行仕様変更を拒否する。許容変更は両hashを含む承認とともに旧新契約・hash・added/removed/changedを保存（:168–198）。前回QA記録の書換え・runtime上のFinding dispositionは行っていない。

追加の固定SHA正常系・ユーザーindex付き改変拒否Evidence:

```json
[
  {
    "case": "postscan-mutation-with-user-index",
    "error": "表示済み対象から内容が変わりました",
    "no_invite_commit": true,
    "no_remote_topic": true,
    "user_index_unchanged": true
  },
  {
    "case": "fixed-sha-publish",
    "snapshot_hash_matches": true,
    "contract_hash_matches": true,
    "invite_blob_matches": true,
    "commit_id_matches": true
  }
]
```

## Focus packと計画の照合

**path-sanitization: PASS（対象差分範囲）**。全7変更ファイルを確認。追加の個人絶対パスは実在情報ではなくpublish.mdの合成fixture例のみ。既存testの検出用literalも合成値として区別した。追加の実在個人情報、file:///、Windows drive/UNC pathは認めない。対象treeの全履歴に機密情報がないという保証ではない。

**openspec-coherence: FAIL**。check保護/承認とraw bytes provenanceはruntime、spec、手順、Reviewer契約が一致し、正本/配布runtime全5モジュールも一致。ただしQA-C3-F01が残る。計画036のT-01〜04は実差分7pathが計画の許可集合内に収まり、gitops/store等が未変更なのは既存のcommit snapshot guard/validationを再利用するためと確認した。計画の「拒否時HEAD/index不変」は初回走査拒否やEvidence不足ではsuiteが確認するが、最終化後の拒否に一般化できない。今回の追加Evidenceはその境界を明示する。

Change: `unify-qa-skill-workflow`、Schema: `spec-driven`、Reviewed SHA上は **46/47 tasks complete**。OpenSpec list/status/instructions applyを対象treeで読み取り確認。planning complete/valid=trueは独立QA受入や実装完了ではない。指示中の実装/チェック更新は今回のレビュー権限へ拡張していない。

## 必須check Evidence

対象はすべてReviewed SHAの隔離tree。Python **3.12.3**、pytest **7.4.4**。argvは配列としてshell=Falseで実行。timeoutは秒、durationはms、期待終了codeは0。stdout/stderr SHA-256は取得した完全raw出力のhash、切詰めなし。以下の表示では個人の絶対パスを `<OUTPUT>` に置換したが、hashは置換前。cwdは隔離treeからの相対表記、TMPDIRとGit探索境界の `<OUTPUT>` は本依頼のOutput dirの絶対展開値を意味する。

初回suiteは一時DIRを出力先内に置いたため、非Git fixtureが親の共有repoを探索し、既存test1件がFAILした。製品不具合とは混同せず、この観測も残す。Git探索境界（GIT_CEILING_DIRECTORIES）を設けた同じ固定tree/argvの再実行は **174 passed、exit 0**。有効な必須suite判定は後者。cacheproviderを無効化した以外はtest選別やskipはしていない。syncは6 passed、OpenSpec strictはvalid=true。

```json
[
  {
    "argv": [
      "python3",
      "--version"
    ],
    "cwd": ".",
    "env": {
      "PYTHONDONTWRITEBYTECODE": "1",
      "PYTHONPATH": ".",
      "TMPDIR": "<OUTPUT>/.review-e7wzazoe",
      "PYTEST_ADDOPTS": "-p no:cacheprovider"
    },
    "timeout": 30,
    "exit_code": 0,
    "duration_ms": 2,
    "stdout": "Python 3.12.3\n",
    "stderr": "",
    "stdout_sha256": "5b3e43dc38ca01e3f5a7854ba50d4330864b0c1e0f646650b2c78cf072acc366",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "truncated": false,
    "id": "CHECK-PYTHON",
    "required": true,
    "expected_exit_codes": [
      0
    ],
    "python_version": "3.12.3",
    "pytest_version": "7.4.4",
    "status": "PASS",
    "note": ""
  },
  {
    "argv": [
      "pytest",
      "--version"
    ],
    "cwd": "quality-loop",
    "env": {
      "PYTHONDONTWRITEBYTECODE": "1",
      "PYTHONPATH": ".",
      "TMPDIR": "<OUTPUT>/.review-e7wzazoe",
      "PYTEST_ADDOPTS": "-p no:cacheprovider"
    },
    "timeout": 30,
    "exit_code": 0,
    "duration_ms": 221,
    "stdout": "pytest 7.4.4\n",
    "stderr": "",
    "stdout_sha256": "4f9dfcc21a1f93a4ee147352b319c30a08c87083c56c6a21684da3d93ebbf0e9",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "truncated": false,
    "id": "CHECK-PYTEST-VERSION",
    "required": false,
    "expected_exit_codes": [
      0
    ],
    "python_version": "3.12.3",
    "pytest_version": "7.4.4",
    "status": "PASS",
    "note": ""
  },
  {
    "argv": [
      "pytest",
      "tests",
      "-q"
    ],
    "cwd": "quality-loop",
    "env": {
      "PYTHONDONTWRITEBYTECODE": "1",
      "PYTHONPATH": ".",
      "TMPDIR": "<OUTPUT>/.review-e7wzazoe",
      "PYTEST_ADDOPTS": "-p no:cacheprovider"
    },
    "timeout": 900,
    "exit_code": 1,
    "duration_ms": 10919,
    "stdout": "............................................................F........... [ 41%]\n........................................................................ [ 82%]\n..............................                                           [100%]\n=================================== FAILURES ===================================\n_ ObservationTest.test_observe_git_changes_fails_gracefully_when_not_git_repo __\n\nself = <test_observation.ObservationTest testMethod=test_observe_git_changes_fails_gracefully_when_not_git_repo>\n\n    def test_observe_git_changes_fails_gracefully_when_not_git_repo(self) -> None:\n        with tempfile.TemporaryDirectory() as temp_dir:\n            non_git = Path(temp_dir)\n>           with self.assertRaises(QualityLoopError) as ctx:\nE           AssertionError: QualityLoopError not raised\n\ntests/test_observation.py:67: AssertionError\n=========================== short test summary info ============================\nFAILED tests/test_observation.py::ObservationTest::test_observe_git_changes_fails_gracefully_when_not_git_repo\n1 failed, 173 passed in 10.67s\n",
    "stderr": "",
    "stdout_sha256": "bf79e08fe7687210babf90013014dc1f3f9c8631fb8f08212d855340ef2fcf97",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "truncated": false,
    "id": "CHECK-SUITE-INITIAL",
    "required": false,
    "expected_exit_codes": [
      0
    ],
    "python_version": "3.12.3",
    "pytest_version": "7.4.4",
    "status": "FAIL",
    "note": "隔離配置の親Git探索によるReviewer実行条件不備。探索境界を設定したCHECK-SUITEで再実行。"
  },
  {
    "argv": [
      "pytest",
      "tests/test_sync_productivity_skills.py",
      "-q"
    ],
    "cwd": "quality-loop",
    "env": {
      "PYTHONDONTWRITEBYTECODE": "1",
      "PYTHONPATH": ".",
      "TMPDIR": "<OUTPUT>/.review-e7wzazoe",
      "PYTEST_ADDOPTS": "-p no:cacheprovider"
    },
    "timeout": 120,
    "exit_code": 0,
    "duration_ms": 801,
    "stdout": "......                                                                   [100%]\n6 passed in 0.58s\n",
    "stderr": "",
    "stdout_sha256": "83ef11ace12d1ef8964708e04e58196db7ea23f86721f1686aa707958b594b11",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "truncated": false,
    "id": "CHECK-RUNTIME-SYNC",
    "required": true,
    "expected_exit_codes": [
      0
    ],
    "python_version": "3.12.3",
    "pytest_version": "7.4.4",
    "status": "PASS",
    "note": ""
  },
  {
    "argv": [
      "openspec",
      "validate",
      "unify-qa-skill-workflow",
      "--strict",
      "--json"
    ],
    "cwd": ".",
    "env": {
      "PYTHONDONTWRITEBYTECODE": "1",
      "PYTHONPATH": ".",
      "TMPDIR": "<OUTPUT>/.review-e7wzazoe",
      "PYTEST_ADDOPTS": "-p no:cacheprovider"
    },
    "timeout": 120,
    "exit_code": 0,
    "duration_ms": 429,
    "stdout": "OpenSpec valid=true、issues=[]。root.pathの個人絶対パスのみ表示上置換。{\n  \"items\": [\n    {\n      \"id\": \"unify-qa-skill-workflow\",\n      \"type\": \"change\",\n      \"valid\": true,\n      \"issues\": [],\n      \"durationMs\": 27\n    }\n  ],\n  \"summary\": {\n    \"totals\": {\n      \"items\": 1,\n      \"passed\": 1,\n      \"failed\": 0\n    },\n    \"byType\": {\n      \"change\": {\n        \"items\": 1,\n        \"passed\": 1,\n        \"failed\": 0\n      }\n    }\n  },\n  \"version\": \"1.0\",\n  \"root\": {\n    \"path\": \"<OUTPUT>/.review-e7wzazoe/tree\",\n    \"source\": \"nearest\"\n  }\n}\n",
    "stderr": "",
    "stdout_sha256": "cd69625783159725fcb4d8bef6fc8c7128a39c6ddfc72b8cb066558385bf0416",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "truncated": false,
    "id": "CHECK-OPENSPEC",
    "required": true,
    "expected_exit_codes": [
      0
    ],
    "python_version": "3.12.3",
    "pytest_version": "7.4.4",
    "status": "PASS",
    "note": ""
  },
  {
    "argv": [
      "pytest",
      "tests",
      "-q"
    ],
    "cwd": "quality-loop/",
    "env": {
      "PYTHONDONTWRITEBYTECODE": "1",
      "PYTHONPATH": ".",
      "TMPDIR": "<OUTPUT>/.review-e6b8d80u",
      "PYTEST_ADDOPTS": "-p no:cacheprovider",
      "GIT_CEILING_DIRECTORIES": "<OUTPUT>",
      "OPENSPEC_TELEMETRY": "0"
    },
    "timeout": 900,
    "exit_code": 0,
    "duration_ms": 10254,
    "stdout": "........................................................................ [ 41%]\n........................................................................ [ 82%]\n..............................                                           [100%]\n174 passed in 10.01s\n",
    "stderr": "",
    "stdout_sha256": "dc5b11a4bdc8b7e6800203c825bcea6027c5310289c1fe312722314f3ddfa4a0",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "truncated": false,
    "id": "CHECK-SUITE",
    "required": true,
    "expected_exit_codes": [
      0
    ],
    "python_version": "3.12.3",
    "pytest_version": "7.4.4",
    "status": "PASS",
    "note": ""
  }
]
```

## 追加check契約Evidence

Python最低版とtypeを含む10種類について承認なし/正しい両hash付き承認ありの20拒否を確認。旧新hashなし・誤新hash・他契約hashも拒否。重複IDはStore.validateで拒否。非dict/unhashable IDは比較前schema validationがないため直接APIではTypeErrorになるが、状態変更・契約受理はなく、CLI mainはTypeErrorを捕捉しexit 2へ変換する（cli.py:main）。この依頼で確認した契約迂回はない。入力診断の統一は残余事項として記録し、要求外の修正を必須化しない。

任意check追加の成功例では旧hash `cda6296e7271dfd92a6ca1575bf48ba0aad0ec6cad15e216ca0f553809796586`、新hash `a82c0af9e935b48fe666d2da14313dea9e0925174472fb77381623afdcc58766`、diffはadded=[CHECK-EXTRA]/removed=[]/changed=[]。実際の契約と保存値が一致した。詳細matrixは[機械記録](03_machine.json)の `additional_evidence.required_contract_probes` に保持。

## 未検証事項・残余事項

実GitHubクラウド起動/公開、Python 3.10・他OS、secret/path scannerの全形式・検出精度は **unverified**。Windows/UNCの新規差分がないという静的確認を、これら形式のscanner機能保証へ読み替えない。追加fixtureはAPIと合成local bare remoteで実施したもので、productionへの操作はない。任意checkの変更/削除の全組合せは静的実装確認であり、独立動的matrixは任意追加のみ。

既存Cycle 2報告・依頼・ユーザー差分は保持。保存した成果物は本レビュー、tasks、machine JSON、STATUSの4ファイルのみ。次の行動はQA-C3-F01の契約と回復方針を実装担当/Ownerが判断し、明示承認された修正後の固定SHAで再QAすること。merge、外部配置、旧版削除、commit、pushをこのレビューから許可しない。
