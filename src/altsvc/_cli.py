"""Command line: check an Alt-Svc value or a response head and print JSON."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from ._errors import Issue
from ._head import field_lines
from ._lint import analyse
from ._model import Alternative

EXIT_INVALID = 1
EXIT_USAGE = 2


def _issue(issue: Issue) -> dict[str, object]:
    return {
        "code": issue.code,
        "severity": issue.severity,
        "offset": issue.offset,
        "message": issue.message,
    }


def _alternative(alternative: Alternative) -> dict[str, object]:
    return {
        "protocol": alternative.protocol,
        "alpn": alternative.alpn.decode("utf-8", "backslashreplace"),
        "host": alternative.host,
        "port": alternative.port,
        "max_age": alternative.max_age,
        "persist": alternative.persist,
        "params": alternative.params,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line; returns the process exit code."""
    parser = argparse.ArgumentParser(
        prog="altsvc",
        description="Check an Alt-Svc value, or the response head read from standard input "
        "(for example the output of curl -sI). Prints the alternatives and the findings as "
        "JSON. Exit status 0 means the value follows RFC 7838, 1 that it has errors, 2 a "
        "usage error such as input without the field.",
    )
    parser.add_argument("value", nargs="?", help="an Alt-Svc field value")
    args = parser.parse_args(argv)
    if args.value is None and sys.stdin.isatty():
        parser.error("give a value, or pipe a response head (curl -sI URL | altsvc)")
    # Latin-1 keeps every octet of a raw head, obs-text included.
    text = args.value if args.value is not None else sys.stdin.buffer.read().decode("latin-1")
    head = field_lines(text)
    status, fields = head if head is not None else ("", [])
    if head is None:
        bare = text.strip(" \t\r\n")
        # An empty argument is a value to check; empty standard input is a usage error.
        fields = [bare] if bare or args.value is not None else []
    if not fields:
        print("altsvc: no Alt-Svc field in the input", file=sys.stderr)
        return EXIT_USAGE
    analysis = analyse(fields)
    issues = list(analysis.issues)
    if status == "421":
        message = "a 421 (Misdirected Request) response's Alt-Svc must be ignored"
        issues.append(Issue("status.421", message, "warning"))
    report: dict[str, object] = {
        "field": ", ".join(fields),
        "valid": not analysis.errors,
        "clear": analysis.clear,
        "alternatives": [_alternative(item) for item in analysis.alternatives],
        "issues": [_issue(issue) for issue in issues],
    }
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if not analysis.errors else EXIT_INVALID
