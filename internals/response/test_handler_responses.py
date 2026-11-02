import http.client
import pytest


BASE_HOST = "localhost"
PORT = 42069


@pytest.mark.parametrize(
    "path, expected_status, expected_reason, expected_body",
    [
        (
            "/coffee",
            200,
            "OK",
            b"All good frfr\n",
        ),
        (
            "/yourproblem",
            400,
            "Bad Request",
            b"Your problem is not my problem\n",
        ),
        (
            "/myproblem",
            500,
            "Internal Server Error",
            b"Woopsie, my bad\n",
        ),
    ],
)
def test_handler_responses(
    path,
    expected_status,
    expected_reason,
    expected_body,
):
    conn = http.client.HTTPConnection(
        BASE_HOST,
        PORT,
        timeout=5,
    )

    try:
        # Send HTTP request
        conn.request("GET", path)

        # Receive HTTP response
        response = conn.getresponse()
        body = response.read()

        # Verify status line
        assert response.status == expected_status
        assert response.reason == expected_reason

        # Verify response headers
        assert response.getheader("Content-Type") == "text/plain"

        content_length = int(response.getheader("Content-Length"))
        assert content_length == len(expected_body)

        # Verify response body
        assert body == expected_body

    finally:
        conn.close()