from flask import Flask, render_template, request, url_for
from os import environ as env
import os
import datetime
from time import mktime
import http.client
import struct
import socket
import typing
import json
import urllib
from urllib.parse import quote
from random import randint

JSON_MIME = 'application/json'

app = Flask(__name__)
app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))

DETA_PROJECT_KEY = env.get('DETA_PROJECT_KEY').split("_")

class DetaReqs:
    def __init__(self, project_key):
        self.project_id = project_key[0]
        self.project_token = project_key[1]
        self.project_key = '_'.join(project_key)
        self.__ttl_attribute = "__expires"
        self.base_path = "/v1/{0}/{1}".format(self.project_id, "clips")
        self.host = "database.deta.sh"
        self.timeout = 10
        self.keep_alive = True
        self.client = http.client.HTTPSConnection("database.deta.sh", timeout=self.timeout)
        
    def _is_socket_closed(self):
        if not self.client.sock:
            return True
        fmt = "B" * 7 + "I" * 21
        tcp_info = struct.unpack(
            fmt, self.client.sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 92)
        )
        # 8 = CLOSE_WAIT
        if len(tcp_info) > 0 and tcp_info[0] == 8:
            return True
        return False

    def _request(
        self,
        path: str,
        method: str,
        data: typing.Union[str, bytes, dict] = None,
        headers: dict = None,
        content_type: str = None,
        stream: bool = False,
    ):
        url = self.base_path + path
        headers = headers or {}
        headers["X-Api-Key"] = self.project_key
        if content_type:
            headers["Content-Type"] = content_type
        if not self.keep_alive:
            headers["Connection"] = "close"

        # close connection if socket is closed
        # fix for a bug in lambda
        try:
            if (
                self.client
                and os.environ.get("DETA_RUNTIME") == "true"
                and self._is_socket_closed()
            ):
                self.client.close()
        except:
            pass

        # send request
        body = json.dumps(data) if content_type == JSON_MIME else data

        # response
        res = self._send_request_with_retry(method, url, headers, body)
        status = res.status

        if status not in [200, 201, 202, 207]:
            # need to read the response so subsequent requests can be sent on the client
            res.read()
            if not self.keep_alive:
                self.client.close()
            ## return None if not found
            if status == 404:
                return status, None
            raise urllib.error.HTTPError(url, status, res.reason, res.headers, res.fp)

        ## if stream return the response and client without reading and closing the client
        if stream:
            return status, res

        ## return json if application/json
        payload = (
            json.loads(res.read())
            if JSON_MIME in res.getheader("content-type")
            else res.read()
        )

        if not self.keep_alive:
            self.client.close()
        return status, payload

    def _send_request_with_retry(
        self,
        method: str,
        url: str,
        headers: dict = None,
        body: typing.Union[str, bytes, dict] = None,
        retry=2,  # try at least twice to regain a new connection
    ):
        reinitializeConnection = False
        while retry > 0:
            try:
                if not self.keep_alive or reinitializeConnection:
                    self.client = http.client.HTTPSConnection(
                        host=self.host, timeout=self.timeout
                    )
                self.client.request(
                    method,
                    url,
                    headers=headers,
                    body=body,
                )
                res = self.client.getresponse()
                return res
            except http.client.RemoteDisconnected:
                reinitializeConnection = True
                retry -= 1
                
    def get(self, key: str):
        if key == "":
            raise ValueError("Key is empty")

        # encode key
        key = quote(key, safe="")
        _, res = self._request("/items/{}".format(key), "GET")
        return res or None

    def put(
        self,
        data: typing.Union[dict, list, str, int, bool],
        key: str = None,
        *,
        expire_in: int = None,
        expire_at: typing.Union[int, float, datetime.datetime] = None,
    ):
        if not isinstance(data, dict):
            data = {"value": data}
        else:
            data = data.copy()

        if key:
            data["key"] = key

        insert_ttl(data, self.__ttl_attribute, expire_in=expire_in, expire_at=expire_at)
        code, res = self._request(
            "/items", "PUT", {"items": [data]}, content_type=JSON_MIME
        )
        return res["processed"]["items"][0] if res and code == 207 else None
    
    def _fetch(
        self,
        query: typing.Union[dict, list] = None,
        buffer: int = None,
        last: str = None,
    ) -> typing.Optional[typing.Tuple[int, list]]:
        payload = {
            "limit": buffer,
            "last": last if not isinstance(last, bool) else None,
        }

        if query:
            payload["query"] = query if isinstance(query, list) else [query]

        code, res = self._request("/query", "POST", payload, content_type=JSON_MIME)
        return code, res

    def fetch(
        self,
        query: typing.Union[dict, list] = None,
        *,
        limit: int = 1000,
        last: str = None,
    ):
        _, res = self._fetch(query, limit, last)

        paging = res.get("paging")

        return {"size": paging.get("size"), "last": paging.get("last"), "items": res.get("items")}

def insert_ttl(item, ttl_attribute, expire_in=None, expire_at=None):
    if expire_in and expire_at:
        raise ValueError("both expire_in and expire_at provided")
    if not expire_in and not expire_at:
        return

    if expire_in:
        expire_at = datetime.datetime.now() + datetime.timedelta(seconds=expire_in)

    if isinstance(expire_at, datetime.datetime):
        expire_at = expire_at.replace(microsecond=0).timestamp()

    if not isinstance(expire_at, (int, float)):
        raise TypeError("expire_at should one one of int, float or datetime")

    item[ttl_attribute] = int(expire_at)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/putclip', methods=['POST'])
def put_copy():
    data = str(request.json['putdata'])
    obj = DetaReqs(DETA_PROJECT_KEY)
    
    res = obj.fetch()
    keys = [i['key'] for i in res["items"]]
    while res["last"]:
        res = obj.fetch(last=res["last"])
        keys += [i['key'] for i in res["items"]]
    
    key_decided = False
    while not key_decided:
        key = randint(0, 999999)
        if key in keys:
            continue
        key_decided = True
        
    req_data = {
        "data": data,
    }
    
    result = obj.put(req_data, key='0'*(6-len(str(key)))+str(key), expire_in=60)
    return result

@app.route('/api/getclip', methods=['POST'])
def get_copy():
    key = str(request.json['key'])
    obj = DetaReqs(DETA_PROJECT_KEY)
    
    result = obj.get(key)
    return result

if __name__ == "__main__":
    app.run()