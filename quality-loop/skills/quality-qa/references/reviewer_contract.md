# 独立Reviewerの実施・返却契約

## 独立して確認する

実装担当とは異なるReviewerとして、依頼に固定されたrepository・Baseline SHA・Reviewed SHA・全受入基準・対象集合を確認する。実装担当AIの説明や過去のPASSを根拠の代わりにしない。まずReviewed SHA内の `quality-loop/skills/quality-qa/SKILL.md` と本契約を読み、依頼に記されたSHA-256を照合する。どちらかが読めない、対象SHAが取得できない、またはhashが一致しない場合はHOLDとして理由を記録する。

SHA-256は対象commit内の各ファイルのraw bytesに対して計算する。改行変換、文字コード変換、Markdown正規化を挟まず、依頼記載値・commit tree内容・Reviewerが取得した内容を照合する。

対象差分はBaselineからReviewedまでの全変更を調べ、初回基準からの要件と周辺影響も確認する。依頼に記された製品pathを個別に確認し、登録運用成果物と対象外判断を混同しない。ディレクトリ単位で製品文書を除外せず、renameは旧path・新pathの両方を確認する。変更仕様に関係する実行可能な確認は対象環境で実行する。Python、pytest等が既に利用可能で、リポジトリ規則が許せば使う。無許可の依存導入、ネットワーク利用、認証情報利用は行わない。

## 一つのMarkdownだけを提出する

書き込んでよい成果物は依頼の「保存先」に指定された日本語Markdown一つだけである。製品コード、QA依頼、runtime状態、他のArtifactを変更しない。Quality QA管理CLI、JSONファイル、旧blind QAの4成果物は作成しない。返却Markdownにレビュー本文、全受入基準の照合、詳細Evidence、Finding、実施側タスク、前回Findingの再確認、残余事項をまとめる。

返却先を変更したい場合は、依頼者へ先に連絡し指定を受ける。GitHub上でのブランチ・PR返却やcommit/pushは対象リポジトリの規則と依頼にある明示許可に従う。製品変更をmergeしない。

## 全受入基準を照合する

依頼にある各 `AC-NNN` を同じID・原文・順序で「受入基準の照合」へすべて列挙する。各基準を `PASS`、`FAIL`、`UNVERIFIED` のいずれかで判定し、Reviewed SHA上の具体的な根拠を記す。欠落、追加、重複、並べ替え、原文改変をせず、要件指紋を補助識別値として保持する。

依頼に構造化checkがある場合、check ID・種類・必須性・argv・cwd・env・timeout・期待終了値を保ち、status・runtime・exit code・duration・stdout/stderr excerptとSHA-256・切詰め有無をEvidenceへ記録する。Gateは次の優先順位で決める。(1) 対象SHA、依頼ID、参照資材hashなどprovenanceが不一致・確認不能ならHOLD。(2) provenanceが有効で、いずれかの受入基準または必須checkがFAILならFAIL。(3) 既知のFAILがなく必須checkにNOT_RUN/ERRORがある場合はINCONCLUSIVE。(4) それ以外で全受入基準と必須checkがPASSした場合だけPASSとする。FAILと必須checkのERROR/NOT_RUNが併存してもFAILを保持し、各check状態・理由を個別に記録する。任意checkの未実施は理由付きで未検証事項へ残す。

PASSは全受入基準と全必須checkがPASSの場合だけ選ぶ。要求未達または重大な未解決FindingとPASSを併記しない。確認できない事項は推測で埋めず、UNVERIFIEDまたはHOLD/INCONCLUSIVEとして扱う。

## Findingと実施側タスクを結ぶ

Findingごとに一意ID、種別（要求未達・不具合・改善提案・未検証）、重大度、状態、要求との対応、根拠 `path:line`、影響、具体的対応案、対象path、完了条件、検証方法を記録する。修正や追加確認が必要なOPEN Findingには、Finding IDを参照する実施側タスクを付ける。改善提案を受入基準へ格上げせず、仕様外の改善を必須修正にしない。

再QAでは前回の全未解決FindingをIDごとに列挙し、`解消`、`未解消`、`未検証`、`撤回提案` のいずれかとReviewed SHA上の具体的根拠を記す。IDの省略や実装担当の自己申告だけで解消扱いにしない。

## 返却前チェック

- 依頼ID、cycle、Baseline/Reviewed SHA、要件指紋、提出版、訂正情報、保存先が依頼と一致する。
- 参照Skill・出力契約のhashを照合した結果を記録する。
- 全受入基準を依頼と同じID・原文・順序で一度ずつ含める。
- 必須checkとGate、Findingと実施側タスク、前回FindingとEvidenceの間に矛盾がない。
- 指定保存先の一つのMarkdownだけを変更し、他のファイルと製品コードを変更していない。
- 出力は日本語とし、JSTのcreated/update、実際のReviewerツール・モデル名を記載する。
