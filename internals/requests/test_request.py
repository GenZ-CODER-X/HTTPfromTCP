
import pytest

from internals.requests.request import (
    ParserState,
    Request,
    parser_request_line,
    request_from_reader,
)
class ChunkReader:
    """Simulates a stream that returns a limited number of bytes per read."""

    def __init__(self, data: str | bytes, num_bytes_per_read: int):
        if num_bytes_per_read <= 0:
            raise ValueError("Chunk size must be positive")

        if isinstance(data, str):
            data = data.encode("utf-8")

        self.data = data
        self.num_bytes_per_read = num_bytes_per_read
        self.pos = 0

    def read(self, size=-1):
        if self.pos >= len(self.data):
            return b""

        if size == 0:
            return b""

        if size is None or size < 0:
            size = self.num_bytes_per_read

        count = min(size, self.num_bytes_per_read)
        end = min(self.pos + count, len(self.data))

        chunk = self.data[self.pos:end]
        self.pos = end
        return chunk


# 1. Valid request line
def test_valid_request_line():
    data = b"POST /coffee HTTP/1.1\r\n"

    consumed, result = parser_request_line(data)

    assert consumed == len(data)
    assert result is not None
    assert result.method == "POST"
    assert result.request_target == "/coffee"
    assert result.http_version == "1.1"


# 2. Incomplete request line
def test_incomplete_request_line():
    consumed, result = parser_request_line(b"GET /cof")

    assert consumed == 0
    assert result is None


# 3. Missing CRLF
def test_request_line_without_crlf():
    consumed, result = parser_request_line(
        b"GET /coffee HTTP/1.1"
    )

    assert consumed == 0
    assert result is None


# 4. Wrong number of components
def test_invalid_no_of_components():
    with pytest.raises(ValueError, match="expected 3 components"):
        parser_request_line(b"/coffee HTTP/1.1\r\n")


# 5. Invalid method
def test_invalid_method():
    with pytest.raises(ValueError, match="Not a valid HTTP method"):
        parser_request_line(b"GeT /coffee HTTP/1.1\r\n")


# 6. Unsupported HTTP version
def test_invalid_http_version():
    with pytest.raises(ValueError, match="Not a valid HTTP version"):
        parser_request_line(b"GET /coffee HTTP/1.3\r\n")


# 7. Only consume the request line, not subsequent headers
def test_only_request_line_is_consumed():
    data = (
        b"GET /coffee HTTP/1.1\r\n"
        b"Host: localhost:42069\r\n"
    )

    consumed, result = parser_request_line(data)

    expected_line = b"GET /coffee HTTP/1.1\r\n"

    assert consumed == len(expected_line)
    assert consumed==expected_line
    assert result is not None
    assert data[consumed:] == b"Host: localhost:42069\r\n"


# 8. New requests start in INITIALIZED state
def test_initial_request_state():
    request = Request()

    assert request.state == ParserState.INITIALIZED
    assert request.request_line is None


# 9. Parsing transitions the request to DONE
def test_request_state_becomes_done():
    request = Request()

    consumed = request.parse(b"GET / HTTP/1.1\r\n")

    assert consumed == len(b"GET / HTTP/1.1\r\n")
    assert request.state == ParserState.DONE
    assert request.request_line is not None
    assert request.request_line.method == "GET"


# 10. Request parsing works with different read sizes
@pytest.mark.parametrize("chunk_size", [1, 3, 8, 128])
def test_streaming_with_different_chunk_sizes(chunk_size):
    raw_request = (
        b"GET /coffee HTTP/1.1\r\n"
        b"Host: localhost:42069\r\n"
        b"User-Agent: curl\r\n"
        b"\r\n"
    )

    reader = ChunkReader(raw_request, chunk_size)
    result = request_from_reader(reader, chunk_size=chunk_size)

    assert result.state == ParserState.DONE
    assert result.request_line is not None
    assert result.request_line.method == "GET"
    assert result.request_line.request_target == "/coffee"
    assert result.request_line.http_version == "1.1"


# 11. CRLF split across reads
def test_crlf_split_across_reads():
    reader = ChunkReader(
        b"GET /coffee HTTP/1.1\r\n",
        num_bytes_per_read=1,
    )

    result = request_from_reader(reader, chunk_size=1)

    assert result.request_line is not None
    assert result.request_line.request_target == "/coffee"
    assert result.state == ParserState.DONE


# 12. EOF before a complete request line
def test_eof_before_complete_request_line():
    reader = ChunkReader(
        b"GET /coffee HTTP/1.1",
        num_bytes_per_read=3,
    )

    with pytest.raises(ValueError, match="Unexpected EOF"):
        request_from_reader(reader, chunk_size=3)
