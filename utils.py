import regex
from loguru import logger
import os
import requests
import time
from cachetools import cached, LRUCache

# ===========================================
#                  Output
# ===========================================
LOG_PATH = 'log'
os.makedirs(LOG_PATH, exist_ok=True)
TRACE = logger.add(LOG_PATH + '/{time}.log')


def is_comment(content: str):
    strip_content = content.strip()
    if strip_content.startswith('//') or strip_content.startswith('/*') or \
            strip_content.startswith('*'):
        return True
    return False


def create_missing_dirs(path: str):
    os.makedirs(path, exist_ok=True)


def logger_add(path: str, name: str):
    create_missing_dirs(path)
    return logger.add(os.path.join(path, name))


def log_message(message: str, level='info'):
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'debug':
        logger.debug(message)


# ===========================================
#                  Network
# ===========================================
requests.adapters.DEFAULT_RETRIES = 5
SESSION = requests.Session()
SESSION.keep_alive = False
BASE_SLEEP_TIME = 4
user_agent = 'Mozilla/5.0 ven(Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/69.0.3497.100 Safari/537.36 '


def send(url, token='', max_retry=1, sleep_time=2):
    time.sleep(BASE_SLEEP_TIME)

    headers = {'User-Agent': user_agent}
    if token:
        headers['Authorization'] = f'token %{token}'

    try:
        res = SESSION.get(url, headers=headers, stream=False, timeout=10)
        return res
    except Exception as e:
        logger.error('[Request Error] url: {}    - msg: {}'.format(url, e))

        # only retry when exception happens
        if max_retry <= 0:
            return None
        cur_sleep_time = sleep_time + BASE_SLEEP_TIME
        time.sleep(cur_sleep_time)
        return send(url, token, max_retry - 1, sleep_time=cur_sleep_time)


# ===========================================
#                    Regex
# ===========================================
GENERIC_REGEX = regex.compile(r'(?P<gen><(?:[^<>]++|(?&gen))*>)')
DOUBLE_QUOTE_REGEX = regex.compile(r'[^\\](")')
_cache_generic_type_ranges = LRUCache(maxsize=500)
_cache_string_ranges = LRUCache(maxsize=500)


@cached(cache=_cache_generic_type_ranges)
def get_generic_type_ranges(content: str):
    """
    Match `<...>` pairs in the given string
    :param content: string to match
    :return: a list of offset range for `<...>` pairs
    """
    range_list = list()
    if content:
        its = GENERIC_REGEX.finditer(content)
        for m in its:
            range_list.append((m.start(), m.end()))
    return range_list


@cached(cache=_cache_string_ranges)
def get_string_ranges(content: str):
    """
    Match `"` pairs in the given string
    :param content: string to match
    :return: a list of offset range for `"` pairs
    """
    range_list = list()
    tmp_list = list()

    if not content or '"' not in content:
        return range_list

    # find the offset of each double quote
    if content.startswith('"'):  # the leading quote won't be matched by regex, but should be added to tmp_list
        tmp_list.append(0)

    its = DOUBLE_QUOTE_REGEX.finditer(content)
    for m in its:
        tmp_list.append(m.start(1))

    # whether double quotes appear in pairs
    size = len(tmp_list)
    if size % 2 != 0:
        tmp_list.append(len(content) - 1)

    # pair double quotes in order
    i = 0
    while i < size:
        range_list.append((tmp_list[i], tmp_list[i + 1] + 1))
        i += 2

    return range_list


def in_range(num, bound_list):
    for bound in bound_list:
        if bound[0] <= num < bound[1]:
            return True
    return False


# ===========================================
#                    Others
# ===========================================
def tohex(val, nbits):
    # https://stackoverflow.com/questions/7822956/how-to-convert-negative-integer-value-to-hex-in-python
    return hex((val + (1 << nbits)) % (1 << nbits))


def convert_str_to_int(num_str: str):
    num_str = num_str.strip()
    try:
        # Bitwise Complement (with all bits inversed): ~0b 1000 0000 0000 0000, i.e., 0b 0111 1111 1111 1111
        bitwise_complement = False
        if num_str.startswith('~'):
            bitwise_complement = True
            num_str = num_str.lstrip('~')
        # In fact, the type of constant depends on the variable.
        # For example, if the variable is long, then const will be convert to long even if it is int.
        # Since cannot get the variable type, there may be some false positives.
        is_long = False
        if num_str.endswith(('L', 'l')):
            num_str = num_str[:-1]
            is_long = True
        int_val = int(num_str, 0)
        if bitwise_complement:
            int_val = ~int_val

        # Notice 'negative' hex numbers in Java are positive in Python
        # Now, int_val can be a negative number in python, we need to map it back to hex number for Java
        if int_val < 0:
            hex_str = tohex(int_val, 64) if is_long else tohex(int_val, 32)
            int_val = int(hex_str, 0)

        return int_val
    except ValueError:
        return None


def str_to_float(num_str: str):
    try:
        if num_str.endswith(('D', 'd', 'F', 'f')):
            return float(num_str[:-1])
        elif num_str.endswith(('L', 'l')):
            return int(num_str[:-1])
        else:
            return float(num_str)
    except ValueError:
        return None
