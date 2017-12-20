import json
import urllib.request


def get_json(url):
    request = urllib.request.urlopen(url)
    data = request.read()
    encoding = request.info().get_content_charset('utf-8')
    return json.loads(data.decode(encoding))
