# altsvc

Parse and build the HTTP Alt-Svc header (RFC 7838), a typed zero-dep codec.

## Install

```
pip install altsvc
```

## Usage

```python
from altsvc import CLEAR, Alternative, build, parse

# Parse a header value into alternatives.
alternatives = parse('h3=":443"; ma=3600; persist=1, h2="alt.example.com:443"')
# [Alternative(protocol='h3', authority=':443', params={'ma': '3600', 'persist': '1'}),
#  Alternative(protocol='h2', authority='alt.example.com:443', params={})]

first = alternatives[0]
first.protocol   # 'h3'
first.authority  # ':443'
first.ma         # 3600  (the ma parameter as an int, or None)
first.persist    # True  (whether persist=1 was present)

# Build a header value back.
build([Alternative("h3", ":443", {"ma": "3600"})])  # 'h3=":443"; ma=3600'

# The clear token.
parse("clear")    # CLEAR
build(CLEAR)      # 'clear'
```

The parser respects quoted-strings, so commas and semicolons inside an authority or a
parameter value are not treated as separators. Malformed alternatives are skipped rather
than discarding the whole header, as RFC 7838 asks recipients to do.

## Why

Alt-Svc tells a client that a service is also available over another protocol or
authority, for example to advertise HTTP/3. No Python package ships this header as a
small codec: the logic lives inside curl's C core and inside Erlang, Haskell and Rust
clients, so Python projects hand-roll it or pull in a whole HTTP framework. This library
is a single-purpose, typed, zero-dependency parser and builder for that one header.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
