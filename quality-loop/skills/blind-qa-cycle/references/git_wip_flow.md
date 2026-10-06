# QA開始前準備と既存ブランチのWIPコミット連携

この手順は、既存の非default topic branchで事前にQA計画を固定する経路と、事前計画なしで実装済み差分をQAへ渡す経路を定めます。`prepare`の計画commitまたは`checkpoint` commitがBaselineとなり、後続Reviewed commitまでの差分だけを独立QAへ渡します。モード名は **`checkpoint` のまま**です（`setup`へリネームしない）。

Git状態に触れる前にread-only preflightを行い、root、branch、HEAD、upstream/default branch、staged・unstaged・untracked pathを記録します。既存変更をstage、stash、reset、clean、restoreで整理しません。今回対象・無関係・不明を分類し、対象外staged変更、unstaged/untracked混在、default branch、branchまたはbaseline不明ならcommitせず、人が指定した整理後に再確認します。clean基準点は別の隔離worktreeで作るか、対象WIPだけを明示されたcheckpoint契約で固定します。

```text
事前準備: clean topic branch → 00_plan.mdだけをYip commit (Blind-QA-Plan)
          → 実装 → staged-only Reviewed Yip → 同じcycleの00_invite.md
          → invite commit → (cloudのみ) topic-only push / path handoff

事後開始: stagedな作業前WIP → Yip checkpoint (Blind-QA-Checkpoint)
          → 実装 → staged-only Reviewed Yip → 新cycleの00_invite.md
          → invite commit → (cloudのみ) topic-only push / path handoff

どちらも Baseline..Reviewed の差分が審査範囲
```

事前準備経路では、計画commitがBaseline treeを作るため`00_plan.md`はレビュー差分へ含まれません。実装後のfinal inviteは同じcycleに追加し、BaselineとReviewedの完全SHAを固定します。事後開始では最新の同topic `Blind-QA-Checkpoint`をBaselineにし、見つからなければ停止します。

## `/blind-qa-cycle prepare`

1. `SKILL.md`のprepare modeに従い、cleanな非default topic branchでのみ実施します。
2. `00_plan.md`だけを `Yip: QA plan <topic> c<N>` / `Blind-QA-Plan: <topic>` としてcommitします。commit後の完全SHAがBaselineです。
3. この段階で製品差分・final inviteを作らず、fetch・push・reviewもしません。
4. 実装完了後、同じtopic、cycle、branchに対応するplan commitが現branchの祖先であることを確認してcloud/localのReviewedフローに渡します。条件不一致なら自動で別Baselineへ切替えず停止します。

## `/blind-qa-cycle checkpoint`

1. 現在のブランチが `main` / `master` ではないことを確認します。
2. 利用者が選んでステージしたファイルだけを対象にします。indexが空、未ステージ差分あり、未追跡ファイルありの場合は、コミットせず停止します。
3. 対象パスと差分概要を示し、明示的な `checkpoint` 起動に基づいてindexだけをコミットします。
4. commit subjectは `Yip: WIP QA checkpoint <topic>`、本文末尾の識別トレーラーは `Blind-QA-Checkpoint: <topic>` とします。
5. コミット後の完全SHAを表示します。これが同じtopicの通常 `cloud` QAでBaselineになります。
6. push・invite作成はしません。

## `/blind-qa-cycle cloud`

明示起動 `/blind-qa-cycle cloud` は、次を**一通貫**で許可します（main マージはしない）。

1. 現ブランチが `main` / `master` なら **fail-fast で停止**（確認による続行は不可。Reviewed/invite commit・push へ進まない）。
2. 同じtopic・cycleに対応する`Blind-QA-Plan`が現branchの祖先なら、それをBaselineにします。planに対応するcycleが一意でない、または祖先関係が確認できない場合は停止します。準備計画がない事後開始では、現ブランチのfirst-parent履歴から同じtopicの最新`Blind-QA-Checkpoint`をBaselineとして特定します。checkpointがなく、今回の明示cloud依頼で新しいtopic branchを作った場合に限り、branch切替前に記録した完全HEAD SHAをBaselineにできます。branchはそのSHAから開始し、Reviewedより前に他のbranch commitを作っていないことを確認し、inviteにsource branchと`branch_start`理由を記録します。その他の場合は停止します。Baselineをmerge-baseや無関係なQA cycleから推測してはなりません。
3. 今回の変更を利用者がステージし、未ステージ差分・未追跡ファイルがないことを確認します。ステージ済みならパス一覧と概要を示し、indexだけを `Yip: WIP QA review <topic>` でコミットし、`Blind-QA-Reviewed: <topic>` トレーラーを付けます。
4. 同topicのReviewedトレーラーを持つコミットが既にHEADなら再利用します。空コミットや重複コミットは作りません。
5. Prepared flowではplanのcycle DIRを再利用し、事後開始では次の未使用cycle DIR `docs/Artifacts/qa_cycles/<topic>/c<N>/`を選びます。Reviewedを固定した後に`00_invite.md`を作成します（inviteはBaseline..Reviewedに混ぜない）。既存inviteや凍結済みcycleは上書きしません。
6. invite ファイルだけをステージし、`Yip: QA invite <topic> c<N>`（trailer **必須** `Blind-QA-Invite: <topic>`）で追従コミットします。
7. **topic のみ** `git push -u origin HEAD` を実行します（この明示モードが認可）。force-push や main マージはしません。
8. preflight（Baseline / Reviewed が `origin/<branch>` の祖先）成功後、Cloud 手渡しは次の**相対パス1行**を既定とします。

   ```text
   docs/Artifacts/qa_cycles/<topic>/c<N>/00_invite.md
   ```

9. push または preflight に失敗した場合はローカルコミットを保持し、パス手渡しを主張せず、手動 push 手順と**本文フォールバック**を出して停止します。

## `/blind-qa-cycle cloud re-qa`

1. 現ブランチが `main` / `master` なら **fail-fast で停止**（`cloud` と同じ。確認による続行は不可）。
2. 凍結済み cycle（通常 HOLD/FAIL）の **Reviewed SHA** を Baseline 既定とします。新規 checkpoint は必須ではありません。
3. 修復後 tip を Reviewed とし、`c{N+1}` に invite を作り、通常 cloud と同じく invite コミット → topic push → パス手渡しへ進みます。
4. 前 cycle のファイルは変更しません。

## `/blind-qa-cycle respond <cycle>`

1. 凍結済みcycleの`02_tasks.md`から利用者が指定したFinding/taskだけを対象にします。Reviewer成果物、特に`02_tasks.md`のcheckboxや`03_machine.json`のstatusは変更しません。
2. 修正を利用者が認可した範囲で行い、変更対象外pathが混在する場合はコミットせず停止します。`main`/`master`では対応commitを作りません。
3. 変更pathだけがindexにあり、他のstaged/unstaged/untracked pathがないことを確認します。stage/cleanup/reset/restoreでユーザー状態を整理しません。
4. indexだけを `Yip: QA response <topic> c<N>` でcommitし、`Blind-QA-Response: <topic>` と `Blind-QA-Findings: <comma-separated IDs>` を付けます。
5. 対応commitはFindingを閉じません。前cycle ReviewedをBaselineにした新cycleへresponse SHAとFinding IDsを渡し、Reviewerの再確認を受けます。前cycleはimmutableのままです。

`respond`自体はpushしません。後続の`cloud re-qa`のみが明示起動で必要なtopic commitをpushできます。

## Review / ingest の成果物コミット

```text
cloud review（または ingest）
  → 現ブランチが main/master なら fail-fast STOP
  → Output dir に 01/02/03/STATUS のみ
  → Yip: QA review <topic> c<N>  + Blind-QA-Review-Artifacts
  → topic-only push
```

- `00_invite.md` と製品ツリーは変更しません。
- `main` / `master` では artifact commit も push もしません（確認による続行不可）。
- push できない Cloud は4ファイルを返し、依頼側が `/blind-qa-cycle ingest` します（ingest も非-main topic 限定）。

## 保護条件

- 明示的な`prepare`で許可される計画commitは新規`00_plan.md`だけです。`checkpoint` / `cloud` / `respond`で許可されるcommitは確認済みの既存indexだけです。
- `git add -A`、暗黙のstage、unstaged/untrackedを含む製品コミット、変更の破棄は行いません。
- `prepare`の計画commitは`00_plan.md`だけ、`cloud`のinvite追従commitは`00_invite.md`だけをstageしてよいです。
- `review` / `ingest` の成果物コミットに限り、Output dir の4ファイルだけをステージしてよいです。
- index以外に変更がある場合は、対象ファイルを利用者が整理・stageした後に再実行します。
- ブランチ作成、commit修正、reset、rebase、main マージ、force-pushはこのフローに含めません。
- QA成果物（invite / review artifacts）はReviewedコミット確定後に作成するため、レビュー対象差分へ混入しません。
- topicを変えて同じブランチでQAする場合は、新しいtopicのチェックポイントを作ります。
- 実装前に受入基準を固定できる新規作業では`prepare`を使います。すでに実装済みならcheckpointでBaselineを固定します。Re-QA（`cloud re-qa`）では前回ReviewedをBaselineにできるためcheckpoint再取得は必須ではありません。

## Git上の確認

```bash
git show -s --format='%H%n%s%n%b' <commit>
git diff --name-status <baseline> <reviewed>
git diff --stat <baseline> <reviewed>
```

トレーラーはコミット履歴に残り、別cloneでもSHAとともに追跡できます。invite と review 成果物はトピックブランチ上の別コミットとして保存します。
