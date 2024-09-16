import json

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from decouple import config

from base64 import b64decode, b64encode

from django.core.serializers.json import DjangoJSONEncoder


def encrypt_data(data):
    key = config('ENCRYPTION_KEY')
    vector = config('ENCRYPTION_VECTOR')
    key_in_bytes = b64decode(key)
    iv = b64decode(vector)
    json_data = json.dumps(
        data,
        sort_keys=True,
        indent=1,
        cls=DjangoJSONEncoder
    )
    data_in_byte = bytes(json_data, 'utf-8')
    cipher = AES.new(key_in_bytes, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(pad(data_in_byte, AES.block_size))
    data = b64encode(encrypted_data).decode('utf-8')
    # result = json.dumps({'key': key, 'vector': vector, 'data': data})
    return data


def decrypt_data(options):
    try:
        b64_data = json.loads(options)
    except:
        b64_data = json.loads((json.dumps(options)))
    key = b64decode(config('ENCRYPTION_KEY'))
    iv = b64decode(config('ENCRYPTION_VECTOR'))
    data = b64decode(options)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data_in_byte = unpad(cipher.decrypt(data), AES.block_size)
    decoded_data = data_in_byte.decode('utf-8')
    # print(type(decoded_data))
    return json.loads(decoded_data)

# data = json.loads(b'{\r\n    "application_id": "TP-FD-0007"\r\n}')
# print(encrypt_data(data))