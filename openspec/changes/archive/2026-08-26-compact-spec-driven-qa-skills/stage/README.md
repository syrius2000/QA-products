# コンパクト化ステージングBundle

このディレクトリは、`compact-spec-driven-qa-skills`の実装・検証をリポジトリ内で行うための隔離領域である。

- 外部Skill配置先は読み取り専用の基準対象であり、このChangeから直接変更しない。
- `baseline/`は読み取り専用ベースライン、`scripts/`は標準ライブラリのみの計測・台帳生成、`fixtures/`は検証入力である。
- `manifest.json`の`allowed_write_root`外へ書き込む配備処理は、設計上fail-closedとする。
- backupとrollbackは外部配備前の必須ゲートであり、現時点では未作成・設計のみである。
- Contract v1.2は未検証候補であり、圧縮候補の仕様正本ではない。
