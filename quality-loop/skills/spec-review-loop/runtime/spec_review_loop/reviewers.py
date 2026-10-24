"""Reviewer CLIアダプタ。版で変わるフラグはここに閉じ込める。

各アダプタの責務は「プロンプトを渡す」「読取り専用・承認なしで実行する」「最終出力を得る」の3点に限る。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

DEFAULT_REVIEWER = 'codex'
DEFAULT_TIMEOUT = 1200


def quiet_env() -> dict:
    """Reviewer・checkの実行環境。無害なバイトコード書込み（__pycache__）を抑止する。"""
    return {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}


@dataclass(frozen=True)
class Adapter:
    name: str
    binary: str
    help_args: tuple[str, ...]
    required_flags: tuple[str, ...]
    install_hint: str

    def command(self, exe: str, cwd: Path, out_file: Path, model: str | None, prompt: str,
                effort: str | None = None) -> tuple[list[str], str | None]:
        """(argv, stdinに渡す文字列)を返す。"""
        if self.name == 'codex':
            argv = [exe, 'exec', '--sandbox', 'read-only', '--ephemeral', '--color', 'never',
                    '-C', str(cwd), '--output-last-message', str(out_file)]
            argv += ['--model', model] if model else []
            argv += ['-c', f'model_reasoning_effort={effort}'] if effort else []
            return argv + ['-'], prompt
        if self.name == 'claude':
            argv = [exe, '--print', '--tools', 'Read,Grep,Glob', '--permission-mode', 'dontAsk',
                    '--permission-prompts', 'none', '--output-format', 'json']
            argv += ['--model', model] if model else []
            argv += ['--effort', effort] if effort else []
            return argv, prompt
        # cursor（Cursor CLIのagent）: askモードは読取り専用。プロンプトはstdinで渡す
        argv = [exe, '--print', '--mode', 'ask', '--sandbox', 'enabled', '--trust', '--workspace', str(cwd),
                '--output-format', 'json']
        if model:
            argv += ['--model', f'{model}[effort={effort}]' if effort and '[' not in model else model]
        return argv, prompt

    def final_text(self, stdout: str, out_file: Path) -> str:
        if self.name == 'codex':
            return out_file.read_text(encoding='utf-8') if out_file.exists() else ''
        data = json.loads(stdout)
        if data.get('is_error'):
            raise ValueError(f'{self.name}がエラーを返しました: {str(data.get("result", ""))[:500]}')
        return str(data.get('result', ''))

    def model_name(self, stdout: str, requested: str | None) -> str:
        if requested:
            return requested
        if self.name == 'codex':
            return _codex_config_model() or 'unknown（CLI既定）'
        if self.name == 'cursor':
            return 'auto（Cursor既定）'
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return 'unknown'
        usage = data.get('modelUsage')
        return ', '.join(usage) if isinstance(usage, dict) and usage else 'unknown'


ADAPTERS = {
    'codex': Adapter('codex', 'codex', ('exec', '--help'),
                     ('--sandbox', '--output-last-message', '--ephemeral', '--cd'),
                     'brew install codex または npm install -g @openai/codex'),
    'cursor': Adapter('cursor', 'agent', ('--help',),
                      ('--print', '--mode', '--sandbox', '--trust', '--workspace', '--output-format', '--model'),
                      'Cursor CLIを導入し（curl https://cursor.com/install -fsS | bash）、agent login で認証してください'),
    'claude': Adapter('claude', 'claude', ('--help',),
                      ('--print', '--tools', '--permission-mode', '--permission-prompts', '--output-format'),
                      'npm install -g @anthropic-ai/claude-code'),
}


def _codex_config_model() -> str | None:
    home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    try:
        import tomllib
        return tomllib.loads((home / 'config.toml').read_text(encoding='utf-8')).get('model')
    except (OSError, ValueError, ImportError):
        return None


def get(name: str) -> Adapter:
    if name not in ADAPTERS:
        raise ValueError(f'未対応のReviewerです: {name}（{"/".join(ADAPTERS)}）')
    return ADAPTERS[name]


def probe(name: str) -> dict:
    """CLIの存在・版・必要フラグを確認する。"""
    adapter = get(name)
    exe = shutil.which(adapter.binary)
    result = {'tool': name, 'path': exe, 'version': None, 'missing_flags': [], 'ok': False, 'install': adapter.install_hint}
    if not exe:
        result['problem'] = f'{adapter.binary} が見つかりません'
        return result
    try:
        version = subprocess.run([exe, '--version'], capture_output=True, text=True, timeout=30)
        result['version'] = (version.stdout or version.stderr).strip().splitlines()[0] if (version.stdout or version.stderr).strip() else 'unknown'
        helptext = subprocess.run([exe, *adapter.help_args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        result['problem'] = f'{adapter.binary} を実行できません: {exc}'
        return result
    text = helptext.stdout + helptext.stderr
    result['missing_flags'] = [flag for flag in adapter.required_flags if flag not in text]
    if result['missing_flags']:
        result['problem'] = f'必要なフラグに対応していません: {", ".join(result["missing_flags"])}'
        return result
    result['ok'] = True
    return result


def extract_json(text: str) -> dict:
    """最終出力からJSONオブジェクトを1つ取り出す。コードフェンスや前置きを許容する。"""
    stripped = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())
    decoder = json.JSONDecoder()
    for match in re.finditer(r'\{', stripped):
        try:
            value, _ = decoder.raw_decode(stripped[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError('Reviewer出力にJSONオブジェクトがありません')


def _stream(argv: list[str], stdin: str | None, cwd: Path, timeout: int, log_path: Path | None) -> dict:
    """子プロセスを起動し、出力を逐次ログへ書きながら終了を待つ。timeoutでは子孫ごと止める。"""
    log = open(log_path, 'a', encoding='utf-8', buffering=1) if log_path else None
    lock = threading.Lock()

    def emit(tag: str, text: str) -> None:
        if log:
            with lock:
                log.write(f'[{tag}] {text}' if text.endswith('\n') else f'[{tag}] {text}\n')

    started = time.monotonic()
    emit('srl', f'start {time.strftime("%Y-%m-%dT%H:%M:%S%z")} timeout={timeout}s argv0={Path(argv[0]).name}')
    proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, env=quiet_env(), start_new_session=True)
    chunks: dict[str, list[str]] = {'out': [], 'err': []}

    def pump(pipe, tag: str) -> None:
        for line in iter(pipe.readline, ''):
            chunks[tag].append(line)
            emit(tag, line)

    def feed() -> None:
        try:
            proc.stdin.write(stdin or '')
        except (BrokenPipeError, OSError):
            pass
        finally:
            try:
                proc.stdin.close()
            except OSError:
                pass

    threads = [threading.Thread(target=pump, args=(proc.stdout, 'out'), daemon=True),
               threading.Thread(target=pump, args=(proc.stderr, 'err'), daemon=True),
               threading.Thread(target=feed, daemon=True)]
    for t in threads:
        t.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            proc.kill()
        proc.wait()
    for t in threads:
        t.join(timeout=5)
    emit('srl', f'end returncode={proc.returncode} timed_out={timed_out} elapsed={time.monotonic() - started:.1f}s')
    if log:
        log.close()
    return {'returncode': proc.returncode, 'stdout': ''.join(chunks['out']), 'stderr': ''.join(chunks['err']),
            'timed_out': timed_out}


def run(name: str, prompt: str, cwd: Path, timeout: int, model: str | None, info: dict, effort: str | None = None,
        log_path: Path | None = None) -> dict:
    """Reviewerを1回実行する。失敗は例外ではなく ok=False で返す。log_pathがあれば出力を逐次書き出す。"""
    adapter = get(name)
    base = {'tool': name, 'version': info.get('version') or 'unknown', 'model': model or 'unknown', 'ok': False}
    with tempfile.TemporaryDirectory(prefix='spec-review-out-') as tmp:
        out_file = Path(tmp) / 'last_message.txt'
        argv, stdin = adapter.command(info['path'], cwd, out_file, model, prompt, effort)
        try:
            proc = _stream(argv, stdin, cwd, timeout, log_path)
        except OSError as exc:
            return {**base, 'error': f'起動に失敗しました: {exc}', 'raw': ''}
        if proc['timed_out']:
            return {**base, 'error': f'timeout（{timeout}秒）', 'raw': ''}
        base['model'] = adapter.model_name(proc['stdout'], model) + (f'（effort {effort}）' if effort else '')
        if proc['returncode'] != 0:
            return {**base, 'error': f'終了コード {proc["returncode"]}: {proc["stderr"].strip()[-2000:]}', 'raw': proc['stdout'][-20000:]}
        try:
            text = adapter.final_text(proc['stdout'], out_file)
        except (OSError, ValueError) as exc:
            return {**base, 'error': f'最終出力を読めません: {exc}', 'raw': proc['stdout'][-20000:]}
    try:
        data = extract_json(text)
    except ValueError as exc:
        return {**base, 'error': str(exc), 'raw': text[-20000:]}
    return {**base, 'ok': True, 'data': data, 'raw': text}
