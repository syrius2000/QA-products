## Context

動機は [proposal.md](proposal.md) を、振る舞い契約は [specs/reviewer-verification-integrity/spec.md](specs/reviewer-verification-integrity/spec.md) および [specs/spec-driven-qa/spec.md](specs/spec-driven-qa/spec.md) を正とする。

現状（実装起点）:

- Reviewer lifecycle の stage 実装は `openspec/changes/spec-driven-qa-reviewer-case-lifecycle/stage/` にあり、QA-0004 で条件付き受入済み。
- `verify_submission` は revision／自己クローズ／未知 Finding／非空 `test_evidence` を検査するが、`test_evidence` のパス実在は未強制。`modified_files` は指定時のみ存在確認（欠落・空を契約要求として拒否しない）。
- `render_handoff` は正本から digest を書き出すが、verify 時に正本再計算との照合（stale digest 拒否）と専用 negative テストが無い（QA-0004 C2/C3）。

制約:

- Schema・digest アルゴリズム・revision 意味は共有基盤から変更しない（照合を追加するだけ）。
- 実装・検証は Change 配下（または明示した stage パス）に限定。外部 Skill 配備・旧版削除・commit／push は行わない。
- 実行時依存は Python 標準ライブラリのみ。

## Goals / Non-Goals

**Goals:**

- verify 経路で stale digest／欠落 Evidence パス／不正または欠落 `modified_files` を機械的に拒否する。
- 上記の golden／negative 自動テストを追加し、task／Evidence の完了表記を実測に合わせる。
- 共有コアの digest 計算を再利用し、handoff 生成と verify の照合式を一致させる。

**Non-Goals:**

- Author Response 生成・Author Firewall の本実装（別 Change）。
- tokens／latency 指標の計測（QA-0004 C4／Contract v1.2）。
- 外部配備・dry-run・rollback。
- handoff 手編集の「修復的受理」（再生成要求のみ）。

## Decisions

### 1. 実装ホームは既存 Reviewer stage を直接 hardening する

- 主変更点: `spec-driven-qa-reviewer-case-lifecycle/stage/spec-driven-qa-review/lifecycle.py` の `verify_submission`（必要なら digest 再計算ヘルパを同 Bundle 内に追加）。
- テスト: 同 stage の `tests/` に stale digest／Evidence パス／`modified_files` の negative・golden を追加。
- 本 Change 配下には proposal／specs／design／tasks／Evidence を置き、コード差分の正本は既存 stage とする（二重コピーによるドリフトを避ける）。
- 代替案「本 Change に stage を再複製」は QA-0004 実装との二重管理コストが高いため不採用。

### 2. stale digest 照合は handoff 生成と同一入力で再計算する

- verify 時: 現行正本（少なくとも open Finding ID 集合と cycle／case_id など、現行 `render_handoff` が `content_digest` に渡している入力）から digest を再計算し、handoff.md 上の `content_digest`／`semantic_digest` と文字列一致させる。
- 不一致は即拒否（正本・Finding 状態を更新しない）。`semantic` と `content` が現状同一値でも、両フィールドを独立に照合し、将来の分離に備える。
- 代替案「Author Validator のみに任せる」は Reviewer verify が偽陽性を出し得るため不採用（spec は Reviewer 経路でも MUST）。

### 3. Evidence パス判定はヒューリスティック、非パスは非空のみ

- `test_evidence` 文字列が「リポジトリ相対パスらしい」場合のみ実在検査する。判定例: `/` または `.` を含み、空白行でなく、絶対パス／`file://` は受理しない（既存 `spec-driven-qa` の相対パス規則に合わせる）。
- パスらしいが欠落 → 拒否。パスらしくない非空記述 → 実在検査スキップ（従来の非空必須を維持）。
- 代替案「常にパス必須」は既存テストの自由記述 Evidence を一括破壊するため、本 Change では採らない。

### 4. `modified_files` は「列挙時は全実在」かつ「fix 提出では非空必須」

- 列挙がある場合: 全パスがワークスペース上に存在すること（現行ループを維持・強化）。
- `fix-submitted` 相当（Finding 技術検証を進める提出）では、`modified_files` 欠落または空配列を拒否する。文書のみの disposition を別途許す場合は明示フィールドで分岐し、黙って空を成功にしない。
- 存在確認の基準ディレクトリはケース／リポジトリルートを design 実装時に固定し、テストで相対解決を再現する。
- 代替案「常に任意」は QA-0004 C3 と新 spec に反するため不採用。

### 5. 共有コア契約は読取再利用のみ

- digest 関数・authorization・Schema ファイルの意味変更はしない。
- shared_core への改変が避けられない場合は、改変内容と digest 差分を Evidence に明示し、「アーカイブ一致」を主張しない（QA-0004 C1 の延長）。

### 6. 完了表記と独立検証

- tasks／capability 表は、自動テストが通った項目のみ完了。未達は `evidence-gap`／`unverified`。
- 外部配備なし。独立 QA は本 Change の pytest negative／golden と、必要なら短いプローブ記録で足りる。

## Risks / Trade-offs

- [パス判定の誤分類] → Mitigation: ヒューリスティックを狭く定義し、境界ケースをテスト。曖昧なら非パス扱い（実在未強制）より「拒否」を優先しないが、偽陽性成功を増やさないよう文書で境界を固定する。
- [既存 golden が自由記述のみで通っていた提出が、`modified_files` 必須化で落ちる] → Mitigation: テスト fixture を更新し、本番相当の提出形を正とする。
- [digest 入力の将来変更で手off／verify が乖離] → Mitigation: 再計算を単一ヘルパに集約し、handoff 生成と verify が同じ関数を呼ぶ。
- [lifecycle Change 未アーカイブとの並行編集] → Mitigation: 本 hardening は verify／テストに限定し、lifecycle の他責務を広げない。

## Migration Plan

1. stage 上で verify 厳密化とテスト追加。
2. Evidence（pytest 出力、negative 一覧）を本 Change に記録。
3. QA-0004 C2/C3 の消化状況をメモし、条件付き受入の再レビュー条件を更新可能にする。
4. rollback: stage の verify／テスト差分を戻すだけ（外部 Skill 非変更のため影響範囲はリポジトリ内）。

## Open Questions

なし（パス判定の具体正規表現は tasks 実装時にテストで固定すればよく、spec の WHEN/THEN は変えない）。
