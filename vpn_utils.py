import os
import json
import uuid
import random
import string
import requests
from dotenv import load_dotenv

load_dotenv()


class X3:
    def __init__(self, host=None, login=None, password=None, base=None):

        self.host = (host or os.getenv("X3_HOST", "http://148.222.186.138:39922")).rstrip("/")
        base_raw = base or os.getenv("X3_BASE", "K1NUNCbkeGEEBOblC2")
        self.base = "/" + base_raw.lstrip("/")

        self.login = login or os.getenv("LOGIN", "")
        self.password = password or os.getenv("PASSWORD", "")

        self.s = requests.Session()
        self.token = None

        self.login_api()

    # ---------------------------------------------------------
    # ЛОГИН — СТАРЫЙ URL, КОТОРЫЙ У ТЕБЯ РЕАЛЬНО РАБОТАЕТ
    # ---------------------------------------------------------
    def login_api(self):
        url = f"{self.host}{self.base}/login"
        r = self.s.post(url, json={"username": self.login, "password": self.password})

        data = r.json()
        if data.get("success"):
            self.token = r.cookies.get("3x-ui")
            return True

        raise RuntimeError("LOGIN FAILED")    # ---------------------------------------------------------
    # ПРАВИЛЬНЫЙ API для inbound'ов — /panel/api/...
    # ---------------------------------------------------------
    def list_inbounds(self):
        url = f"{self.host}{self.base}/panel/api/inbounds/list"
        print("GET INBOUNDS:", url)

        r = self.s.get(url)
        print("LIST STATUS:", r.status_code)
        print("LIST TEXT:", r.text[:200])

        try:
            return r.json()
        except:
            raise RuntimeError("INBOUNDS RESPONSE NOT JSON")

    # ---------------------------------------------------------
    # ДОБАВЛЕНИЕ КЛИЕНТА
    # ---------------------------------------------------------
    def add_client(self, inbound_id: int, user_id: int):
        # Обязательно повторный логин — панель часто дропает сессию
        self.login_api()

        # 1. Получаем inbound'ы
        data = self.list_inbounds()
        if not data.get("success"):
            return None

        inbound = next((i for i in data["obj"] if i["id"] == inbound_id), None)
        if inbound is None:
            return None

        # 2. Разбор settings
        try:
            settings = json.loads(inbound["settings"])
        except:
            return None

        clients = settings.get("clients", [])

        # 3. Создаём нового клиента
        new_uuid = str(uuid.uuid4())
        new_subid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

        new_client = {
            "id": new_uuid,
            "email": f"user_{user_id}",
            "remark": f"user_{user_id}",
            "flow": "",
            "limitIp": 0,
            "totalGB": 0,
            "expiryTime": 0,
            "enable": True,
            "tgId": "",
            "subId": new_subid,
            "comment": "",
            "reset": 0
        }

        clients.append(new_client)
        settings["clients"] = clients

        # 4. Обновлённый inbound payload
        payload = {
            "id": inbound_id,
            "up": inbound["up"],
            "down": inbound["down"],
            "total": inbound["total"],
            "remark": inbound["remark"],
            "enable": inbound["enable"],
            "expiryTime": inbound["expiryTime"],
            "listen": inbound.get("listen", ""),
            "port": inbound["port"],
            "protocol": inbound["protocol"],
            "settings": json.dumps(settings, ensure_ascii=False),
            "streamSettings": inbound["streamSettings"],
            "tag": inbound["tag"]
        }

        # ВАЖНО — правильный URL update
        url = f"{self.host}{self.base}/panel/api/inbounds/update/{inbound_id}"

        # ВАЖНО — передаём cookie токен
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": f"3x-ui={self.token}"
        }

        r = self.s.post(url, data=payload, headers=headers)

        if '"success":true' in r.text:
            return new_uuid

        return None

    def generate_link(self, client_uuid: str, user_id: int) -> str:
        host = "148.222.186.138"
        port = 443
        pbk = "lfA7_Apsl8-tTxNLS3RfPq2qxrVxfXTLhoLmGd_uKCg"
        sni = "max.ru"
        sid = "b5430da5739bd4df"

        return (
            f"vless://{client_uuid}@{host}:{port}"
            f"?type=tcp"
            f"&encryption=none"
            f"&security=reality"
            f"&pbk={pbk}"
            f"&fp=chrome"
            f"&sni={sni}"
            f"&sid={sid}"
            f"&spx=%2F"
            f"#BlackGate-{user_id}"
        )
