# altsvc 1.0.0 certification report

Progress:
- [x] Release branch created from main `4da1939`; no earlier release branch
- [x] PyPI 0.2.0 identified; eleven pinned references fetched and verified
- [x] Stable API review, safe diagnostics, executable examples and strict typing
- [x] README, GUIDE, dated CHANGELOG and production metadata
- [x] Initial gates: 274 passed, one opt-in wheel test skipped
- [ ] Installed wheel, CLI, PyPI upgrade and distribution inspection
- [ ] Every available supported interpreter
- [ ] Mutation round of at least ten deliberate defects
- [ ] Final four gates
- [ ] Independent reviewer (item 16, separate stage)
- [ ] Five independent QA lenses (item 19, separate stage)
- [ ] Merge and publication (item 17, separate stage)

## API review

The fourteen names in `__all__` and their signatures remain available from 0.2.0.
`Alternative` remains a mutable, unvalidated dataclass; its factory and the builder
validate complete values. Strict and tolerant behavior, offsets and builder limits
are described in GUIDE.md. Corrections to duplicate ordering, long ports, integer
validation, surrogate handling, finite times and diagnostic privacy are in CHANGELOG.
The source and tests pass `mypy --strict src tests`. Public classes, functions and
properties have executable examples; constants are demonstrated in the package docstring.

## Ground truth

Fetched during this preparation on 2026-11-03. The requested release date in the
CHANGELOG is 2026-11-02. `tests/upstream/MANIFEST.json` records URL, revision, license,
size and SHA-256. All eleven downloads matched their existing pinned hashes.
Downloaded content is external to the repository, selected through `ALTSVC_UPSTREAM`.
Missing content skips source tests; the fetch script verifies immutable references.

- RFC 7838: https://www.rfc-editor.org/rfc/rfc7838.txt
- RFC 9110: https://www.rfc-editor.org/rfc/rfc9110.txt
- RFC 9111: https://www.rfc-editor.org/rfc/rfc9111.txt
- RFC 3986: https://www.rfc-editor.org/rfc/rfc3986.txt
- RFC 9114: https://www.rfc-editor.org/rfc/rfc9114.txt
- RFC 9460: https://www.rfc-editor.org/rfc/rfc9460.txt
- RFC 7838 errata, IANA ALPN and parameter registries, pinned curl and quiche source
  URLs are in the manifest. Their tests check current registry facts and parser rules.

`test_sources.py` extracts actual RFC field examples and encoding table rows from the
downloaded files. Expected results are interpretations of those examples. The independent
standard-library urllib codec oracle runs all 256 octets and seeded random octet strings;
it is executed locally, not a remembered vector set. Generated and hostile vectors in
the other tests are hand-written or seeded properties, not claimed as official fixtures.

## Pending validation

Installed distribution, interpreter and mutation results will be recorded here after
execution. Independent reviews and QA lens verdicts have not been performed for 1.0.0.
