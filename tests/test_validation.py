# import sys

# sys.path.insert(0, "src/create_order")

# import app


# def test_invalid_body():
#     result = app.handler(
#         {"body": "{}"},
#         None,
#     )

#     assert result["statusCode"] == 422


# def test_invalid_json():
#     result = app.handler(
#         {"body": "{invalid-json"},
#         None,
#     )

#     assert result["statusCode"] == 400


import importlib.util
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


create_order = load_module(
    "create_order_app",
    ROOT_DIR / "src" / "create_order" / "app.py",
)

process_order = load_module(
    "process_order_app",
    ROOT_DIR / "src" / "process_order" / "app.py",
)


class FakeTable:
    def __init__(self):
        self.put_calls = []
        self.update_calls = []

    def put_item(self, **kwargs):
        self.put_calls.append(kwargs)

    def update_item(self, **kwargs):
        self.update_calls.append(kwargs)


class FakeQueue:
    def __init__(self):
        self.messages = []

    def send_message(self, **kwargs):
        self.messages.append(kwargs)


def test_invalid_json():
    result = create_order.handler(
        {"body": "{invalid-json"},
        None,
    )

    assert result["statusCode"] == 400

    body = json.loads(result["body"])

    assert body["error"] == "Invalid JSON"


def test_missing_required_fields():
    result = create_order.handler(
        {"body": "{}"},
        None,
    )

    assert result["statusCode"] == 422

    body = json.loads(result["body"])

    assert body["error"] == "customer_id and items are required"


def test_create_order_success(monkeypatch):
    table = FakeTable()
    queue = FakeQueue()

    monkeypatch.setattr(
        create_order,
        "get_table",
        lambda: table,
    )

    monkeypatch.setattr(
        create_order,
        "get_queue",
        lambda: queue,
    )

    monkeypatch.setenv(
        "QUEUE_URL",
        "https://example.com/order-queue",
    )

    event = {
        "body": json.dumps(
            {
                "customer_id": "DEMO-100",
                "items": [
                    {
                        "sku": "SKU-001",
                        "quantity": 2,
                    }
                ],
            }
        )
    }

    result = create_order.handler(event, None)

    assert result["statusCode"] == 202

    response_body = json.loads(result["body"])

    assert response_body["customer_id"] == "DEMO-100"
    assert response_body["status"] == "RECEIVED"
    assert response_body["order_id"]
    assert response_body["created_at"]

    assert len(table.put_calls) == 1

    stored_item = table.put_calls[0]["Item"]

    assert stored_item["order_id"] == response_body["order_id"]
    assert stored_item["status"] == "RECEIVED"

    assert len(queue.messages) == 1

    queue_message = queue.messages[0]

    assert (
        queue_message["QueueUrl"]
        == "https://example.com/order-queue"
    )

    message_body = json.loads(queue_message["MessageBody"])

    assert message_body["order_id"] == response_body["order_id"]


def test_process_order_success(monkeypatch):
    table = FakeTable()

    monkeypatch.setattr(
        process_order,
        "get_table",
        lambda: table,
    )

    event = {
        "Records": [
            {
                "body": json.dumps(
                    {
                        "order_id": "ORDER-123",
                    }
                )
            }
        ]
    }

    result = process_order.handler(event, None)

    assert result["processed"] == 1
    assert len(table.update_calls) == 2

    first_update = table.update_calls[0]

    assert (
        first_update["ExpressionAttributeValues"][":s"]
        == "PROCESSING"
    )

    second_update = table.update_calls[1]

    assert (
        second_update["ExpressionAttributeValues"][":s"]
        == "COMPLETED"
    )


def test_process_order_empty_batch(monkeypatch):
    table = FakeTable()

    monkeypatch.setattr(
        process_order,
        "get_table",
        lambda: table,
    )

    result = process_order.handler(
        {"Records": []},
        None,
    )

    assert result["processed"] == 0
    assert table.update_calls == []