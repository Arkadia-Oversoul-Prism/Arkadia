"""Stable copy for 5xx responses, with the cause kept in the log.

An exception's own text is server-side evidence: it can carry an internal host,
a credential state, or a database path. Returning it to the caller discloses
that evidence and, when the handler does not log, destroys it at the same
moment. :func:`internal_failure_detail` keeps the traceback and hands the
caller copy that names the operation without describing the failure.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("arkadia")


def internal_failure_detail(operation: str) -> str:
    """Log the active exception and return caller-safe copy.

    Call this only from inside an ``except`` block; ``logger.exception`` reads
    the exception the interpreter is currently handling.
    """
    logger.exception("%s failed", operation)
    return f"{operation} failed; inspect server logs for internal details."
