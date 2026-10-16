"""6.1 各サブコマンドの正常系・拒否系の終了コード（0成功、2契約拒否、3入出力、4内部エラー）。"""
from __future__ import annotations

import json

from conftest import CHANGE, cli, git, make_review, report, set_review


def test_start_ok_and_rejections(repo):
    code, out = cli(repo, 'start', CHANGE)
    assert code == 0 and 'T-1.1' in out and 'S-greeting-1.1' in out and 'CHK-VALIDATE' in out
    assert cli(repo, 'start', CHANGE)[0] == 2           # 開始済み
    assert cli(repo, 'start', 'missing')[0] == 2        # 存在しないchange
    git(repo, 'switch', '-q', 'master')
    assert cli(repo, 'start', CHANGE)[0] == 2           # default branch（state未作成のmaster側）


def test_commit_round_review_status_finish_prune_refreeze(repo, tmp_path):
    assert cli(repo, 'status', CHANGE)[0] == 2          # 未開始
    cli(repo, 'start', CHANGE)
    code, out = cli(repo, 'commit-round', CHANGE)
    assert code == 2 and '実装報告' in out              # 報告なし
    assert cli(repo, 'review', CHANGE)[0] == 2          # レビュー対象なし
    report(repo, 1)
    code, out = cli(repo, 'commit-round', CHANGE)
    assert code == 0 and 'r1' in out
    assert cli(repo, 'commit-round', CHANGE)[0] == 2    # 未レビューで次round
    set_review(tmp_path, make_review(repo))
    code, out = cli(repo, 'review', CHANGE)
    assert code == 0 and 'Gate: PASS' in out
    assert cli(repo, 'review', CHANGE)[0] == 2          # レビュー済み
    code, out = cli(repo, 'status', CHANGE)
    assert code == 0 and 'finish' in out
    assert cli(repo, 'refreeze', CHANGE, '--reason', ' ')[0] == 2
    assert cli(repo, 'prune', CHANGE)[0] == 2           # バックアップrefなし
    code, out = cli(repo, 'finish', CHANGE)
    assert code == 0 and 'dry-run' in out
    code, out = cli(repo, 'finish', CHANGE, '--confirm')
    assert code == 0 and 'tree一致' in out
    assert cli(repo, 'finish', CHANGE, '--confirm')[0] == 2   # squash済み
    code, out = cli(repo, 'prune', CHANGE)
    assert code == 0 and '--confirm' in out
    assert cli(repo, 'prune', CHANGE, '--confirm')[0] == 0
    assert cli(repo, 'refreeze', CHANGE, '--reason', 'x')[0] == 2  # 終了済み


def test_review_failure_exit_3_and_json_output(repo, tmp_path, monkeypatch):
    cli(repo, 'start', CHANGE)
    report(repo, 1)
    cli(repo, 'commit-round', CHANGE)
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'fail')
    code, out = cli(repo, '--json', 'review', CHANGE)
    assert code == 3 and json.loads(out)['record']['gate']['gate'] == 'INCONCLUSIVE'


def test_doctor_exit_codes(repo, fake_bin):
    assert cli(repo, 'doctor')[0] == 0
    (fake_bin / 'agent').unlink()
    code, out = cli(repo, 'doctor', '--reviewer', 'cursor')
    assert code == 2 and 'agent login' in out


def test_internal_error_exit_4(repo, monkeypatch):
    from spec_review_loop import cli as cli_mod
    monkeypatch.setattr(cli_mod, 'execute', lambda a: (_ for _ in ()).throw(RuntimeError('boom')))
    assert cli_mod.main(['--root', str(repo), 'status', CHANGE]) == 4


def test_corrupt_state_is_io_error(repo):
    cli(repo, 'start', CHANGE)
    (repo / 'openspec' / 'changes' / CHANGE / 'review' / 'state.json').write_text('{broken', encoding='utf-8')
    assert cli(repo, 'status', CHANGE)[0] == 3
