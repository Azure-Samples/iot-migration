# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import asyncio
from azure.iot.device.aio import ProvisioningDeviceClient
import os
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
import uuid
import jwt
import datetime

messages_to_send = 10
provisioning_host = "global.azure-devices-provisioning.net"  # Global device endpoint
id_scope = "" # ID Scope of Device Provisioning Service
registration_id = ""  # Unique Device ID, should match with the enrollmnt ID in DPS
symmetric_key = "" # Generated Symmetric key of the device


async def main():
    provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
        provisioning_host=provisioning_host,
        registration_id=registration_id,
        id_scope=id_scope,
        symmetric_key=symmetric_key,
    )

    ######### Generate signed JWT using ECC private key #########
    private_key_file="./ec_private.pem"
    algorithm="ES256"
    with open(private_key_file, "r") as f:
        private_key = f.read()

    token = {
        "iat": datetime.datetime.now(tz=datetime.timezone.utc),
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=14400),
        "provisioning_host": provisioning_host,
        "id_scope": id_scope,
        "registration_id": registration_id
    }
    encodedjwt = jwt.encode(token, private_key, algorithm=algorithm)

    ######### Send signed JWT as provisioning payload #########
    provisioning_device_client.provisioning_payload = { "jwt":encodedjwt}

    registration_result = await provisioning_device_client.register()

    print("The complete registration result is")
    print(registration_result.registration_state)

    if registration_result.status == "assigned":
        print("Will send telemetry from the provisioned device")
        device_client = IoTHubDeviceClient.create_from_symmetric_key(
            symmetric_key=symmetric_key,
            hostname=registration_result.registration_state.assigned_hub,
            device_id=registration_result.registration_state.device_id,
        )
        # Connect the client.
        await device_client.connect()

        async def send_test_message(i):
            print("sending message #" + str(i))
            msg = Message("test wind speed " + str(i))
            msg.message_id = uuid.uuid4()
            await device_client.send_message(msg)
            print("done sending message #" + str(i))

        # send `messages_to_send` messages in parallel
        await asyncio.gather(*[send_test_message(i) for i in range(1, messages_to_send + 1)])

        # finally, disconnect
        await device_client.disconnect()
    else:
        print("Can not send telemetry from the provisioned device")


if __name__ == "__main__":
    asyncio.run(main())

    # If using Python 3.6 use the following code instead of asyncio.run(main()):
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # loop.close()