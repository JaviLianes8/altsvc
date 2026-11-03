# altsvc 1.0.0 certification report

Progress:
- [x] Release branch created from main `4da1939`; no earlier release branch
- [x] PyPI 0.2.0 identified; eleven pinned references fetched and verified
- [x] Stable API review, safe diagnostics, executable examples and strict typing
- [x] README, GUIDE, dated CHANGELOG and production metadata
- [x] Final complete suite: 297 passed, no skips (wheel e2e enabled)
- [x] Installed wheel, CLI, PyPI upgrade and distribution inspection
- [x] Every available supported interpreter
- [x] Mutation round of at least ten deliberate defects
- [x] Final four gates
- [x] QA round 1: all twelve findings addressed; 406 tests passed
- [x] QA round 3: E-04 and E-05 contracts added; both mutants detected; 437 tests passed
- [x] QA round 4: E-06 and E-07 contracts added; both mutants detected; 473 tests passed
- [x] QA round 5: E-R5-01 and E-R5-02 contracts added; both mutants detected; 494 tests passed
- [x] Independent reviewer (item 16): PASS in round 1, no findings
- [x] Five independent QA lenses (item 19): all five PASS
- [x] PR #3 from `release/1.0.0` to `main`, trace guard CLEAN, final gates on a fresh clone
- [ ] Merge and publication (maintainer)

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

## Scorecard

| Item | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Fourteen stable names and factory signatures pinned by API contracts; changes documented |
| 2 | PASS | Exact public namespace and `__all__`; incidental `annotations` removed |
| 3 | PASS | Module doctests, every public callable and property, README and GUIDE examples executed |
| 4 | PASS | `mypy --strict src tests`, installed-wheel strict consumer, `py.typed` |
| 5 | PASS | Typed errors, codes and offsets; generated diagnostics omit input; 100 KB secret tests |
| 6 | PASS | 297 tests including every exported name, failure paths, CLI and metadata |
| 7 | PASS | Eleven live downloads verified; RFC examples extracted; urllib codec oracle executed |
| 8 | PASS | Actual PyPI 0.2.0 installed, common consumer run, upgrade in place, full consumer and CLI |
| 9 | PASS | 15,768 seeded or exhaustive property trials plus six large input scaling shapes |
| 10 | PASS | CPython 3.10 through 3.14, including free-threaded 3.14, installed wheel and sdist tests |
| 11 | PASS | Absolute links, exact badge, problem and scoped alternatives comparison, strict twine check |
| 12 | PASS | Requested dated 1.0.0 section, 2026-11-02; complete changes from published 0.2.0 |
| 13 | PASS | 1.0.0, Production/Stable, Python 3.10+, MIT, four project URLs, no runtime dependencies |
| 14 | PASS | Wheel and sdist contents inspected and asserted, LICENSE in both, no downloaded references |
| 15 | PASS | Each of the four gates exits 0; full suite includes installed-wheel e2e |
| 16 | PASS | Independent reviewer round 1, every item PASS, no findings (see below) |
| 17 | PASS | PR #3 from `release/1.0.0` to `main`, trace guard CLEAN; merge and publication by the maintainer |
| 18 | PASS | Twenty isolated mutations, twenty detected failures, baseline and restored suite pass |
| 19 | PASS | Lenses a to e each report PASS after their fix rounds (see below) |

## Packaging and end-to-end checks

The wheel was installed into a fresh environment, first installing actual PyPI 0.2.0
from https://pypi.org/pypi/altsvc/json (checked 2026-11-03; uploaded 2026-10-20).
The common consumer program passed before and after upgrading in place to 1.0.0.
The program imports from site-packages under isolated mode, exercises every function,
and checks type information. Both the installed command and `python -m altsvc` were
driven through subprocesses with response heads, invalid values and missing fields.
A separate consumer passed `mypy --strict` against the installed wheel and executed.

`twine check --strict` passed for both artifacts. The wheel contains only the package,
type marker and distribution metadata including the entry point and MIT license.
The sdist contains source, tests, source manifest, docs and development/build scripts.
It contains no downloaded source text, bytecode, caches, version-control files or
certification reports. A small build hook removes Hatchling's forced VCS-file inclusion.

- `altsvc-1.0.0-py3-none-any.whl`: 20 entries, SHA-256 `efeba72c1a9508e2e378b41da721aea897793c002ea47bb5fa15a363f636b106`.
- `altsvc-1.0.0.tar.gz`: 47 entries, SHA-256 `86e562ed81610203605abf7d8c3186e606017d1ab78688b0aac699714a9c8aca`.

## Interpreter matrix

The local installed interpreter was CPython 3.14.6. All other launcher registrations
pointed to missing historical paths. Isolated CPython builds were therefore downloaded
for every other supported minor version, plus free-threaded 3.14. The sdist was extracted,
its `src` directory moved outside the test tree, and the wheel installed into each fresh
environment. Tests ran with isolated Python and the pytest source-path setting cleared.
The sole skip in each matrix run is the separate wheel-building e2e test, run above.

| Interpreter | Result |
| --- | --- |
| CPython 3.14.6 | 296 passed, 1 skipped in 20.93s |
| CPython 3.10.22 | 296 passed, 1 skipped in 23.79s |
| CPython 3.11.18 | 296 passed, 1 skipped in 25.51s |
| CPython 3.12.16 | 296 passed, 1 skipped in 17.86s |
| CPython 3.13.18 | 296 passed, 1 skipped in 16.13s |
| CPython 3.14.10t | 296 passed, 1 skipped in 13.63s |

No supported minor version from 3.10 through 3.14 was left untested. Other Python
implementations were not installed and are not separately advertised.

## Robustness and mutation round

The property suite includes 2,000 generated round trips, 3,000 hostile parser inputs,
6,768 codec comparisons with urllib, and 4,000 independently evaluated duplicate
parameter sequences. Blank lines, folded lines, long quoted values, many parameters,
leading-zero ports and percent escapes scale at 10,000, 40,000 and 160,000 units.
Large quoted serialization round trips and bounded diagnostic tests run in the suite.
Tests use a 300-second per-test timeout; subprocesses also have finite timeouts.

Each mutation below was applied alone to a scratch copy of the final library. The
complete non-e2e suite ran with stop-on-first-failure. Every mutation produced a real
test failure (exit 1); no collection error or timeout counted as a detection. The clean
baseline and restored suite both passed 296 tests with only the opt-in e2e skipped.

| # | Deliberate defect | Test that caught it |
| --- | --- | --- |
| 1 | default lifetime one second short (`_model.py`) | `tests/test_cert_contract.py::test_public_docstrings_are_executable` |
| 2 | delta ceiling one second low (`_params.py`) | `tests/test_build_safety.py::test_build_accepts_the_largest_ma_and_leading_zeros` |
| 3 | expiry includes boundary (`_cache.py`) | `tests/test_cert_contract.py::test_public_docstrings_are_executable` |
| 4 | age added instead of subtracted (`_cache.py`) | `tests/test_cert_contract.py::test_public_docstrings_are_executable` |
| 5 | nonfinite times accepted (`_cache.py`) | `tests/test_cert_contract.py::test_nonfinite_times_are_refused[nan]` |
| 6 | duplicate spelling order lost (`_lint.py`) | `tests/test_cert_contract.py::test_exact_spelling_reinserted_after_other_case_variants` |
| 7 | long port converts raw digits (`_codec.py`) | `tests/test_cert_contract.py::test_long_zero_prefixed_port_is_safe[]` |
| 8 | protocol percent left bare (`_codec.py`) | `tests/test_cert_contract.py::test_public_docstrings_are_executable` |
| 9 | decoder uses decimal (`_codec.py`) | `tests/test_cert_contract.py::test_public_docstrings_are_executable` |
| 10 | maximum port rejected (`_codec.py`) | `tests/test_codec.py::test_split_authority[[2001:db8::1]:65535-2001:db8::1-65535]` |
| 11 | empty build silently written (`_build.py`) | `tests/test_build.py::test_build_refuses_an_empty_sequence` |
| 12 | builder allows duplicate names (`_build.py`) | `tests/test_build_safety.py::test_build_refuses[alternative10-parameter.duplicate]` |
| 13 | builder accepts invalid persistence (`_build.py`) | `tests/test_build_safety.py::test_build_refuses[alternative9-persist.invalid]` |
| 14 | strict parse ignores errors (`_parse.py`) | `tests/test_docs.py::test_every_readme_example_runs_and_prints_its_comment` |
| 15 | clear no longer invalidates alternatives (`_parse.py`) | `tests/test_build.py::test_round_trip_clear` |
| 16 | CLI accepts 421 response (`_cli.py`) | `tests/test_cli.py::test_a_421_response_is_ignored` |
| 17 | CLI invalid status exits success (`_cli.py`) | `tests/test_cli.py::test_errors_exit_one_and_list_findings` |
| 18 | quoted backslash not escaped (`_chars.py`) | `tests/test_build_safety.py::test_build_quotes_values_that_are_not_tokens` |
| 19 | last parameter becomes first (`_params.py`) | `tests/test_cert_contract.py::test_exact_spelling_reinserted_after_other_case_variants` |
| 20 | factory raises wrong exception (`_model.py`) | `tests/test_cert_contract.py::test_huge_factory_integers_have_typed_errors[port]` |

## Final gates

On CPython 3.14.6, each command exited 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, and `pytest`. The stronger `mypy --strict src tests` also passed
(33 source files). Pytest with `ALTSVC_E2E=1` and the verified source downloads passed
all 297 tests, no skips. Scratch paths were supplied for pytest temporary directories.

## QA round 1

Date: 2026-11-03. Reviewed base: `1bd1ae88c28c46695fdecbae2a31c2c4989e0eff`.
Fix commit: `e1e12d587a890c3c3a3c06a9508cf929a832ff7c`. All twelve findings addressed,
none disputed. The earlier scorecard and hashes describe preparation before this round.

| Finding | Change and verification |
| --- | --- |
| A01 | Require boolean `strict`; six wrong-type contract cases |
| A02, C-01 | Validate authority and parameter storage types, reject present `ma=None`, and propagate validation through freshness helpers; malformed-field and independent-accessor contracts |
| A03 | State the horizontal-tab exception in README, CHANGELOG and the builder docstring |
| A04 | Define error severity to include documented library policy in the Issue docstring |
| A05 | Distinguish wrong-type TypeError from invalid-value AltSvcError in the builder docstring |
| B-001 | Discard ignored persistence values before storage; preserve earlier `persist=1` across case variants and quoted values; 42 strict/tolerant regression cases; update previous conflicting expectations |
| C-02 | Normalize host, port and lifetime subclasses before validation and serialization; underlying-value and range contracts |
| C-03 | Use constant, bounded CLI usage diagnostics; subprocess checks for unknown options, excess arguments and help values, including large synthetic markers |
| D-001 | Suppress effective CLI alternatives when clear is present; subprocess checks in both list orders, piped heads and both installed launchers |
| E-01 | Protect Issue from a writable instance dictionary; M37 now fails the new contract |
| E-02 | Assert protocol-id.empty for empty bytes and text; M49 now fails both cases |

Hand-written regressions ran before implementation changes. Replaying the API and
factory contracts on the reviewed source confirmed 94 failures and five passes.
The initial subprocess run demonstrated both CLI bugs. After correcting Windows
newline translation in the piped test harness, all 109 new cases pass.

Scratch mutation copies, with imported paths checked, produced one failure for M37
and two for M49. No mutation was left in the repository.

All four gates exited 0: `ruff format --check .`, `ruff check .`, `mypy --strict src`,
and `pytest`. Strict source/test typing also passed (36 files). CPython 3.14.6 passed
**406 tests, no skips**, with `ALTSVC_E2E=1`, verified fixtures and `--timeout=300`.
The wheel test built distributions, upgraded 0.2.0 and checked both CLI launchers.
The interpreter matrix was not repeated this round; earlier results remain above.

Evidence and temporary paths, relative to this checkout: `../../scratch/altsvc-cert/fix-r1/`.
Logs: `red.log`, `original-verified.log`, `M37-verified.log`, `M49-verified.log`,
`final.log`, `report-gates.log`. Behavior changes are recorded in CHANGELOG.md.

## QA round 2

Date: 2026-11-03. Reviewed base: `4b49011ebc9d01b2bda27caf16d70dc317ee4f98`.
Fix commit: `b5ab5010571fefe413adbf896bd5e68f0fa0a87a`. Both reported findings
addressed; none disputed. Earlier scorecards, artifact hashes and interpreter results
describe their respective preparation rounds.

| Finding | Change and verification |
| --- | --- |
| C-04 | Normalize accepted authority strings and parameter keys and values with base-string conversion before accessor operations. Ten hand-written cases check destinations, lifetime boundaries, freshness, parameter matching and persistence against strict serialization round trips. Raw constructor values remain unchanged. |
| E-03 | Add source and installed-wheel CLI contracts for a 421 response containing a valid alternative. Assert exit 1, `ignored=true`, a `status.421` issue and `alternatives=[]`; the wheel contract exercises both installed launchers. Existing CLI suppression remains unchanged. |

Before the accessor fix, the new contracts produced nine accessor failures; the
uppercase-key control and eleven CLI cases passed. After the fix, all 21 targeted
cases passed. The behavior correction and the added CLI coverage are in CHANGELOG.md.

N02 was applied only to a scratch source copy, replacing `ignored or analysis.clear`
with `analysis.clear`. Each run below exited 1 at the empty-alternatives assertion;
neither a collection error nor a build failure counted as a detection.

| Mutation | Detecting contract | Result |
| --- | --- | --- |
| N02, source | `tests/test_cli_contract.py::test_421_suppresses_effective_alternatives` | One test failed on the exposed h3 alternative |
| N02, installed wheel | `tests/test_e2e_wheel.py::test_installed_wheel_end_to_end` | Wheel built and installed; the 421 output assertion failed |

All four gates exited 0: `ruff format --check .`, `ruff check .`, `mypy --strict src`,
and `pytest`. The stronger `mypy --strict src tests` also passed (37 files).
CPython 3.14.6 passed **417 tests, no skips**, with `ALTSVC_E2E=1`, verified upstream
fixtures and a 300-second per-test timeout. The wheel test built both distributions,
upgraded the installed 0.2.0 release and exercised both CLI launchers. The interpreter
matrix was not repeated in this bounded fix round.

Evidence paths relative to this checkout: `../../scratch/altsvc-cert/fix-r2/`.
Logs: `red.log`, `green.log`, `n02-source.log`, `n02-wheel.log`, `full-gates.log`.
The mutation driver and mutated copy remain in that scratch directory; no mutation
was applied to the repository.

## QA round 3

Date: 2026-11-03. Reviewed base: `6cd1786471fc6c04ffe674a722b3b3a1da9c3299`.
Fix commit: `286fbbd05556b9744351d7d231f923a6b6ef4c31`. Both findings addressed;
none disputed. These were missing regression contracts: the reviewed implementation
already returned the correct results. No library code, public API or behavior changed.
CHANGELOG.md records the added coverage.

| Finding | Change and verification |
| --- | --- |
| E-04 | Add source and installed-wheel contracts rejecting long-s lookalikes as persistence names, including a lookalike after an ASCII parameter. ASCII case variants still enable persistence. |
| E-05 | Require `ma.invalid` for explicitly empty `ma`, `MA` and `Ma` through `ma`, `max_age`, `expires_at` and `is_fresh`. Both source and installed-wheel controls preserve the missing-parameter default and freshness boundary. |

The 20 new hand-written source cases and installed-wheel check first passed on the
unchanged implementation. Each exact reviewer mutation was then applied independently
to a scratch source copy. Source imports were checked against that copy; the wheel was
built from it and consumed under isolated Python from an empty directory, with the
package's site-packages location asserted. Each detection below exited 1 because of
the expected contract failure, without a collection error, build failure or timeout.

| Mutation | Detecting contract | Result |
| --- | --- | --- |
| P05: replace ASCII name folding with Unicode `casefold()` | `test_non_ascii_lookalikes_cannot_enable_persistence` | Four source failures; 16 controls passed |
| P05: installed wheel | `test_installed_wheel_end_to_end`, running `wheel_parameters.py` | Failed the false-persistence assertion |
| P10: replace `return found` with `return found or None` | `test_empty_lifetime_is_invalid` | Twelve source failures; eight controls passed |
| P10: installed wheel | `test_installed_wheel_end_to_end`, running `wheel_parameters.py` | Failed because empty `ma` did not raise `ma.invalid` |

All four gates exited 0: `ruff format --check .`, `ruff check .`, `mypy --strict src`,
and `pytest`. The stronger `mypy --strict src tests` also passed (39 files).
CPython 3.14.6 passed **437 tests, no skips**, with `ALTSVC_E2E=1`, verified upstream
fixtures and a 300-second per-test timeout. The wheel check built both distributions,
upgraded the installed 0.2.0 release and exercised the new parameter consumer and both
CLI launchers. The interpreter matrix was not repeated in this bounded fix round.

Evidence paths relative to this checkout: `../../scratch/altsvc-cert/fix-r3/`.
Logs: `baseline.log`, `P05-source.log`, `P05-wheel.log`, `P10-source.log`,
`P10-wheel.log`, `full-gates.log` and `report-gates.log`. Exact mutation commands and
exit codes are in `verify.py` and `results.json`. Mutations exist only in scratch copies.
Earlier scorecards, artifact hashes and interpreter results describe their own rounds.

## QA round 4

Date: 2026-11-03. Reviewed base: `d9ba619e17db20ec559562076a3a59e5014cc670`.
Fix commit: `4deb9a8c19c60cb7969cda5a299b6c909517093a`. Both findings addressed;
none disputed. These were missing contract cases: the reviewed implementation already
returned the correct results. No library source, public API or behavior changed.
CHANGELOG.md records the added coverage.

| Finding | Change and verification |
| --- | --- |
| E-06 | Add source and installed-wheel acceptance contracts for `UserDict` and `MappingProxyType`, checking `ma`, `max_age` and `persist`. |
| E-07 | Add source and installed-wheel contracts requiring false persistence for space/tab-padded values and `ma.invalid` for padded lifetimes through `ma`, `max_age`, `expires_at` and `is_fresh`. |

The 36 new hand-written source cases first passed against the unchanged implementation.
The targeted baseline, including the installed-wheel test, passed all 57 cases. Each
exact reviewer mutation was applied independently to a scratch source copy. Source
imports were checked against that copy; each wheel was built from its mutated copy
and consumed under isolated Python from an empty directory, with site-packages asserted.
All detections exited 1 on the intended contract failure, with no collection error,
build failure or timeout.

| Mutation | Detecting contract | Result |
| --- | --- | --- |
| M06: replace `isinstance(params, Mapping)` with `isinstance(params, dict)` | `test_parameter_accessors_accept_non_dict_mappings` | Six source failures; 50 controls passed |
| M06: installed wheel | `test_installed_wheel_end_to_end`, running `wheel_parameters.py` | Failed because the accepted `UserDict` raised `TypeError` |
| M10: append `.strip()` to `str.__str__(value)` | `test_whitespace_padded_persistence_is_false`, `test_whitespace_padded_lifetime_is_invalid` | 30 source failures; 26 controls passed |
| M10: installed wheel | `test_installed_wheel_end_to_end`, running `wheel_parameters.py` | Failed the false-persistence assertion |

All four gates exited 0: `ruff format --check .`, `ruff check .`, `mypy --strict src`,
and `pytest`. The stronger `mypy --strict src tests` also passed (39 files).
CPython 3.14.6 passed **473 tests, no skips**, with `ALTSVC_E2E=1`, hash-verified
upstream fixtures and a 300-second per-test timeout. The wheel check built both
distributions, upgraded the installed 0.2.0 release and exercised the parameter consumer
and both CLI launchers. The interpreter matrix was not repeated in this bounded round.

Evidence paths relative to this checkout: `../../scratch/altsvc-cert/fix-r4/`.
Logs: `baseline.log`, `M06-source.log`, `M06-wheel.log`, `M10-source.log`,
`M10-wheel.log`, `full-gates.log` and `report-gates.log`. Exact mutation commands and
exit codes are in `verify.py` and `results.json`. Mutations exist only in scratch copies.
Earlier scorecards, artifact hashes and interpreter results describe their own rounds.

## QA round 5

Date: 2026-11-03. Reviewed base: `5187e9af8359e462093df65e207ecac21ee91b2e`.
Fix commit: `77f4c44ba832cc6be20a111a7bca2e753b228ab4`. Both findings addressed;
none disputed. These were missing contract cases: the reviewed implementation already
returned the correct results. No library source, public API or behavior changed.
CHANGELOG.md records the added coverage.

| Finding | Change and verification |
| --- | --- |
| E-R5-01 | Add source and installed-wheel contracts keeping space/tab-padded parameter names unmatched through `ma`, `max_age` and `persist`. Check both missing parameters and a padded spelling following an existing matching parameter. |
| E-R5-02 | Add source and installed-wheel contracts requiring `TypeError` through all three accessors for an items-only object that is not a `Mapping`. Retain acceptance controls for `UserDict` and `MappingProxyType`. |

The 21 new hand-written source cases first passed against the unchanged implementation.
The targeted baseline, including the installed-wheel test, passed all 78 cases. Each
exact reviewer mutation was applied independently to a scratch source copy. Source
imports were checked against that copy; each wheel was built from its mutated copy
and consumed under isolated Python from an empty directory, with site-packages asserted.
All detections exited 1 on the intended contract failure, with no collection error,
build failure or timeout.

| Mutation | Detecting contract | Result |
| --- | --- | --- |
| S03: append `.strip()` to `str.__str__(key)` | `test_whitespace_padded_parameter_names_remain_unmatched` | 18 source failures; 59 controls passed |
| S03: installed wheel | `test_installed_wheel_end_to_end`, running `wheel_parameters.py` | Failed because the padded lifetime name matched instead of returning `None` |
| S07: replace `isinstance(params, Mapping)` with `hasattr(params, "items")` | `test_parameter_accessors_reject_items_only_non_mappings` | Three source failures; 74 controls passed |
| S07: installed wheel | `test_installed_wheel_end_to_end`, running `wheel_parameters.py` | Failed because the items-only object did not raise `TypeError` |

All four gates exited 0: `ruff format --check .`, `ruff check .`, `mypy --strict src`,
and `pytest`. The stronger `mypy --strict src tests` also passed (39 files).
CPython 3.14.6 passed **494 tests, no skips**, with `ALTSVC_E2E=1`, eleven hash-verified
upstream fixtures and a 300-second per-test timeout. The wheel check built both
distributions, upgraded the installed 0.2.0 release and exercised the parameter consumer
and both CLI launchers. The interpreter matrix was not repeated in this bounded round.

Evidence paths relative to this checkout: `../../scratch/altsvc-cert/fix-r5/`.
Logs: `baseline.log`, `S03-source.log`, `S03-wheel.log`, `S07-source.log`,
`S07-wheel.log`, `full-gates.log` and `report-gates.log`. Exact mutation commands and
exit codes are in `verify.py` and `results.json`; gate commands are in `gates.py`.
Mutations exist only in scratch copies. Earlier scorecards, artifact hashes and
interpreter results describe their own rounds.

## QA lenses (item 19)

Five independent lenses each ran their own checks and reported back. Every finding
was fixed in the rounds above and re-verified by the same lens until it reported PASS.

| Lens | Rounds | Final verdict | Report | Commit |
| --- | --- | --- | --- | --- |
| a. API and docs | 2 | PASS | laptop, `scratch/altsvc-cert/lens-a-r2/REPORT.md` | `4b49011ebc9d01b2bda27caf16d70dc317ee4f98` |
| b. Correctness and ground truth | 2 | PASS | laptop, `scratch/altsvc-cert/lens-b-r2/REPORT.md` | `4b49011ebc9d01b2bda27caf16d70dc317ee4f98` |
| c. Adversarial and robustness | 3 | PASS | laptop, `scratch/altsvc-cert/lens-c-r3/REPORT.md` | `6cd1786471fc6c04ffe674a722b3b3a1da9c3299` |
| d. Packaging and real e2e | 2 | PASS | laptop, `scratch/altsvc-cert/lens-d-r2/REPORT.md` | `4b49011ebc9d01b2bda27caf16d70dc317ee4f98` |
| e. Contract strength | 6 | PASS | `D:/pylib-scratch/altsvc-cert/lens-e-r6/REPORT.md` | `8112cbe8e79527ca56d92f73d3be8b4513470579` |

Lens e round 6 re-checked E-R5-01 and E-R5-02 (both killed in source and installed-wheel
runs) and swept ten further probes on parameter lookup: eight killed, two shown equivalent.

## Independent reviewer (item 16)

Round 1 at `8112cbe8e79527ca56d92f73d3be8b4513470579`, report
`D:/pylib-scratch/altsvc-cert/review-r1/REPORT.md`. Verdict PASS, no findings.
The reviewer ran the four gates, the suite with and without references (494 passed,
no skips with `ALTSVC_E2E=1`), doctests, build and `twine check --strict`, a PyPI 0.2.0
upgrade in a throwaway venv, an installed-wheel interpreter matrix and its own twelve
mutants (eleven killed, one equivalent for the documented contract).

| Item | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | API pinned by stability and contract tests; changes in CHANGELOG |
| 2 | PASS | Namespace equals `__all__`; no private imports in docs |
| 3 | PASS | Examples on every public name; doctests and README/GUIDE examples pass |
| 4 | PASS | `mypy --strict src tests`; `py.typed` shipped; no `Any` in public API |
| 5 | PASS | Typed `AltSvcError(code, offset)`; codes documented; no input echo |
| 6 | PASS | 494 tests cover every exported name and failure paths |
| 7 | PASS | Eleven hash-verified fetched references with URL and date; urllib oracle |
| 8 | PASS | Wheel e2e, PyPI 0.2.0 upgrade and both launchers in its own venv |
| 9 | PASS | Seeded properties; own fuzz and scaling probes |
| 10 | PASS | 3.10, 3.12, 3.13, 3.14 and 3.14t pass; 3.11 run in preparation, listed |
| 11 | PASS | Strict twine check; absolute links; problem, why, install, quick start, links |
| 12 | PASS | `[1.0.0] - 2026-11-02` with a Stable section |
| 13 | PASS | 1.0.0, Production/Stable, 3.10 to 3.14, MIT, four URLs, keywords, no deps |
| 14 | PASS | Contents inspected; LICENSE in both; no third-party files shipped |
| 15 | PASS | Four gates exit 0 |
| 16 | PASS | This review |
| 17 | PASS | PR #3 from `release/1.0.0`, trace guard CLEAN; merge by the maintainer |
| 18 | PASS | Twenty-row table plus round mutations; own re-check 11 of 12 killed, 1 equivalent |
| 19 | PASS | Lens a-r2, b-r2, c-r3, d-r2 and e-r6 reports exist with verdict PASS |

## Remaining stages

Merge of PR #3 and publication to PyPI are left to the maintainer.
