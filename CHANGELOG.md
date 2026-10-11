# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- Parse an Alt-Svc header value into a list of alternatives, each with protocol,
  authority and parameters, following RFC 7838.
- Build an Alt-Svc header value from alternatives, quoting the authority and parameter
  values as needed.
- Support the `clear` token, quoted-string authorities and values, the `ma` and
  `persist` parameters, multiple comma-separated alternatives, and tolerant skipping of
  malformed entries.
