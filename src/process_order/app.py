import json,os,boto3
table=boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
def handler(event,context):
    for record in event.get("Records",[]):
        payload=json.loads(record["body"]); oid=payload["order_id"]
        table.update_item(Key={"order_id":oid},UpdateExpression="SET #s=:s",ExpressionAttributeNames={"#s":"status"},ExpressionAttributeValues={":s":"PROCESSING"})
        # Real implementation would call inventory/payment/fulfillment services here.
        table.update_item(Key={"order_id":oid},UpdateExpression="SET #s=:s",ExpressionAttributeNames={"#s":"status"},ExpressionAttributeValues={":s":"COMPLETED"})
    return {"processed":len(event.get("Records",[]))}
