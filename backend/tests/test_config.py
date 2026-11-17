from app.main import allowed_frontend_origins


def test_allowed_frontend_origins_supports_both_localhost_ports():
    result = allowed_frontend_origins(
        "http://localhost:5500,http://localhost:5501"
    )

    assert result == [
        "http://127.0.0.1:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5500",
        "http://localhost:5501",
    ]


def test_allowed_frontend_origins_removes_duplicates_and_whitespace():
    result = allowed_frontend_origins(
        " https://skillswap.example/, https://skillswap.example "
    )

    assert result == ["https://skillswap.example"]