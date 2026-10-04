# 対象確定とクラウド公開

まず対象ファイル一覧・内容、開発ブランチ、remote、送出commit一覧を表示する。対象リポジトリの承認規則と実際のユーザー指示を確認する。準備だけの指示をcommitやpushへ広げない。分離できないindex・無関係な送出履歴・分岐があれば具体的な条件を示す。

ローカルで対象を確定する:

```text
quality-qa-cli finalize --request QA-001 --message "この対象をローカルでcommitして" --approved-path src/product.py
```

`--message` は実際のユーザー発言。表示集合の全パスを `--approved-path` に渡す。対象外indexと差分を保持する。ユーザー自身がcommitした場合は `finalize --commit <完全SHA>` で下書きとの一致を検査する。どちらもpushしない。

クラウドへ公開する:

必須checkがある場合は、依頼固定snapshotのまま次を実行し、全必須checkの成功Evidenceを記録する。コマンドはshell経由でなく、依頼に固定したargv配列で実行する。結果がFAIL/ERROR/NOT_RUN、または検査後に製品snapshotが変わった場合は公開を停止する。

```text
quality-qa-cli verify --request QA-001
```

公開直前に、招待文と製品対象snapshotの機密情報・秘密鍵・個人ローカルパス検査を行う。検出、固定snapshotとの不一致、またはcheck Evidenceのhash不一致があれば、commit/pushを開始しない。テスト用の値は `API_KEY=test-token` や `/Users/qa-user/...` のような明示的な合成fixtureだけを例外として扱い、実値らしい秘密情報は通過させない。

```text
quality-qa-cli publish --request QA-001 --message "クラウドQAに出して" --approved-path src/product.py --approved-path docs/Artifacts/qa_invite_001_MMDD.md
```

製品対象と依頼パスだけを指定する。再QAで既存check契約を削除・任意化・変更したりcheckを追加したりする場合は、利用者が検証契約変更を明示承認し、その実際の発言を `--check-contract-approval` へ渡す必要がある。単なる再QA依頼だけでは変更できない。対象commitの後、そのSHAを参照する依頼を別commitへ保存する。既存対象commit・途中作成commitは再利用する。remote tipへの到達可能性が確認できた後で、ユーザーへGitHub上の依頼相対パスと手渡し方法を返す。公開はレビュー実行ではない。ユーザーが手渡したら `handoff` を記録する。

公開失敗時は作成済みcommitを保持し、同じ操作を再試行する。リモート先行分は登録したレビュー成果物だけ・祖先関係あり・既存差分保持可能の場合に限ってfast-forwardする。製品変更混在や分岐は別の統合判断へ戻る。既定ブランチ公開、force-push、stash、reset、cleanは行わない。

訂正依頼は本文手渡しで使える。GitHubへ保存する実際の指示がある場合だけ `publish-correction --message <実際の発言> --approved-path <予約された訂正依頼>` を使う。原レビューを上書きしない。
