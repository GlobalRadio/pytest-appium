import time
import requests


def get_json(url, headers: dict=None):
    r = requests.get(url, headers=headers)
    return r.json()


def post_json(url, data, headers: dict=None):
    r = requests.post(url, json=data, headers=headers)
    return r.json()


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
