"""
AST-level code validation using Python's ast module + RestrictedPython.
Rejects dangerous imports, builtins, and attribute access patterns.
"""

import ast
import logging
from dataclasses import dataclass, field

from RestrictedPython import compile_restricted

from app.sandbox.policy import BLOCKED_ATTRIBUTES, BLOCKED_MODULES

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_code(code: str) -> ValidationResult:
    """
    Perform two-pass validation:
    1. RestrictedPython compile check (syntax + restricted grammar).
    2. Custom AST walk for blocked imports and dangerous patterns.

    Returns ValidationResult — never raises.
    """
    result = ValidationResult(is_valid=True)

    # ── Pass 1: RestrictedPython compile ────────────────────────────────────
    try:
        compile_restricted(code, filename="<user_code>", mode="exec")
    except SyntaxError as exc:
        result.is_valid = False
        result.errors.append(f"Syntax error: {exc}")
        return result  # No point walking AST if it won't parse
    except Exception as exc:
        result.is_valid = False
        result.errors.append(f"Compilation error: {exc}")
        return result

    # ── Pass 2: AST walk ─────────────────────────────────────────────────────
    try:
        tree = ast.parse(code, filename="<user_code>")
    except SyntaxError as exc:
        result.is_valid = False
        result.errors.append(f"AST parse error: {exc}")
        return result

    for node in ast.walk(tree):
        # Block dangerous imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_root = alias.name.split(".")[0]
                if module_root in BLOCKED_MODULES:
                    result.is_valid = False
                    result.errors.append(f"Blocked import: '{alias.name}'")

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            module_root = module.split(".")[0]
            if module_root in BLOCKED_MODULES:
                result.is_valid = False
                result.errors.append(f"Blocked import from: '{module}'")

        # Block dangerous builtins called directly
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ("exec", "eval", "compile", "__import__", "open"):
                    result.is_valid = False
                    result.errors.append(f"Blocked call: '{node.func.id}()'")

        # Block dangerous attribute access (__class__.__bases__[0].__subclasses__() style)
        elif isinstance(node, ast.Attribute):
            if node.attr in BLOCKED_ATTRIBUTES:
                result.is_valid = False
                result.errors.append(f"Blocked attribute access: '.{node.attr}'")

    if not result.is_valid:
        logger.warning("Code validation failed: %d error(s)", len(result.errors))
    else:
        logger.debug("Code validation passed")

    return result
