import json
import urllib  #.request


def _decode_response(response):
    data = response.read()
    try:
        encoding = response.info().get_content_charset('utf-8')
    except AttributeError:
        encoding = 'utf-8'
    return json.loads(data.decode(encoding))


def get_json(url):
    return _decode_response(urllib.request.urlopen(url))


def post_json(url, data):
    try:
        return _decode_response(
            urllib.request.urlopen(
                urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf8'),
                    headers={'content-type': 'application/json'},
                )
            )
        )
    except urllib.error.HTTPError as ex:
        return _decode_response(ex)