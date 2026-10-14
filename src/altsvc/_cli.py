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
        "JSON. Exit status 0 means the value follows RFC 7838 and a client may use it, 1 that "
        "it has errors or comes in a 421 response, 2 a usage error such as input without "
        "the field.",
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
    # RFC 7838 section 6: a client ignores the field of a 421 response altogether.
    ignored = status == "421"
    if ignored:
        message = "a 421 (Misdirected Request) response's Alt-Svc must be ignored"
        issues.append(Issue("status.421", message, "error"))
    usable = [] if ignored else analysis.alternatives
    report: dict[str, object] = {
        "field": ", ".join(fields),
        "valid": not analysis.errors,
        "ignored": ignored,
        "clear": analysis.clear and not ignored,
        "alternatives": [_alternative(item) for item in usable],
        "issues": [_issue(issue) for issue in issues],
    }
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if not analysis.errors and not ignored else EXIT_INVALID
