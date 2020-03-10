
import httpx
from .datastructures import MultiDict, HeaderDict
from urllib.parse import urlencode

class Request:
    def __init__(self, method, url, data=None,
                 params=None,
                 auth_path=None,
                 stream_output=False,
                **kwargs):
        # Default empty dicts for dict params.
        params = {} if params is None else params

        self.method = method
        self.url = url
        self.headers = HeaderDict()
        self.params = params or MultiDict()
        self.auth_path = auth_path
        self.stream_output = stream_output
        self._body = ""
        self.data = data
        self.body = data
        # This is a dictionary to hold information that is used when
        # processing the request. What is inside of ``context`` is open-ended.
        # For example, it may have a timestamp key that is used for holding
        # what the timestamp is when signing the request. Note that none
        # of the information that is inside of ``context`` is directly
        # sent over the wire; the information is only used to assist in
        # creating what is sent over the wire.
        self.context = {}

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, data):
        self._body = data
        self._finalize_body()

    def _to_utf8(self, item):
        key, value = item
        if isinstance(key, str):
            key = key.encode('utf-8')
        if isinstance(value, str):
            value = value.encode('utf-8')
        return key, value

    def _finalize_body(self):
        """Prepares the given HTTP body data."""
        body = self._body
        if body == b'':
            body = None

        if isinstance(body, dict):
            params = [self._to_utf8(item) for item in body.items()]
            body = urlencode(params, doseq=True)

        if isinstance(body, str):
            body = body.encode('utf-8')

        self.body = body

    def get_client(self):
        try:
            return httpx.AsyncClient()
        except:
            return httpx

    async def __call__(self):
        client = self.get_client()
        if not self.stream_output:
            ret = await client.get(self.method.upper(),
                self.url,
                headers=self.headers.allitems(),
                params=self.params.allitems())
            return ret
        else:
            async with client.stream(self.method.upper(),
                self.url,
                headers=self.headers.allitems(),
                params=self.params.allitems()) as response:
                async for chunk in response.aiter_bytes():
                    pass

