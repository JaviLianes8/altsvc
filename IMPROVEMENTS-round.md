# altsvc improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Pin the ground truth: RFC 7838 and its errata, RFC 9110, RFC 9111, RFC 3986, RFC 9114, RFC 9460, the IANA ALPN and Alt-Svc parameter registries, the quiche and curl parsers
- [x] Grammar-driven scanner with offsets: tokens, quoted strings, OWS, empty list elements, recovery
- [x] Strict and tolerant reading, several field lines, the clear token
- [x] Protocol-id percent-encoding: decode, canonical encode, typed ALPN access
- [x] Alt-authority: host and port, IP literals, A-labels
- [x] Parameters: ma (ASCII digits, 2^31 ceiling, 86400 default), persist, duplicates, unknown names
- [x] Linter: every finding with a code, a severity and an offset
- [x] Cache helper: expiry and freshness from ma and Age, injected clock
- [x] Safe builder: no header injection, canonical protocol-id, strict round trip
- [x] Command line
- [x] Contracts: pinned sources, README examples, typing, installed wheel
- [x] Docs and packaging: README, CHANGELOG, metadata, sdist contents
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [x] Mutation run: removing guarded logic makes the suite fail
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` gives `parse`, `build`, the `Alternative` dataclass, the `CLEAR` token and
`AltSvcError`. Probed against the sources below:

- `build` writes control characters as they are: an authority or a parameter value holding
  CR LF ends the field line and starts a new header (`Set-Cookie` injection).
- `ma` is read with `str.isdigit()` and `int()`: Arabic-Indic digits are read as 12, and a
  value of 5000 digits escapes as a bare `ValueError` from the interpreter's integer
  conversion limit. RFC 9111 section 1.2.2 allows only ASCII `1*DIGIT` and reads values that
  overflow as 2147483648.
- An absent `ma` gives `None`; RFC 7838 section 3.1 says the alternative is fresh for 24
  hours by default. There is no helper for expiry or for the `Age` adjustment that section
  3.1 works through.
- `h3=":443", clear` is read as one alternative; section 3 says `clear` invalidates every
  alternative, those in the same field included.
- The authority is never checked: `h3="host"` (no port), a port above 65535, a host with
  spaces or non-ASCII letters (section 8 asks for A-labels) are all accepted.
- The protocol-id is kept raw: `w%3Dx%3Ay#z` (the RFC's own example) cannot be turned into
  its ALPN name `w=x:y#z`, and non-canonical encodings are not detected.
- `MA=60` is ignored. The RFC does not say whether parameter names are case-sensitive;
  curl and quiche both compare them case-insensitively.
- Whitespace around `=` and other syntax errors are accepted silently, there are no offsets,
  and `bytes` input fails inside `str.join` with a confusing `TypeError`.
- The README says skipping malformed alternatives is what RFC 7838 asks recipients to do; the
  RFC only says unknown parameters are ignored. Skipping is a robustness choice and must be
  documented as such.

## Sources (fetched 2026-10-14)

- RFC 7838, https://www.rfc-editor.org/rfc/rfc7838.txt: the field grammar (3), protocol-id
  percent-encoding and its canonical form (3), alt-authority (3), unknown parameters (3),
  `ma` and the 24 hour default, the Age example, `persist` (3.1), A-labels (8), 421 (6).
  Errata page https://www.rfc-editor.org/errata/rfc7838 read: two editorial reports (one held
  for update about a hyphen, one rejected); neither changes the grammar.
- RFC 9110, https://www.rfc-editor.org/rfc/rfc9110.txt: token, OWS, quoted-string (5.6),
  list recipient rules with empty elements (5.6.1.2), combining field lines (5.3).
- RFC 9111, https://www.rfc-editor.org/rfc/rfc9111.txt: delta-seconds and the 2147483648
  ceiling (1.2.2).
- RFC 3986, https://www.rfc-editor.org/rfc/rfc3986.txt: host, IP-literal, reg-name, port.
- RFC 9114, https://www.rfc-editor.org/rfc/rfc9114.txt: the `h3` ALPN token and its Alt-Svc
  example (3.1.1).
- RFC 9460, https://www.rfc-editor.org/rfc/rfc9460.txt: SVCB and HTTPS records compared with
  Alt-Svc (9.2, 9.3): no SvcParamKey for `ma` or `persist`, and the example field in 9.3.
- IANA ALPN protocol IDs,
  https://www.iana.org/assignments/tls-extensiontype-values/alpn-protocol-ids.csv, and the
  Alt-Svc parameter registry,
  https://www.iana.org/assignments/http-alt-svc-parameters/http-alt-svc-parameters.xml.
- google/quiche `spdy_alt_svc_wire_format.cc` at commit
  132bfd90ea370faeacee616c70d10210bb12ba66 and curl `lib/altsvc.c` at commit
  9a6d4ffc1b6c184fb2ec7c6e4879c835cb367689: two shipping parsers. Both default `ma` to 86400
  and compare parameter names case-insensitively; quiche refuses the whole field on any error
  and requires a positive port, curl matches `clear` case-insensitively.
- None of these files is committed. `tests/upstream/MANIFEST.json` records URL, revision,
  size, sha256 and licence; `scripts/fetch_upstream.py` fetches and checks them into the
  ignored `tests/upstream/` folder, and the tests that read them skip while they are absent.

## Ranked improvements

1. **Safe builder.** No control characters or non-ASCII text in any part, canonical
   protocol-id, a checked authority, `ma` within the delta-seconds range, `persist` only as
   `1`, parameter names as tokens without case-insensitive clashes, plain `str` copies of
   every part. `parse(build(x), strict=True) == x` for every valid input.
2. **Correct `ma`.** ASCII digits only, quoted form unescaped first, values above 2^31 read
   as 2^31 without converting long digit strings, and `max_age` with the 86400 default.
3. **Grammar-driven scanner.** `clear / 1#alt-value` with RFC 9110 tokens, quoted strings,
   OWS around `;` and `,`, empty list elements, offsets for every finding, and recovery at
   the next parameter or alternative. Several field lines combine as one list. `bytes` input
   gets a clear `TypeError`.
4. **Strict and tolerant reading.** `parse(value, strict=True)` raises `AltSvcError` with a
   code and an offset on the first error. The default tolerant mode keeps every alternative
   whose protocol-id, authority and `ma` are sound and ignores a broken unknown parameter.
   `clear` next to alternatives reads as `CLEAR`, as section 3 says.
5. **Protocol-id and authority.** `decode_protocol_id`, `encode_protocol_id`, and
   `Alternative.alpn`, `.host`, `.port`; `Alternative.of(...)` builds one from an ALPN name,
   a port and an optional host, bracketing IPv6 literals.
6. **Linter.** `lint(value)` lists every `Issue` (code, message, severity, offset): grammar
   errors, a non-canonical protocol-id, a bad port or host, a bad `ma`, a capped `ma`, a
   duplicate parameter, an ignored `persist`, `clear` mixed with alternatives, and a protocol
   that is not one of the HTTP ALPN ids in the IANA registry.
7. **Cache helper.** `expires_at(alternative, received_at, age=0)` and
   `is_fresh(alternative, received_at, now, age=0)` follow section 3.1, the Age example
   included. Times are passed in, never read from the clock.
8. **Command line.** `altsvc` reads a value or a `curl -sI` dump and prints the alternatives
   and the findings as JSON; a 421 response is flagged because section 6 says its field is
   ignored. Exit status says whether the field is valid. It fits: checking what a site
   advertises is a shell task.
9. **Contracts.** RFC examples, registry entries and parser defaults are read from the pinned
   files, README examples run, types are checked with mypy, the installed wheel and its
   console script are driven from an empty folder.
10. **Docs and packaging.** README with executed examples and an API table, honest notes on
    where shipping parsers differ, CHANGELOG, keywords and classifiers, an sdist without
    planning notes or fetched files.

## Out of scope

- An alternative service cache keyed by origin, network change handling, the ALTSVC HTTP/2
  frame and the Alt-Used request field: they belong to a client, not to a field codec.
- Resolving SVCB or HTTPS records (RFC 9460); only the relation to Alt-Svc is documented.
- Legacy Google QUIC parameters (`v`, `quic`) that quiche still reads.
