# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-02

### Stable

- The fourteen exported names, signatures and defaults, the mutable `Alternative`
  model, typed findings, strict and tolerant parsing, safe serialization, protocol-id
  codecs, freshness helpers and JSON command line are the supported API.
- Runnable docstrings, a detailed guide, installed-wheel upgrade coverage, seeded
  properties, source-derived examples and mutation-tested contracts.

### Changed

- Source and installed-wheel contracts now require ASCII-only parameter matching and
  `ma.invalid` for explicitly empty lifetimes, including freshness helpers. Missing
  lifetimes retain the default; existing library behavior is unchanged.
- Authority and parameter accessors read the underlying characters of accepted string
  subclasses, matching serialization for destinations, lifetimes and persistence.
  Stored constructor values remain unchanged; freshness helpers use the same lifetimes.
- CLI contracts now require empty effective alternatives for HTTP 421 responses in
  both source and installed-wheel runs. Existing CLI behavior is unchanged.
- `parse` requires a boolean `strict`; other types raise `TypeError`.
- `Alternative` accessors reject wrong authority types and malformed parameter
  mappings with `TypeError`, including a present `ma=None` instead of treating it as
  the default lifetime. Freshness helpers propagate this validation.
- `Alternative.of` normalizes accepted host, port and lifetime subclasses before
  validation and serialization, preserving their underlying string and integer values.
- Parsing ignores non-`1` persistence values before storing parameters, so a later
  ignored value cannot cancel an earlier `persist=1`, regardless of case or quoting.
  Other parameters retain the last-occurrence policy; ignored persistence still warns.
- CLI usage errors use bounded diagnostics without echoing arguments. JSON reports
  no effective alternatives when `clear` invalidates the list, while retaining findings.
- Contracts now protect `Issue` against a writable instance dictionary and assert
  `protocol-id.empty` for empty text and bytes. Neither changes existing behavior.
- Documentation consistently permits horizontal tab in builder parameter values,
  distinguishes wrong types from invalid values, and includes library policy in errors.
- Library-generated errors and lint findings no longer quote input values or type names.
  Codes and offsets remain available; diagnostic wording is not a stable contract.
- Repeated parameter spellings now preserve wire order: `ma=1; MA=2; ma=3` reads as 3.
- Ports with thousands of leading zeros read without triggering Python's integer limit.
- `Alternative.of` rejects out-of-range integers before converting them to text and
  rejects non-mapping `params`, including empty lists.
- Encoding lone surrogates raises `AltSvcError` with code `protocol-id.unicode`.
- Freshness helpers require an `Alternative` and finite numeric times (booleans refused);
  invalid times raise `AltSvcError` with code `time.invalid`, wrong types raise `TypeError`.
  Expiry is consistently returned as a float.
- CLI processing of leading blank lines and folded fields takes linear time.
- The incidental `annotations` module attribute is removed; `__all__` is the complete
  supported public surface.

## [0.2.0] - 2026-10-20

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
- `build` refuses control characters except horizontal tab, non-ASCII text,
  non-canonical protocol-ids, invalid authorities, an invalid `ma` or `persist`,
  repeated parameter names and an empty list;
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
