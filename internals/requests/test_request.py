from internals.requests.request import (
    parser_request_line,
    request_from_reader,
)
import pytest
    
def test_invalid_no_of_components():
    request = (
        "/coffee HTTP/1.1\r\n"
        "Host: localhost:42069\r\n"
        "\r\n"
    )
    with pytest.raises(ValueError, match="expected 3 components"):
        parser_request_line(request)

def test_valid_request_line():
    request = "POST /coffee HTTP/1.1"

    result = parser_request_line(request)

    assert result.method == "POST"
    assert result.request_target == "/coffee"
    assert result.http_version == "HTTP/1.1"

def test_valid_method():
    request = "GeT /coffee HTTP/1.1"

    with pytest.raises(ValueError, match="Not a valid HTTP method"):
        parser_request_line(request)

def test_HTTP_Validator():
    request="PUT /coffee HTTP/1.3"
    with pytest.raises(ValueError,match="Not a valid HTTP version"):
        parser_request_line(request)
    
# POST /coffee HTTP/1.1
# Host: localhost:42069
# Content-Type: application/json
# Content-Length: 22

# {"flavor":"dark mode"}

    