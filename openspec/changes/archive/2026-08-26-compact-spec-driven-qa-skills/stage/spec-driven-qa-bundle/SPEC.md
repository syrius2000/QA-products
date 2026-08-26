# spec-driven-qa Bundle詳細仕様

## 分類

Findingの重大度は`critical`、`high`、`medium`、`low`とする。Findingの状態は`open`、`accepted`、`fix-submitted`、`fixed-and-verified`、`risk-accepted`、`not-applicable`とする。

## Evidence

Evidenceは`verified`、`unverified`、`evidence-gap`、`risk-accepted`、`fixed-and-verified`を区別する。`unverified`または`evidence-gap`はOwnerの明示判断なしに`fixed-and-verified`へ変換しない。

## 状態遷移

`open`から`review`または`handoff`、`needs-response`から`respond`または`submit`、`verification-in-progress`から`verify`または`close`を許可する。`closed`からの操作は許可しない。

## 安全規則

- ReviewerとAuthorの操作を共有コアで再認可する。
- handoffのcase revision、semantic digest、content digestが正本と一致しない提出は拒否する。
- AuthorはReviewer正本、イベント、closureへ直接書き込めない。
- 未知major、Manifest不整合、共有コア欠落、未検証リンクはfail-closedとする。
- `file://`、秘密値、内部Tokenを診断出力へ出さない。
- 外部Skill配置、旧版削除、commit、pushは明示承認まで実行しない。

## 参照実装

契約は`schemas/contract.json`、共有実装は`shared_core/`、役割入口は`spec-driven-qa-review/SKILL.md`と`spec-driven-qa-author-response/SKILL.md`を参照する。判定正本はOpenSpec Changeの`spec.md`であり、この文書はBundle内の派生詳細仕様である。
