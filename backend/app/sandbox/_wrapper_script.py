"""
Sandbox wrapper — this file is COPIED (not imported) into each execution directory.
It sets up a minimal, restricted __builtins__ and then exec()s the user code.
Do NOT rename or move this file; runner.py locates it by path.
"""
import os
import sys
import json
import io

# ── Restrict __builtins__ ────────────────────────────────────────────────────
SAFE_BUILTINS = {
    'abs': abs, 'all': all, 'any': any, 'bool': bool, 'bytes': bytes,
    'dict': dict, 'divmod': divmod, 'enumerate': enumerate, 'filter': filter,
    'float': float, 'format': format, 'frozenset': frozenset,
    'getattr': getattr, 'hasattr': hasattr, 'hash': hash, 'hex': hex,
    'int': int, 'isinstance': isinstance, 'issubclass': issubclass,
    'iter': iter, 'len': len, 'list': list, 'map': map, 'max': max,
    'min': min, 'next': next, 'object': object, 'oct': oct, 'ord': ord,
    'pow': pow, 'print': print, 'range': range, 'repr': repr,
    'reversed': reversed, 'round': round, 'set': set, 'setattr': setattr,
    'slice': slice, 'sorted': sorted, 'str': str, 'sum': sum,
    'tuple': tuple, 'type': type, 'zip': zip,
    '__name__': '__main__', '__doc__': None,
    '__import__': __import__,
}

# ── Execute user code ─────────────────────────────────────────────────────────
user_code_path = os.path.join(os.path.dirname(__file__), 'transform.py')
with open(user_code_path, 'r', encoding='utf-8') as f:
    user_code = f.read()

try:
    exec(compile(user_code, 'transform.py', 'exec'), {'__builtins__': SAFE_BUILTINS})
except Exception as exc:
    print(f"EXECUTION ERROR: {exc}", file=sys.stderr)
    sys.exit(1)
