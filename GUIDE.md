# Alt-Svc guide

## Reading and writing

`parse(value, *, strict=False)` accepts a string or a sequence of strings. Several
field lines are joined with comma and space; offsets refer to that joined value.
`strict` must be a bool; other types raise `TypeError`.
The default returns usable alternatives in wire order, or `CLEAR`. Strict mode raises
`AltSvcError` on the first error; warnings do not prevent parsing. `lint(value)` returns
all findings sorted by offset. Recovery from malformed values is library policy.

`clear` is case-sensitive. When mixed with alternatives it still clears the result in
tolerant mode, while strict mode rejects the mixed list. Empty list members are allowed
around alternatives, but not around `clear`. An entirely empty value is an error.

Parameter names are compared using ASCII case folding. The last occurrence wins, even
when spellings alternate in case. Invalid earlier `ma` values still produce diagnostics.
Unknown parameters are retained. Persistence is the exception: values other than `1`
are ignored before storage and cannot cancel an earlier `persist=1`. Decimal `ma` is capped
at 2147483648, without converting unbounded digit strings. Absence means 86400 seconds.

`Alternative(protocol, authority, params={})` is a mutable, unvalidated data container.
Each instance gets its own default dictionary. Accessors validate the relevant part:
authority accessors require a string, and parameter accessors require a mapping with
string keys and values. Wrong types, including a present `ma=None`, raise `TypeError`.
`Alternative.of(alpn, port, host='', *, ma=None, persist=False, params=None)` validates
the complete value through the builder and copies the supplied mapping. Explicit `ma`
and true `persist` replace those exact lower-case keys; conflicting case variants are
rejected by the builder. False `persist` leaves supplied parameters unchanged.
Host, port and lifetime subclasses are normalized to their underlying primitive values
before validation and serialization; custom formatting cannot replace those values.

`build` accepts `CLEAR` or a nonempty sequence of alternatives. Its output parses
strictly back to equal alternatives. It rejects ambiguous duplicate parameter names,
noncanonical protocols, control characters except horizontal tab, non-ASCII values,
out-of-range `ma`, and `persist` values other than `1`. The raw constructor itself does
not make that guarantee. Empty extension values are quoted. Dictionary insertion order
determines serialization order.

## Protocols and authorities

`encode_protocol_id` accepts UTF-8 text or bytes. Percent and non-token octets use
uppercase percent escapes. Empty input and lone surrogates raise `AltSvcError`.
`decode_protocol_id` returns bytes and accepts lowercase escapes too. Strict header
parsing and building require canonical encoding. These helpers encode arbitrary ALPN
octets; they do not enforce a TLS handshake's protocol-name length limit.

Authorities require a port from 1 to 65535; leading zeros are accepted. Hosts are ASCII
URI reg-names (including valid percent escapes), IPv4 text, or bracketed IPv6. Empty
hosts refer to the origin. IPvFuture and zone IDs are outside the supported policy.
This is syntactic validation, not DNS resolution or proof of authority for an origin.

## Freshness

`expires_at(alternative, received_at, *, age=0)` returns the receipt time plus the
remaining lifetime, never earlier than receipt. `is_fresh(alternative, received_at,
now, *, age=0)` uses a strict less-than comparison: the exact expiry instant is stale.
Times must be finite ints or floats, excluding booleans; age must be a nonnegative
integer, excluding booleans. The caller supplies the clock and response age.

```python
from altsvc import Alternative, expires_at, is_fresh

service = Alternative.of("h3", 443, ma=60)
assert expires_at(service, 100.0, age=30) == 130.0
assert not is_fresh(service, 100.0, 130.0, age=30)
```

## Errors and findings

Wrong argument types raise `TypeError`; invalid values raise `AltSvcError`, a
`ValueError` subclass with `code`, `message`, and optional `offset`. `Issue` is frozen,
with `code`, `message`, `severity` (`error` or `warning`), and optional `offset`, and
has no writable instance dictionary. Errors include documented additional library policy.
Constructors for `Alternative`, `Issue`, and `AltSvcError` store the caller's fields;
they do not sanitize or validate arbitrary objects supplied directly to them.

Library-generated diagnostics do not echo input. Wording may change; branch on codes.
Codes include `protocol-id.*`, `authority.port`, `authority.host`, `ma.invalid`,
`parameter.*`, `persist.*`, `syntax.*`, `clear.*`, `empty`, `age.negative`, and
`time.invalid`. Parser offsets index the combined field; builder/accessor offsets
refer to the individual component. Neither the parser nor builder performs network I/O.
Processing is linear in input length apart from sorting findings by offset. There is
no arbitrary input-size cap; callers should enforce their own HTTP field-size limit.

## Command line

Usage errors print bounded diagnostics without argument contents. Use `--` before a
field value starting with a hyphen. When `clear` is present, JSON lists no effective
alternatives, including when mixed-list errors are reported.

`altsvc VALUE` and `python -m altsvc VALUE` check one field. Without an argument they
read standard input as Latin-1, preserving every input byte. A response head may contain
multiple field lines or multiple responses; the last response is selected. Obsolete
folding is unfolded. Exit 0 means syntactically usable, 1 means invalid or a 421
response, and 2 means a usage error or no Alt-Svc field. A 421 result is ignored even
when the field itself is valid. JSON includes the original field, so it should be
treated as potentially sensitive input when logging. Validation does not authenticate
the alternative service or replace TLS checks.

## Upgrade from 0.2.0

Names and call signatures remain available. Normal parsing and building keep their
results. See the [CHANGELOG](https://github.com/JaviLianes8/altsvc/blob/main/CHANGELOG.md)
for corrected duplicate ordering, long ports, bounded diagnostics, factory validation,
finite times, surrogate handling and CLI scaling changes. Error text is deliberately
different. The supported interpreter range remains Python 3.10 and later.
