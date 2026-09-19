from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import requests
import my_pb2
import output_pb2
import jwt

app = Flask(__name__)

AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'

def encrypt_message(plaintext):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    padded_message = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded_message)

def get_jwt_from_majorlogin(access_token, open_id):
    try:
        game_data = my_pb2.GameData()
        game_data.timestamp = "2025-08-30 05:19:21"
        game_data.game_name = "free fire"
        game_data.game_version = 1
        game_data.version_code = "1.114.13"
        game_data.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
        game_data.device_type = "Handheld"
        game_data.network_provider = "ATM Mobils"
        game_data.connection_type = "WIFI"
        game_data.screen_width = 1280
        game_data.screen_height = 960
        game_data.dpi = "240"
        game_data.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 2"
        game_data.total_ram = 5951
        game_data.gpu_name = "Adreno (TM) 640"
        game_data.gpu_version = "OpenGL ES 3.2"
        game_data.user_id = "Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f"
        game_data.ip_address = "105.235.139.91"
        game_data.language = "hi"
        game_data.open_id = open_id
        game_data.access_token = access_token
        game_data.platform_type = 4
        game_data.field_99 = "4"
        game_data.field_100 = "4"

        serialized_data = game_data.SerializeToString()
        encrypted_data = encrypt_message(serialized_data)
        hex_encrypted_data = binascii.hexlify(encrypted_data).decode('utf-8')

        url = "https://loginbp.ppmainecoonghj.com/MajorLogin"
        headers = {
            "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept-Encoding": "deflate, gzip",
            "X-GA-SV": "1789535859",
            "Authorization": "Bearer",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB55",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1"
        }
        edata = bytes.fromhex(hex_encrypted_data)

        response = requests.post(url, data=edata, headers=headers, verify=False, timeout=10)

        if response.status_code == 200:
            token_value = None
            try:
                example_msg = output_pb2.Garena_420()
                example_msg.ParseFromString(response.content)
                if example_msg.token:
                    token_value = example_msg.token
            except Exception:
                pass

            if not token_value:
                text_resp = response.text
                jwt_idx = text_resp.find("eyJ")
                if jwt_idx != -1:
                    token_candidate = text_resp[jwt_idx:]
                    dot_idx = token_candidate.find(".", token_candidate.find(".") + 1)
                    if dot_idx != -1:
                        token_value = token_candidate[:dot_idx + 44]

            if token_value:
                try:
                    decoded_token = jwt.decode(token_value, options={"verify_signature": False})
                except Exception:
                    decoded_token = {}

                return {
                    "account_id": decoded_token.get("account_id"),
                    "account_name": decoded_token.get("nickname"),
                    "open_id": open_id,
                    "access_token": access_token,
                    "platform": decoded_token.get("external_type"),
                    "region": decoded_token.get("lock_region"),
                    "status": "success",
                    "token": token_value
                }, None
    except Exception as e:
        return None, str(e)

    return None, "MajorLogin failed to get token"

@app.route('/token', methods=['GET', 'POST'])
def oauth_guest():
    # GET और POST दोनों से पैरामीटर सपोर्ट करेगा
    if request.method == 'POST':
        json_data = request.get_json(silent=True) or {}
        uid = json_data.get('uid') or request.form.get('uid')
        password = json_data.get('password') or request.form.get('password')
    else:
        uid = request.args.get('uid')
        password = request.args.get('password')

    if not uid or not password:
        return jsonify({"message": "Missing uid or password"}), 400

    oauth_url = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
    payload = {
        "client_id": 100067,
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_type": 2,
        "device_id": "02-344afb0e-593c-40b7-92f2-171972f74807",
        "password": password,
        "response_type": "token",
        "uid": int(uid) if str(uid).isdigit() else uid,
    }
    headers = {
        "User-Agent": "GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)",
        "Connection": "Keep-Alive",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Cookie": "datadome=y23Z3X17pgkMHEt5zY8dqxC6BIf7WJMgC0RXNbqifHT7t9zajKe_hegFb1Ie9_7JixXpz7FRGVodOn~mWPk_NrqIIhUOXDYqKOahzoRQcyEy77GWEMcdA9_MqPJeM5qv",
        "Host": "100067.connect.garena.com",
    }

    try:
        oauth_response = requests.post(oauth_url, json=payload, headers=headers, timeout=10, verify=False)
        oauth_data = oauth_response.json()
    except Exception as e:
        return jsonify({"message": f"OAuth Error: {str(e)}"}), 500

    if oauth_response.status_code != 200 or oauth_data.get('code') != 0:
        return jsonify({"message": "OAuth failed", "details": oauth_data}), 400

    token_data = oauth_data.get('data', {})
    access_token = token_data.get('access_token')
    open_id = token_data.get('open_id')

    if not access_token or not open_id:
        return jsonify({"message": "OAuth response missing access_token or open_id"}), 500

    result, err = get_jwt_from_majorlogin(access_token, open_id)
    if err:
        return jsonify({"message": err}), 400

    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1080, debug=False)
