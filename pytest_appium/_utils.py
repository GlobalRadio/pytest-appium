import json
import urllib  #.request
import time


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


def wait_for(
    func_attempt,
    func_is_ok=lambda response: response,
    func_generate_exception=lambda response: Exception('wait failed'),
    trys=5,
    sleep_duration=1,
):
    """
    Example:
        wait_for(
            func_attempt=lambda: get_data(),
            func_is_ok=lambda response: response.status_code == 'ok',
            func_generate_exception=lambda response: Exception('it broken {}'.format(response.message)),
        )

        Will repeat get_data() up to 3 times. Each time checking the return object from get_data() with func_is_ok.
        If it's not ok. Retry.
        If no success, func_generate_exception is called with the last response object.
    """
    for _ in range(int(trys)):
        try:
            response = func_attempt()
            if func_is_ok(response):
                return
        except Exception:
            pass
        time.sleep(float(sleep_duration))
    raise func_generate_exception(response)
