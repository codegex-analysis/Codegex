from patterns.models.context import Context
from rparser import Line, VirtualStatement
from utils import send


def online_search(query: str, token='', search_parent=False, repo_name=''):
    resp = send(query, token, 3)
    if resp:
        resp = resp.json()
        if 'total_count' in resp:
            if resp['total_count'] == 0 and search_parent and repo_name:
                # get parent repo name
                resp = send(f'https://api.github.com/repos/{repo_name}')
                if resp:
                    resp = resp.json()
                    # forked repositories are not currently searchable
                    if 'fork' in resp and resp['fork']:
                        parent_full_name = ''
                        if 'parent' in resp and 'full_name' in resp['parent']:
                            parent_full_name = resp['parent']['full_name']
                        elif 'source' in resp and 'full_name' in resp['source']:
                            parent_full_name = resp['source']['full_name']
                        # search in parent
                        if parent_full_name:
                            new_query = query.replace(repo_name, parent_full_name)
                            return online_search(new_query, token)
            else:
                return resp
    return None


def get_exact_lineno(target, line: Line, is_strip=False, keyword_mode=False):
    """
    Return the exact line number according to target in line
    :param target: an integer less than or equal to the length of line content under default mode,
                    or keyword string under keyword mode
    :param line: a simple line object or a virtual statement object
    :param is_strip: if true, left strip the first sub-line and right strip the last sub-line
    :param keyword_mode: if false, the default offset mode is on, otherwise, the keyword mode is on
    :return: the exact lineno
    """
    if isinstance(line, VirtualStatement):
        if keyword_mode:
            tmp = line.get_exact_lineno_by_keyword(target)
        else:
            tmp = line.get_exact_lineno_by_offset(target, is_strip)

        if tmp:
            return tmp
        else:
            # Return the lineno of the last sub-line
            # to ensure all content of the virtual statement is shown in code review of pull requests
            delta = len(line.sub_lines) - 1
            return line.lineno[0] + delta, line.lineno[1] + delta
    else:
        return line.lineno


class Detector:
    def __init__(self):
        self.bug_accumulator = []

    def match(self, context: Context):
        """
        Match single line and generate bug instance using regex pattern
        :param context: context object
        :return: None
        """
        pass

    def reset_bug_accumulator(self):
        self.bug_accumulator = list()
