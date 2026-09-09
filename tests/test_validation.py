import sys

sys.path.insert(0, "src/create_order")

import app


def test_invalid_body():
    result = app.handler(
        {"body": "{}"},
        None,
    )

    assert result["statusCode"] == 422


def test_invalid_json():
    result = app.handler(
        {"body": "{invalid-json"},
        None,
    )

    assert result["statusCode"] == 400