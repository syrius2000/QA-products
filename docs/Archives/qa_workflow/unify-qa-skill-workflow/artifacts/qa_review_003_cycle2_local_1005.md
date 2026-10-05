# QA-003 Cycle 2 ローカル独立レビュー

記録日: 2026-10-05 (JST)
取得元: ユーザー提供のローカル独立Reviewer結果
注記: Cycle 1の原レビューは変更せず、本書をCycle 2の別記録として保存する。Reviewer名は提供本文に記載なし。

## 総合Gate: HOLD

レビュー対象の固定・隔離は確認できました。必須checkはCycle 2 baseline、Reviewed SHAの両方で成功しました。一方、Reviewed SHAにあるReviewer契約のSHA-256が依頼記載値と一致しません。依頼の規定に従い、この不一致だけでGateはHOLDです。加えて、QA-F01とQA-F02には未解決事項が残ります。PASSとは判定しません。

## 対象確認

- ブランチ: `codex/unify-qa-skill-workflow`
- Initial baseline: `ad6ca1ee196bd75bed026858c2de9586ca49c85c`
- Cycle 2 baseline: `d9bad5c125791306e38bca8830b4082f7f38fc6b`
- Reviewed SHA: `17bd3e7a3d81842bb5906ac7ab25329ec0be4ffb`
- baselineはReviewed SHAの祖先であり、指定SHAとtreeを照合しました。対象treeは`/tmp`へ展開して確認し、共有worktreeの未コミット変更・未追跡ファイルはレビューに含めていません。
- Cycle 2差分: 33パス、4,211追加行、77削除行。renameなし。
- 依頼指定のQA Skillはhash一致。Reviewer契約は不一致です。

| 資材 | 依頼記載SHA-256 | Reviewed SHAでのSHA-256 | 判定 |
|---|---|---|---|
| `quality-loop/skills/quality-qa/SKILL.md` | `57bb58973476cb503c35ea2981c55908c245d8c6e34972385e4c987740bdc261` | 同左 | 一致 |
| `quality-loop/skills/quality-qa/references/reviewer_contract.md` | `9a1b4460e0454f8aba7749a9460d91dc9b888048ddf204b6f6be0ceec5112efb` | `84f11def7f338acbf91362bbd8ad62834cd195383830a8684ec7ec7f4d3bf8cc` | 不一致 |

## 受入基準

| 基準 | 判定 | 根拠 |
|---|---|---|
| AC-001 | PASS | `gitops.status_preflight`がbranch、HEAD、upstream/default branchとstaged・unstaged・untrackedを取得し、dirty状態で安全な操作を止める実装を確認。 |
| AC-002 | PASS | `prepare`が初回・今回baseline、reviewed SHA、対象snapshotを固定し、後続HEADの差し替えを防ぐ処理を確認。 |
| AC-003 | PASS | 依頼とレビューの基準全文を比較するparser処理を確認。 |
| AC-004 | PASS | 必須check契約に従い両SHAでpytestを実行。結果は後記Evidenceのとおり。 |
| AC-005 | 未解決 | 公開時の対象snapshot検査、内容走査、必須check Evidence照合、対象パス制限を確認。一方、公開処理前の依頼文検査は後続処理で依頼文が更新された版まで結び付いておらず、QA-F01が残る。 |
| AC-006 | HOLD | review parserは識別・基準・Finding・タスク等を検査する。Reviewer契約資材のhash不一致のため、指定出力契約を対象SHA上で確定できない。 |
| AC-007 | PASS | 承認済み計画のhash/pathと提出snapshotを確認する処理を確認。 |
| AC-008 | 未解決 | 再QAは前回基準・履歴を引き継ぐ。ただしcheck契約は入力された承認文の簡易パターン一致で変更可能で、必須checkの削除・弱体化を防ぐ強い拘束は確認できない。QA-F02が残る。 |
| AC-009 | PASS | 自動merge・deploy・closeを行わず、人の終了判断を残す仕様・実装を確認。 |
| AC-010 | PASS | legacy経路を読み取り用途に限定し、新契約の状態を変更しない構成を確認。 |

## Cycle 1 Findingの再確認

- **QA-F01 — 未解決（OPEN）**
  `workflow.py`は公開時に製品対象と依頼文を走査し、check Evidenceを製品snapshot・check契約hashに照合します。しかし走査対象の依頼文は、公開フロー内で正式化される前の内容です。その後に依頼文が更新されてから送出されるため、最終送出本文に対する走査Evidenceがありません。修正後の依頼本文を走査し、その内容hashをcommit対象へ結び付ける必要があります。
- **QA-F02 — 部分対応・未解決（OPEN）**
  check契約が変更されるとき、既存契約との比較と承認文のパターン検査があります。しかし承認文は所定語句を含めば通り、必須checkを維持する検査も契約差分の制約もありません。したがって、再QA入力で必須契約を削除・弱体化できる余地が残っています。
- **QA-F03 — 解消を確認**
  Gate判定はprovenance不備をHOLD、確認済みFAILをFAIL、必須check未完了をINCONCLUSIVEの順で決め、理由を別々に検証します。FAILと必須check ERROR/NOT_RUNの併存を受け入れられる実装になっています。
- **QA-F04 — 解消を確認**
  配布templateに参照資材hash行と「実施側タスク」節があります。Cycle 1で指摘されたtemplateとparserの形式乖離は修正されています。
- **QA-F05 — 解消を確認**
  履歴とPlan 033は、対象treeに存在しない退避先を退避済みと記載せず、計画ごとの所在と未検証状態を明示しています。provenance文書の相対リンク先も存在します。
- **QA-F06 — 解消を確認**
  Cycle 1の対象SHAとCycle 2 Reviewed SHAの双方で、指定pytestを実行でき、exit code 0でした。Evidenceは後記のとおりです。

## 必須check Evidence

実行環境はPython 3.12.3。stdout/stderr hashは完全出力のSHA-256です。stderrはいずれも空でした。

| Check／対象 | argv・cwd・env・timeout | 結果・所要時間 | stdout SHA-256 |
|---|---|---|---|
| CHECK-PYTHON／Reviewed SHA | `["python3", "--version"]`、cwd repository root、env `{}`、30秒 | exit 0、6 ms、`Python 3.12.3`、PASS | `5b3e43dc38ca01e3f5a7854ba50d4330864b0c1e0f646650b2c78cf072acc366` |
| CHECK-QUALITY-LOOP／Reviewed SHA | `["pytest", "tests", "-q"]`、cwd `quality-loop/`、env `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=.`、900秒 | exit 0、9,938 ms、173 passed、PASS | `ba8e9db601c7949abf3b0b6a2e4e3fa4fc605947b6c98cc31c9e4ada4b8b7245` |
| CHECK-QUALITY-LOOP／Cycle 2 baseline | 同上 | exit 0、8,889 ms、163 passed、PASS | `4eae08ac82039283acd984fdfc4b9b6255219dba0695f34653709b9649d726b1` |

全checkのstderr SHA-256は`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。出力は切り詰めず取得しました。Reviewed SHAでのPython stdoutは`Python 3.12.3\n`、pytest stdoutは`173 passed in 9.56s\n`。baseline pytest stdoutは`163 passed in 8.63s\n`です。

## 未検証事項・残余リスク

Reviewer契約のhash不一致により、依頼指定の出力契約がReviewed SHA上の資材と同一であることを確認できませんでした。これはHOLD理由として残します。QA-F01・QA-F02も未解決です。実際のGitHub公開運用、複数OSでの動作、内容走査の検出精度はこのレビューでは検証していません。

レビューは本文返却です。共有worktree上のコード、QA状態、OpenSpec成果物は変更せず、commit・push・外部配置も行っていません。
