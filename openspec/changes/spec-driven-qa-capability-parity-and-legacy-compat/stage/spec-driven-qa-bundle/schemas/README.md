# Schema方針

JSON Schemaを外部検証可能な正本形式として維持する。Python型への全面置換は行わず、標準ライブラリの`validate_schema.py`を実行時検証器として併用する。

受理fixtureは`stage/fixtures/schema/accepted-contract.json`、拒否fixtureは`stage/fixtures/schema/rejected-contract.json`である。契約フィールド、状態、Finding、Evidence、digest対象の必須性・型・列挙値・digest形式を検証する。
