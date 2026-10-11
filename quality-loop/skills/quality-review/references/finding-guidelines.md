# Reviewer Finding 作成ガイドライン

statusやhandoffで検証状況を説明するときは、case revision、`baseline.target_revision`（評価対象版）、cycleを区別して記録に沿って示す。Finding単位の`verified`／`not-verified`等を案件全体の受入や総合QA Gateへ読み替えず、Owner裁定待ちを独立した状態として保つ。

Final Risk AssessmentのReviewer評価勧告は`accept`＝受入推奨、`accept-with-conditions`＝条件付き受入推奨、`require-remediation`＝修正要求推奨、`defer`＝判断延期推奨として区別し、元コードを保持する。これらはOwner裁定ではない。受入基準別の`PASS`／`FAIL`／`UNVERIFIED`および実行checkの`PASS`／`FAIL`／`NOT_RUN`／`ERROR`を参照する場合も、各対象revision/cycleに結び付け、勧告・Finding結果・Owner判断と混同しない。テキスト表示の既定は日本語、英語の選択は`--lang en`とし、表示だけを切り替える。

## 1. Findingの必須5要素
Findingを作成する際は、主観や動機を排除し、以下の5要素を必ず揃えて記述します。

1. **要求参照 (`requirement_ref`)**: どの要求・受入基準・Purposeに対するリスクか
2. **観測された事実 (`observed_fact`)**: 成果物・実行結果から直接観測された客観的事実
3. **品質への影響 (`impact`)**: その事実が放置された場合に生じる具体的な不都合
4. **本来あるべき状態 (`expected_state`)**: 要求を満たすために目指すべき状態
5. **検証・再現方法 (`verification_method`)**: 第三者が確認・追試できる具体的な手順

## 2. 品質目標を勝手に上げない（不適合 vs 改善提案の厳格な分離）
- **不適合 (`requirement-violation`)**: Ownerが定めたBaseline（要求・受入基準）に明確に反するもの。
- **改善提案 (`improvement-proposal`)**: 要求仕様の範囲外だが、保守性や可読性を高めるためのアドバイス。
  - **重要**: 改善提案はImplementerの対応を強制せず、案件の受入を妨げてはならない。
