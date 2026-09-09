import json
import os

import boto3


def get_table():
    return boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


def handler(event, context):
    table = get_table()

    records = event.get("Records", [])

    for record in records:
        payload = json.loads(record["body"])
        order_id = payload["order_id"]

        table.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "PROCESSING"},
        )

        # A production implementation could invoke inventory,
        # payment, and fulfillment services here.

        table.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "COMPLETED"},
        )

    return {"processed": len(records)}