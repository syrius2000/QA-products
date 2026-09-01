# 設計判断

created: 2026-09-01 22:00 (JST)
update: 2026-09-01 22:00 (JST)
author: Codex (GPT-5)

QA-productsを開発正本として保存し、Productivity-Skillを利用成果物の置き場とするための設計・方針判断です。

## 判断記録

- [Archive方針ADR](../adr/0001-repository-document-archive-policy.md): ルート文書、Archive、公開Git履歴の境界
- [Quality Loop設計記録](../quality-loop/): 現行Quality Loopの実装・QAに関係する設計記録
- [旧spec-driven-qa設計記録](../spec-driven-qa/design/): 現行版へ至る前の設計検討と比較資料

## 現行の境界

- QA-products: 開発正本、検証、開発史、設計判断を保持する
- Productivity-Skill: 実務者が利用する2つのSkillだけを`.agents/skills/`直下に保持する
- Productivity-Skill側に開発史、内部QA、同期スクリプトを持ち込まない
- 確定版の同期元・同期先・版・日時・SHA-256はQA-products側で追跡する
