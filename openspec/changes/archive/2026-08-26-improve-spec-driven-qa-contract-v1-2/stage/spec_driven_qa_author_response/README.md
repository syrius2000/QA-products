# Spec-Driven QA Author Response

`spec-driven-qa-author-response`は、`spec-driven-qa-review`が作成したQAケースを実装者AIが受領し、Findingごとの回答と修正提出を記録するCompanion Skillです。

このSkillはQAの独立判定を行いません。回答者はFindingを閉じず、`cycle-01-author-response.md`を追加して別レビュアーへ返します。

親Skillの正本テンプレートは`spec-driven-qa-review/templates/author-response.md`です。このパッケージはテンプレートを複製せず、親Skillのバージョンを確認して利用します。

実行時依存はPython標準ライブラリのみです。PyYAMLは開発・テスト用の任意依存です。
