# 本番Skill配備準備計画

created: 2026-08-26 01:13 (JST)
update: 2026-08-26 01:13 (JST)
author: Codex (GPT-5)

## 1. 目的

QA-0003で受入済みとなったstaging Bundleを、既存Skill利用環境へ安全に配置できる手順と検証条件を定義する。計画作成時点では外部Skill環境へ書き込まない。

## 2. 対象

- 配備候補: `/Users/myamaguchi/.gemini/config/skills/spec-driven-qa-review`
- 配備候補: `/Users/myamaguchi/.gemini/config/skills/spec-driven-qa-author-response`
- 参照Bundle: リポジトリ内の`openspec/changes/compact-spec-driven-qa-skills/stage/spec-driven-qa-bundle/`
- 対象外: 旧版の即時削除、Contract v1.2候補の受入、commit、push

## 3. 実施手順（承認後）

1. 配備対象・現在の実ファイル・Manifest・シンボリックリンクを読み取り専用で再確認する。
2. 対象Skillごとにタイムスタンプ付きバックアップを作成し、バックアップのファイル一覧とSHA-256を保存する。バックアップ失敗時は停止する。
3. dry-runで全差分、追加・変更・削除予定パス、外部参照、Manifest外の対象を表示する。差分に予期しないパスがあれば停止する。
4. 明示承認後、Manifestに記載された対象だけを一時配置へ展開する。配置先の親ディレクトリや無関係なSkillは変更しない。
5. 配置後にLauncher、Manifest digest、役割Firewall、JSON出力、終了コード、cwd非依存性を検証する。
6. 旧版読み取り互換性とAuthor/Reviewerの最小完全サイクルを確認する。失敗時は配置を受入済みと報告しない。
7. 検証失敗または利用不能時は、バックアップから対象Skillだけを復元し、復元後のManifest・Launcher・読み取り互換性を再確認する。

## 4. 停止条件

- バックアップの作成またはハッシュ記録に失敗
- Manifest差分と実ファイル差分が一致しない
- 外部Skill以外のパスが変更対象に含まれる
- Launcherのdigest検証、役割Firewall、終了コードが不一致
- ロールバック手順が再現できない

## 5. 承認境界

このArtifactは手順計画であり、配備・バックアップ・外部ファイル変更を実行する承認ではない。実施には、対象パス、バックアップ先、実行時刻、ロールバック担当を指定した明示承認が必要である。
