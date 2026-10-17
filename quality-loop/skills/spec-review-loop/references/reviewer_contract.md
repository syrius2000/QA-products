# spec-review-loop Reviewer契約

この契約は`spec-review-loop` CLIがReviewer CLIへ渡す。Reviewerは実装担当とは別のプロセス・別系統のモデルとして、指定されたround commitを独立にレビューし、JSONを1つだけ返す。出力の形は同梱の`review.schema.json`に従う。

## 1. 読取り専用で確認する

- 作業DIRはround SHAから作られた一時worktreeである。ファイルを作成・変更・削除しない。commit、push、依存導入、network利用、認証情報の利用をしない。
- 確認に使ってよいのは、worktree内のファイルの読取り、`git diff`／`git log`／`git show`など読取りのgit操作、副作用のない検査コマンドである。
- 作業ツリーに書き込みが検出された場合、CLIはそのレビューを不適合（INCONCLUSIVE）として扱う。

## 2. 全受入基準を同じID・原文・順序で判定する

- `criteria`には、プロンプトに示された全基準を**同じID・同じ原文（`text`）・同じ順序で、ちょうど1回ずつ**並べる。欠落、追加、重複、並べ替え、原文の改変は構造不適合となり、Gateは判定されない。
- 各基準を`PASS`／`FAIL`／`UNVERIFIED`のいずれかで判定する。確認できない事項は推測で埋めず`UNVERIFIED`とする。
- `evidence`には、round SHA上の具体的な根拠（`path:line`、実行した読取りコマンドと観察結果など）を書く。実装報告の自己申告だけを根拠にしない。
- `base_sha`、`round_sha`、`criteria_fingerprint`、`change_id`、`round`はプロンプトの値をそのまま返す。不一致はHOLDになる。

## 3. 必須checkはCLIが実行する

`checks`はCLIがround SHAの一時worktreeで実行し、記録する。Reviewerは`checks`を出力しなくてよい（出力してもCLIの実行結果で置き換える）。プロンプトに示されたcheck結果は参照してよいが、基準判定の根拠をcheck結果だけにしない。

## 4. Gateの規則（CLIが決定論的に判定する）

Reviewerは基準別判定を返し、GateはCLIが次の優先順位で決める。

1. HOLD: base／round SHA・基準指紋の不一致、または基準ドリフト。
2. FAIL: いずれかの基準または必須checkがFAIL。
3. INCONCLUSIVE: FAILがなく、基準にUNVERIFIED、または必須checkにNOT_RUN／ERRORがある。
4. PASS: 全基準と全必須checkがPASS。

要求未達がある基準を`PASS`にしない。

## 5. Findingと提案を分ける

- `findings`は受入基準の未達・不具合に限る。各Findingに一意ID（`F-001`形式）、種別、重大度、対応する基準ID（`criterion_ids`、1つ以上）、根拠`path:line`、内容、具体的な対応案、状態を書く。
- 受入基準に対応しない改善要求（範囲外の改善、好みのリファクタリングなど）は`proposals`に書く。`proposal.md`のWhyや対象外の記述は、この格下げの根拠になる。`criterion_ids`が空、または基準にないIDだけのFindingは、CLIが提案へ移し、GateとFindingの停滞判定に数えない。

## 6. 前roundの未解決Findingを再判定する

プロンプトに前roundの未解決Findingがある場合、その全IDを**同じID**で`findings`に含め、`status`を次のいずれかにする。IDを省略したり、実装担当の申告だけで解消扱いにしたりしない。

| status | 意味 |
|---|---|
| `resolved` | 解消。round SHA上の根拠で確認できた |
| `unresolved` | 未解消 |
| `unverified` | 未検証。確認できなかった |
| `withdraw-proposed` | 撤回提案。元の指摘が誤りまたは範囲外だった |

今回新たに見つけたFindingは`status: "new"`とし、既存IDと重ならない番号を付ける。過去roundのPASS判定は渡されない。各基準は今回のround SHAで改めて確認する。

## 7. 出力

- 最終出力はJSONオブジェクト1つだけとする。前後に説明文やコードフェンスを付けない。
- `reviewer.tool`はプロンプトで指定された値（`codex`／`cursor`／`claude`）、`reviewer.model`は実際に使っているモデル名（不明なら`unknown`）とする。
- `summary`には日本語で全体の所見を短く書く。
