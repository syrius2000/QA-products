# r2 実装報告

- F-003（T-1.1、S-text-utils-1.2）: 置換後に`.strip('-')`で前後のハイフンを除去した（textutils.py:5）。
- F-002（T-1.2）: `test_textutils.py`を追加。空白・記号（Hello, World!）、前後の空白、大文字のテストを含む。
- F-001（T-1.1、CHK-UNITTEST）: `python3 -m unittest -q test_textutils` を実行し3件成功。
- tasks.mdの1.1、1.2を完了にした。
