import datetime
import json
import os
import uuid

import boto3


def get_table():
    return boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


def get_queue():
    return boto3.client("sqs")


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON"})

    if not body.get("customer_id") or not body.get("items"):
        return response(
            422,
            {"error": "customer_id and items are required"},
        )

    order_id = str(uuid.uuid4())

    item = {
        "order_id": order_id,
        "customer_id": body["customer_id"],
        "items": body["items"],
        "status": "RECEIVED",
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    table = get_table()
    queue = get_queue()

    table.put_item(
        Item=item,
        ConditionExpression="attribute_not_exists(order_id)",
    )

    queue.send_message(
        QueueUrl=os.environ["QUEUE_URL"],
        MessageBody=json.dumps({"order_id": order_id}),
    )

    return response(202, item)