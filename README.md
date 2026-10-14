# altsvc

Parse, check and build the HTTP `Alt-Svc` header (RFC 7838), typed and zero-dependency.

## Install

```
pip install altsvc
```

## Read a field value

```python
from altsvc import parse

for alt in parse('h3=":443"; ma=3600; persist=1, h2="alt.example.com:443"'):
    print(alt.alpn, repr(alt.host), alt.port, alt.max_age, alt.persist)
# b'h3' '' 443 3600 True
# b'h2' 'alt.example.com' 443 86400 False
```

An empty host means the origin's own host. Without `ma` an alternative is fresh for
86400 seconds (section 3.1). `ma` is read as ASCII digits only, and a value too large to
represent is read as 2147483648, as RFC 9111 says for every delta-seconds value.

`clear` comes back as `CLEAR`, also when it sits next to alternatives, because section 3
says it then invalidates all of them. Several field lines are one list:

```python
from altsvc import CLEAR, parse

print(parse('h3=":443", clear') is CLEAR)
# True
print(parse(['h3=":443"', 'h2=":443"; ma=60'])[1].ma)
# 60
```

## Strict and tolerant reading

The default reading is tolerant: it keeps every alternative whose protocol-id, authority
and `ma` are sound, and ignores a broken parameter of another name. RFC 7838 does not say
how to recover from a malformed value; this is a choice of the library, and `lint` tells
you what was skipped. `strict=True` raises on the first error instead:

```python
from altsvc import AltSvcError, lint, parse

value = 'h3=":443"; ma=x, h2=":0", h3=":8443";'
print(parse(value))
# [Alternative(protocol='h3', authority=':8443', params={})]
for issue in lint(value):
    print(issue.code, issue.severity, issue.offset)
# ma.invalid error 11
# authority.port error 20
# syntax.empty-parameter error 36
try:
    parse(value, strict=True)
except AltSvcError as error:
    print(error.code, error.offset)
# ma.invalid 11
```

Errors break the RFC 7838 grammar or one of its rules; warnings flag legal but likely
mistaken values: a repeated parameter (the last one wins), `persist` with a value other
than `1` (ignored, section 3.1), an `ma` above 2^31, and a protocol that is not one of
the HTTP entries of the IANA ALPN registry.

## Build a field value

```python
from altsvc import CLEAR, Alternative, build, encode_protocol_id, parse

alt = Alternative.of("h3", 8443, "2001:db8::1", ma=3600, persist=True)
print(build([alt, Alternative.of("h2", 443)]))
# h3="[2001:db8::1]:8443"; ma=3600; persist=1, h2=":443"
print(build(CLEAR))
# clear
print(encode_protocol_id("w=x:y#z"))
# w%3Dx%3Ay#z
print(parse(build([alt]), strict=True) == [alt])
# True
```

`build` checks every part before writing it and raises `AltSvcError` rather than write a
value that would not read back: control characters and non-ASCII text (no header
injection through CR LF), a protocol-id that is not in canonical form, a host that is not
an ASCII reg-name or IP literal, a port outside 1 to 65535, an `ma` that is not digits up
to 2^31, `persist` other than `1`, and parameter names that repeat up to case.

## Freshness

```python
from altsvc import expires_at, is_fresh, parse

# RFC 7838 section 3.1: ma=60 on a response that is already 30 seconds old.
(alt,) = parse('h2=":8000"; ma=60')
print(expires_at(alt, received_at=1000.0, age=30))
# 1030.0
print(is_fresh(alt, received_at=1000.0, now=1031.0, age=30))
# False
```

Times are whatever clock you pass in; the library never reads the clock itself.

## Command line

```
$ curl -sI https://example.org | altsvc
$ altsvc 'h3=":443"; ma=86400'
```

Prints the alternatives and the findings as JSON. Exit status 0 means the value follows
RFC 7838, 1 that it has errors, 2 a usage error such as input without the field. With
`curl -sIL` the last response is checked, and a 421 response is flagged because
section 6 says its `Alt-Svc` must be ignored.

## API

| Name | What it does |
| --- | --- |
| `parse(value, *, strict=False)` | Read a value or a list of field lines into alternatives or `CLEAR` |
| `lint(value)` | Every finding as an `Issue` (code, message, severity, offset) |
| `build(alternatives)` | Write a checked value from alternatives or `CLEAR` |
| `Alternative` | `protocol`, `authority`, `params`; `alpn`, `host`, `port`, `ma`, `max_age`, `persist`; `Alternative.of(...)` |
| `CLEAR`, `Clear` | The `clear` token and its type |
| `encode_protocol_id(name)` | ALPN name to canonical protocol-id |
| `decode_protocol_id(protocol_id)` | Protocol-id to ALPN name octets |
| `expires_at(alt, received_at, *, age=0)` | When the alternative stops being fresh |
| `is_fresh(alt, received_at, now, *, age=0)` | Whether it is still fresh at `now` |
| `Issue` | One finding |
| `AltSvcError` | A `ValueError` with `code` and `offset` |
| `DEFAULT_MAX_AGE`, `DELTA_SECONDS_MAX` | 86400 and 2147483648 |

## Where shipping parsers differ

- quiche (Chromium) refuses the whole field on any error and requires a positive port;
  this library keeps the sound alternatives unless you ask for `strict=True`.
- curl matches `clear` without regard to case; RFC 7838 makes it case-sensitive, and so
  does this library.
- RFC 7838 does not say whether parameter names are case-sensitive. curl and quiche
  compare them without case, and so do `ma`, `persist` and the duplicate check here.
- quiche refuses a quoted `ma`; section 3 says quoted-string forms are processed as
  RFC 7230 asks, so `ma="60"` is read as 60 here.

## Related: SVCB and HTTPS records

RFC 9460 publishes much the same information in DNS. It has no counterpart to `ma` (the
DNS TTL plays that part) nor to `persist`, and a client that uses both should keep its
connection attempts consistent with each. Resolving those records is out of scope here.

## Why

Alt-Svc tells a client that a service is also reachable over another protocol or
authority, most often to advertise HTTP/3. In Python the header is usually hand-rolled
with a split on commas, which breaks on quoted strings and silently accepts what clients
reject. This library is a small, typed, zero-dependency codec for that one header,
checked against the RFC text and two shipping parsers.

## Development

`scripts/check.ps1` runs the gate. The tests that compare the code with the RFCs, the
IANA registries and the quiche and curl sources read files that are not committed:
`python scripts/fetch_upstream.py` fetches them into `tests/upstream/` and checks each
against `tests/upstream/MANIFEST.json`. Without them those tests skip.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
