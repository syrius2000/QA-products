"""標準ライブラリだけで動く、review.schema.jsonに必要な範囲のJSON Schema検証。"""
from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[2] / 'references' / 'review.schema.json'

_TYPES = {
    'object': lambda v: isinstance(v, dict),
    'array': lambda v: isinstance(v, list),
    'string': lambda v: isinstance(v, str),
    'integer': lambda v: isinstance(v, int) and not isinstance(v, bool),
    'number': lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    'boolean': lambda v: isinstance(v, bool),
    'null': lambda v: v is None,
}


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def validate(instance, schema: dict | None = None) -> list[str]:
    """違反をJSON Pointer付きの文字列で返す。空なら適合。"""
    root = schema if schema is not None else load_schema()
    errors: list[str] = []
    _check(instance, root, root, '', errors)
    return errors


def _resolve(ref: str, root: dict) -> dict:
    if not ref.startswith('#/'):
        raise ValueError(f'未対応の$ref: {ref}')
    node = root
    for part in ref[2:].split('/'):
        node = node[part]
    return node


def _check(value, schema: dict, root: dict, path: str, errors: list[str]) -> None:
    where = path or '/'
    if '$ref' in schema:
        _check(value, _resolve(schema['$ref'], root), root, path, errors)
        return
    if 'const' in schema and value != schema['const']:
        errors.append(f'{where}: {schema["const"]!r} である必要があります')
        return
    if 'enum' in schema and value not in schema['enum']:
        errors.append(f'{where}: {schema["enum"]} のいずれかである必要があります（値: {value!r}）')
        return
    if 'type' in schema:
        types = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not any(_TYPES[t](value) for t in types):
            errors.append(f'{where}: 型は {"/".join(types)} である必要があります')
            return
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            errors.append(f'{where}: 空にできません')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            errors.append(f'{where}: 形式 {schema["pattern"]} に一致しません（値: {value!r}）')
    if isinstance(value, int) and not isinstance(value, bool) and 'minimum' in schema and value < schema['minimum']:
        errors.append(f'{where}: {schema["minimum"]} 以上である必要があります')
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            errors.append(f'{where}: 要素が{schema["minItems"]}件以上必要です')
        if 'items' in schema:
            for i, item in enumerate(value):
                _check(item, schema['items'], root, f'{path}/{i}', errors)
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                errors.append(f'{where}: 必須項目 {key} がありません')
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            for key in value:
                if key not in props:
                    errors.append(f'{where}: 未定義の項目 {key} があります')
        for key, sub in props.items():
            if key in value:
                _check(value[key], sub, root, f'{path}/{key}', errors)
