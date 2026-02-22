"""
Sandbox security policy: allowed builtins and import allowlists.
"""

ALLOWED_BUILTINS: dict = {
    "abs": abs, "all": all, "any": any, "bool": bool, "bytes": bytes,
    "dict": dict, "divmod": divmod, "enumerate": enumerate, "filter": filter,
    "float": float, "format": format, "frozenset": frozenset,
    "getattr": getattr, "hasattr": hasattr, "hash": hash, "hex": hex,
    "int": int, "isinstance": isinstance, "issubclass": issubclass,
    "iter": iter, "len": len, "list": list, "map": map, "max": max,
    "min": min, "next": next, "object": object, "oct": oct, "ord": ord,
    "pow": pow, "print": print, "range": range, "repr": repr,
    "reversed": reversed, "round": round, "set": set, "setattr": setattr,
    "slice": slice, "sorted": sorted, "str": str, "sum": sum,
    "tuple": tuple, "type": type, "zip": zip,
    # Explicitly blocked — None signals "not available"
    "open": None,
    "__import__": None,
    "exec": None,
    "eval": None,
    "compile": None,
}

ALLOWED_IMPORTS: frozenset[str] = frozenset([
    "pandas", "numpy", "os", "os.path", "pathlib",
    "re", "datetime", "math", "json", "csv",
    "collections", "functools", "itertools", "typing",
])

BLOCKED_MODULES: frozenset[str] = frozenset([
    "subprocess", "socket", "requests", "urllib", "http",
    "importlib", "ctypes", "sys", "shutil", "tempfile",
    "pickle", "shelve", "multiprocessing", "threading",
    "concurrent", "asyncio", "signal", "resource",
    "pty", "tty", "termios", "fcntl", "grp", "pwd",
    "platform", "sysconfig", "site", "builtins",
    "gc", "weakref", "inspect", "dis", "tokenize",
    "ast", "code", "codeop", "pdb", "faulthandler",
])

BLOCKED_ATTRIBUTES: frozenset[str] = frozenset([
    "__class__", "__bases__", "__subclasses__", "__globals__",
    "__builtins__", "__code__", "__closure__", "__func__",
    "__self__", "__dict__", "__module__", "__qualname__",
    "mro", "__mro__",
])
