from io import BytesIO

import pytest

from internals.headers.headers import (
    Headers,
    ParserState,
    head_parser,
    req_from_reader,
)


# --------------------------------------------------
# 1. head_parser() tests
# --------------------------------------------------

def test_valid_single_header():
    data = b"Host: localhost:42069\r\n\r\n"

    consumed, parsed_headers = head_parser(data)

    assert parsed_headers == {
        "host": "localhost:42069",
    }
    assert consumed == len(data)


def test_valid_multiple_headers():
    data = (
        b"Host: localhost:42069\r\n"
        b"User-Agent: curl\r\n"
        b"Accept: */*\r\n"
        b"\r\n"
    )

    consumed, parsed_headers = head_parser(data)

    assert parsed_headers == {
        "host": "localhost:42069",
        "user-agent": "curl",
        "accept": "*/*",
    }
    assert consumed == len(data)


def test_header_value_with_extra_whitespace():
    data = b"Host:    localhost:42069 \t\r\n\r\n"

    consumed, parsed_headers = head_parser(data)

    assert consumed == len(data)
    assert parsed_headers["host"] == "localhost:42069"


def test_header_value_can_contain_colons():
    data = b"Host: localhost:42069\r\n\r\n"

    _, parsed_headers = head_parser(data)

    assert parsed_headers["host"] == "localhost:42069"


def test_empty_headers():
    data = b"\r\n"

    consumed, parsed_headers = head_parser(data)

    assert consumed == 2
    assert parsed_headers == {}


def test_incomplete_header_returns_zero():
    data = b"Host: localhost:42069"

    consumed, parsed_headers = head_parser(data)

    assert consumed == 0
    assert parsed_headers == {}


def test_incomplete_header_section_returns_zero():
    data = b"Host: localhost:42069\r\n"

    consumed, parsed_headers = head_parser(data)

    assert consumed == 0
    assert parsed_headers == {}


def test_bytes_after_headers_are_not_consumed():
    data = b"Host: localhost:42069\r\n\r\nBODY"

    consumed, parsed_headers = head_parser(data)

    assert parsed_headers == {
        "host": "localhost:42069",
    }
    assert consumed == data.index(b"\r\n\r\n") + 4
    assert data[consumed:] == b"BODY"


# --------------------------------------------------
# 2. Invalid header tests
# --------------------------------------------------

def test_header_without_colon_raises_error():
    data = b"InvalidHeader\r\n\r\n"

    with pytest.raises(ValueError, match="missing colon"):
        head_parser(data)


@pytest.mark.parametrize(
    "data",
    [
        b"       Host: localhost:42069\r\n\r\n",
        b"Host : localhost:42069\r\n\r\n",
        b"Host\t: localhost:42069\r\n\r\n",
    ],
)
def test_invalid_header_name_whitespace(data):
    with pytest.raises(ValueError, match="Invalid header name"):
        head_parser(data)


def test_invalid_non_ascii_header_name():
    data = b"H\xc2\xa9st: localhost:42069\r\n\r\n"

    with pytest.raises(ValueError, match="Invalid header name"):
        head_parser(data)


@pytest.mark.parametrize(
    "invalid_name",
    [
        b"Bad(Key",
        b"Bad Key",
        b"Bad/Key",
        b"",
    ],
)
def test_invalid_header_name_characters(invalid_name):
    data = invalid_name + b": value\r\n\r\n"

    with pytest.raises(ValueError, match="Invalid header name"):
        head_parser(data)


# --------------------------------------------------
# 3. Case-insensitive header names
# --------------------------------------------------

def test_header_keys_are_lowercase():
    data = (
        b"HoSt: localhost:42069\r\n"
        b"CoNtEnT-LeNgTh: 123\r\n"
        b"\r\n"
    )

    consumed, parsed_headers = head_parser(data)

    assert consumed == len(data)
    assert parsed_headers == {
        "host": "localhost:42069",
        "content-length": "123",
    }


def test_header_names_are_case_insensitive():
    data = (
        b"HOST: localhost:42069\r\n"
        b"host: example.com\r\n"
        b"\r\n"
    )

    _, parsed_headers = head_parser(data)

    # Both names normalize to the same key.
    # For this dict-based implementation, the later value wins.
    assert parsed_headers == {
    "host": "localhost:42069, example.com",
}


# --------------------------------------------------
# 4. Headers.parser() tests
# --------------------------------------------------

def test_parser_stores_all_headers_and_marks_done():
    headers = Headers()

    data = (
        b"Host: localhost:42069\r\n"
        b"User-Agent: curl\r\n"
        b"\r\n"
    )

    consumed = headers.parser(data)

    assert consumed == len(data)
    assert headers.headers == {
        "host": "localhost:42069",
        "user-agent": "curl",
    }
    assert headers.state == ParserState.DONE


def test_parser_returns_zero_for_incomplete_data():
    headers = Headers()

    consumed = headers.parser(b"Host: localhost")

    assert consumed == 0
    assert headers.headers == {}
    assert headers.state == ParserState.INITIALIZED


def test_parser_returns_zero_after_done():
    headers = Headers()

    headers.parser(b"Host: localhost\r\n\r\n")

    consumed = headers.parser(b"User-Agent: curl\r\n\r\n")

    assert consumed == 0
    assert headers.headers == {
        "host": "localhost",
    }
    assert headers.state == ParserState.DONE


def test_parser_handles_empty_header_section():
    headers = Headers()

    consumed = headers.parser(b"\r\n")

    assert consumed == 2
    assert headers.headers == {}
    assert headers.state == ParserState.DONE


# --------------------------------------------------
# 5. req_from_reader() tests
# --------------------------------------------------

@pytest.mark.parametrize("chunk_size", [1, 2, 3, 8, 128])
def test_reader_parses_headers_across_different_chunk_sizes(chunk_size):
    data = (
        b"Host: localhost:42069\r\n"
        b"User-Agent: curl\r\n"
        b"Accept: */*\r\n"
        b"\r\n"
    )

    reader = BytesIO(data)
    headers = req_from_reader(reader, chunk_size=chunk_size)

    assert headers.headers == {
        "host": "localhost:42069",
        "user-agent": "curl",
        "accept": "*/*",
    }
    assert headers.state == ParserState.DONE


def test_reader_handles_empty_header_section():
    reader = BytesIO(b"\r\n")

    headers = req_from_reader(reader)

    assert headers.headers == {}
    assert headers.state == ParserState.DONE


def test_reader_raises_error_on_unexpected_eof():
    reader = BytesIO(b"Host: localhost")

    with pytest.raises(ValueError, match="Unexpected EOF"):
        req_from_reader(reader, chunk_size=4)

def test_multiple_values_for_same_header():
    data = (
        b"Set-Person: lane-loves-go\r\n"
        b"Set-Person: prime-loves-zig\r\n"
        b"Set-Person: tj-loves-ocaml\r\n"
        b"\r\n"
    )

    consumed, parsed_headers = head_parser(data)

    assert consumed == len(data)
    assert parsed_headers == {
        "set-person": (
            "lane-loves-go, prime-loves-zig, tj-loves-ocaml"
        )
    }


def test_existing_header_value_is_appended():
    existing = {"set-person": "existing-value"}

    data = b"Set-Person: new-value\r\n\r\n"

    consumed, parsed_headers = head_parser(data, existing)

    assert consumed == len(data)
    assert parsed_headers == {
        "set-person": "existing-value, new-value"
    }