# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased

### Added

- `lint` lists every finding with a code, a severity and an offset; `parse(..., strict=True)`
  raises `AltSvcError` (now with `code` and `offset`) on the first error.
- `Alternative.alpn`, `.host`, `.port` and `.max_age` (86400 by default, RFC 7838 section
  3.1), and `Alternative.of(alpn, port, host, ma=..., persist=..., params=...)`.
- `encode_protocol_id` and `decode_protocol_id` for the percent-encoded protocol-id.
- `expires_at` and `is_fresh` compute freshness from `ma` and the response age.
- `Issue`, `DEFAULT_MAX_AGE` and `DELTA_SECONDS_MAX`.
- An `altsvc` command (and `python -m altsvc`) that checks a value or a `curl -sI` head and
  prints JSON.
- `parse` and `lint` accept several field lines and combine them as one list.

### Changed

- The reader follows the RFC 7838 grammar with RFC 9110 tokens and quoted strings. The
  tolerant default keeps alternatives whose protocol-id, authority and `ma` are sound and
  drops the others; the README no longer says RFC 7838 asks for this.
- `clear` next to alternatives now reads as `CLEAR`.
- `ma` accepts ASCII digits only and reads values above 2147483648 as 2147483648; parameter
  names are matched without case, and the last repeated parameter wins (for `ma`, an
  invalid value is still an error, but only an invalid last value drops the alternative).
- Wrong argument types raise `TypeError`; `parse` and `lint` take a `str` or a sequence of
  `str` only.
- The command line reads a 421 response's field as ignored and exits 1.
- An authority needs a port from 1 to 65535 (leading zeros allowed) and an ASCII reg-name
  or IPv4 host, or a bracketed IPv6 address without a zone ID.
- `clear` must be the whole value: next to alternatives or list commas it is an error.
- `build` refuses control characters, non-ASCII text, non-canonical protocol-ids, invalid
  authorities, an invalid `ma` or `persist`, repeated parameter names and an empty list;
  it writes the characters of `str` subclasses, never their own rendering.
- `bytes` input gets a clear `TypeError`.

## [0.1.0]

- Parse an Alt-Svc header value into a list of alternatives, each with protocol,
  authority and parameters, following RFC 7838.
- Build an Alt-Svc header value from alternatives, quoting the authority and parameter
  values as needed.
- Support the `clear` token, quoted-string authorities and values, the `ma` and
  `persist` parameters, multiple comma-separated alternatives, and tolerant skipping of
  malformed entries.
