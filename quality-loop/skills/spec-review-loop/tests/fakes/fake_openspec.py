#!/usr/bin/env python3
"""偽openspec。FAKE_OPENSPEC_EXITの終了コードを返す。"""
import os
import sys
if sys.argv[1:] == ['--version']:
    print('0.0.0-fake')
    sys.exit(0)
sys.exit(int(os.environ.get('FAKE_OPENSPEC_EXIT', '0')))
