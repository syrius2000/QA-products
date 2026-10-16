#!/usr/bin/env python3
"""偽Reviewer。codex／claude／agent（Cursor）の名前で置き、FAKE_REVIEW_FILEのJSONを各CLIの出力形式で返す。"""
import json
import os
import sys
import time
from pathlib import Path

name = Path(sys.argv[0]).name
args = sys.argv[1:]
if args == ['--version']:
    print(f'{name} 9.9.9-fake')
    sys.exit(0)
if '--help' in args:
    print('--sandbox --output-last-message --ephemeral --cd --prompt --approval-mode --output-format '
          '--print --tools --permission-mode --permission-prompts --mode --model --trust --workspace')
    sys.exit(0)
prompt = sys.stdin.read()
log = os.environ.get('FAKE_REVIEW_LOG')
if log:
    with open(log, 'a', encoding='utf-8') as fh:
        shown = [a for a in args if a != prompt]
        app = Path('app.py').read_text(encoding='utf-8') if Path('app.py').exists() else None
        fh.write(json.dumps({'name': name, 'args': shown, 'cwd': os.getcwd(), 'prompt': prompt, 'app': app}, ensure_ascii=False) + '\n')
mode = os.environ.get('FAKE_REVIEW_MODE', 'ok')
if mode == 'fail':
    print('boom', file=sys.stderr)
    sys.exit(5)
if mode == 'timeout':
    time.sleep(30)
if mode == 'write':
    Path('INJECTED.txt').write_text('x')
text = 'no json here' if mode == 'garbage' else Path(os.environ['FAKE_REVIEW_FILE']).read_text(encoding='utf-8')
if name == 'codex':
    Path(args[args.index('--output-last-message') + 1]).write_text(text, encoding='utf-8')
elif name == 'claude':
    print(json.dumps({'type': 'result', 'result': text, 'modelUsage': {'fake-claude-model': {}}}))
else:  # agent（Cursor CLI）
    print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': text}))
