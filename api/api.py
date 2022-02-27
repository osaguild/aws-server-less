import json, os, uuid, decimal
from datetime import datetime, timezone
import boto3

ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["TABLE_NAME"])

HEADERS = {
    "Access-Control-Allow-Origin": "*",
}

# this custom class is to handle decimal.Decimal objects in json.dumps()
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def select_data(event, context):
    """
    handler for GET /api
    """
    try:
        response = table.scan()

        status_code = 200
        resp = response.get("Items")
    except Exception as e:
        status_code = 500
        resp = {"description": f"Internal server error. {str(e)}"}
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(resp, cls=DecimalEncoder)
    }

def create_data(event, context):
    """
    handler for POST /api
    """
    try:
        body = event.get("body")
        if not body:
            raise ValueError("Invalid request. The request body is missing!")
        body = json.loads(body)

        for key in ["param_1", "param_2", "param_3", "param_4"]:
            if not body.get(key):
                raise ValueError(f"{key} is empty")

        item = {
            "id": uuid.uuid4().hex,
            "param_1": body["param_1"],
            "param_2": body["param_2"],
            "param_3": body["param_3"],
            "param_4": body["param_4"],
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")
        }
        response = table.put_item(Item=item)

        status_code = 201
        resp = {"description": "Successfully added a new data"}
    except ValueError as e:
        status_code = 400
        resp = {"description": f"Bad request. {str(e)}"}
    except Exception as e:
        status_code = 500
        resp = {"description": str(e)}
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(resp)
    }

def update_data(event, context):
    """
    handler for POST /api/{id}
    """
    try:
        path_params = event.get("pathParameters", {})
        id = path_params.get("id", "")
        if not id:
            raise ValueError("Invalid request. The path parameter 'id' is missing")
        
        response = table.update_item(
            Key={"id": id},
            UpdateExpression=f"SET param_2 = :param_2",
            ExpressionAttributeValues={
                ':param_1': 'updated',
            }
        )

        status_code = 200
        resp = {"description": "OK"}
    except ValueError as e:
        status_code = 400
        resp = {"description": f"Bad request. {str(e)}"}
    except Exception as e:
        status_code = 500
        resp = {"description": str(e)}
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(resp)
    }

def delete_data(event, context):
    """
    handler for DELETE /api/{id}
    """
    try:
        path_params = event.get("pathParameters", {})
        id = path_params.get("id", "")
        if not id:
            raise ValueError("Invalid request. The path parameter 'id' is missing")
        
        response = table.delete_item(
            Key={"id": id}
        )

        status_code = 204
        resp = {"description": "Successfully deleted."}
    except ValueError as e:
        status_code = 400
        resp = {"description": f"Bad request. {str(e)}"}
    except Exception as e:
        status_code = 500
        resp = {"description": str(e)}
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(resp)
    }
