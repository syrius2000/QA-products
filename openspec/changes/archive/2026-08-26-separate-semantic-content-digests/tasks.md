## 1. 契約と入力モデル

- [x] 1.1 semantic digestの正規化入力（case ID、未解決Finding、revision、状態・次アクション）を定義し、仕様の項目表とfixtureで検証する
- [x] 1.2 content digestの対象文書、正規化規則、除外対象を定義し、同一内容の表現差が同一digestになるテストで検証する
- [x] 1.3 semantic/content digestの型、version、エラーコードを共有coreの公開契約として定義し、未知versionを拒否するテストで検証する

## 2. 共有コア実装

- [x] 2.1 semantic digestを意思決定構造から決定的に算出し、意味フィールド変更で値が変わるテストを通す
- [x] 2.2 content digestを正規化文書内容から決定的に算出し、本文だけの変更で値が変わるテストを通す
- [x] 2.3 同一入力では両digestを再現し、意味変更と内容変更で少なくとも一方が区別できることをfixtureで確認する

## 3. Reviewer/Author相互運用

- [x] 3.1 Reviewer handoff生成を両digest契約へ接続し、正本から再計算した値がhandoffに保存されるテストを通す
- [x] 3.2 Author submission検証を両digest照合へ接続し、stale・意味変更・内容変更を異なる診断で拒否または保留するテストを通す
- [x] 3.3 Reviewer生成handoffをAuthorが検証・保存できるclosed混在および複数cycle fixtureで確認する

## 4. 互換性と安全境界

- [x] 4.1 旧同値digestを読み取り専用履歴として検出し、新Contractの検証済みhandoffとして受理しないテストを通す
- [x] 4.2 digest不一致時にFinding、events、closure、正本を変更しないことをnegative testとファイル差分で確認する
- [x] 4.3 秘密値、絶対パス、外部参照をdigest入力へ混入させない検査を追加し、秘密値を含むfixtureで拒否を確認する

## 5. EvidenceとQA完了境界

- [x] 5.1 標準ライブラリのみの回帰テストをcache-freeで実行し、結果とdigest fixtureをEvidenceへ保存する
- [x] 5.2 Reviewerによる独立QAでF06のcontent-onlyシナリオ、旧形式、stale拒否を検証し、QA-0006へ提出する
- [x] 5.3 QA-0006の人間裁定を更新し、残余リスク、未検証項目、再レビュー条件を明記する（Authorが自己クローズしない）
- [x] 5.4 外部Skill配置、旧版削除、commit、pushを行わず、配備は別Changeへ引き継ぐことを確認する
