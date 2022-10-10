import logging
import azure.functions as func
import jwt
import json
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('JWT validation started...')
    
    body = req.get_json()
    logging.info(body)
    encodedjwt = body.get("deviceRuntimeContext").get("payload").get("jwt")
    logging.info(f"JWT Token: {encodedjwt}")
    algorithm="ES256"
    public_key=os.environ["DEVICE_PUBLIC_KEY"]

    decodedjwt = jwt.decode(encodedjwt, public_key,algorithms=[algorithm])
    logging.info(decodedjwt.get("registration_id"))

    dpsresponse = {}
    iotHubName = os.environ['IOT_HUB_HOSTNAME']
    dpsresponse["iotHubHostName"] = iotHubName
    dpsresponse["initialTwin"] = {}
    return func.HttpResponse(body=json.dumps(dpsresponse), status_code=200) 
