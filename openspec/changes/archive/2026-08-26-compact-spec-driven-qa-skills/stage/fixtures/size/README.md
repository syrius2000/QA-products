# サイズ計測Fixture

このFixtureは、`stage/scripts/measure_size.py`の計測条件を固定するための最小資産である。

- 空行は物理行として数える。
- コメント行も配布物に含まれる場合は数える。
- テスト、サンプル、SchemaはManifest対象である限り数える。
- `__pycache__`、`.pytest_cache`、`*.pyc`は除外する。
- `SKILL.md`は常駐対象として別集計する。
- 出力JSONは相対パス、ファイル数、bytes、行数、カテゴリ、SHA-256を含む。
