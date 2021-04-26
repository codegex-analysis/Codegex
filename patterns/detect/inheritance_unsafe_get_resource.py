import cachetools
import regex
from cachetools import cached, LRUCache

from patterns.models import priorities
from patterns.models.bug_instance import BugInstance
from patterns.models.detectors import Detector, online_search, get_exact_lineno
from utils import get_string_ranges, in_range

_cache = LRUCache(maxsize=500)

GENERIC_REGEX = regex.compile(r'(?P<gen><(?:[^<>]++|(?&gen))*>)')
CLASS_EXTENDS_REGEX = regex.compile(r'class\s+([\w$]+)\s*(?P<gen><(?:[^<>]++|(?&gen))*>)?\s+extends\s+([\w$.]+)')
INTERFACE_EXTENDS_REGEX = regex.compile(r'interface\s+([\w$]+)\s*(?P<gen><(?:[^<>]++|(?&gen))*>)?\s+extends\s+([^{]+)')


class GetResourceDetector(Detector):
    def __init__(self):
        self.pattern = regex.compile(r'(?:(\b\w+)\.)?getClass\(\s*\)\.getResource(?:AsStream)?\(')
        Detector.__init__(self)

        self.patch_set, self.extends_dict = None, dict()  # If patch_set is updated, then update extends_dict

    def match(self, context):
        line_content = context.cur_line.content
        if not all(method in line_content for method in ['getClass', 'getResource']):
            return

        its = self.pattern.finditer(line_content)
        string_ranges = get_string_ranges(line_content)
        for m in its:
            if in_range(m.start(0), string_ranges):
                continue

            obj_name = m.groups()[0]
            if not obj_name or obj_name == 'this':
                simple_name = context.cur_patch.name.rstrip('.java').rsplit('/', 1)[-1]  # default class name is the filename
                priority = self.decide_priority(simple_name, context)

                if priority is None:
                    return

                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance('UI_INHERITANCE_UNSAFE_GETRESOURCE', priority, context.cur_patch.name,
                                line_no,
                                'Usage of GetResource may be unsafe if class is extended', sha=context.cur_patch.sha, line_content=context.cur_line.content)
                )
                return

    @cached(cache=_cache, key=lambda self, simple_name, context: cachetools.keys.hashkey(simple_name))
    def decide_priority(self, simple_name, context):
        """
        Decide the priority according to search results of local search or online search
        :param simple_name: simple name of class
        :param context: context object to analysis
        :return: MEDIUM_PRIORITY if extended, else IGNORE_PRIORITY
        """
        # check if patch_set is updated
        if context.patch_set != self.patch_set:
            self.patch_set = context.patch_set
            self._init_extends_dict()
            _cache.clear()

        # local search
        if context.local_search():
            for patch_name, extended_name_list in self.extends_dict.items():
                if simple_name in extended_name_list:
                    return priorities.MEDIUM_PRIORITY
        # online search
        if context.online_search():
            repo_name, token = context.get_online_search_info()
            if context:
                query = f'https://api.github.com/search/code?q=%22extends+{simple_name}%22+in:file' \
                        f'+language:Java+repo:{repo_name}'
                resp_json = online_search(query, token, search_parent=True, repo_name=repo_name)

                if resp_json:
                    if 'total_count' in resp_json:
                        if resp_json['total_count'] > 0:
                            return priorities.MEDIUM_PRIORITY
                        else:
                            # return None
                            return priorities.LOW_PRIORITY

        # default priority
        # return priorities.IGNORE_PRIORITY
        return priorities.LOW_PRIORITY

    def _init_extends_dict(self, ):
        self.extends_dict.clear()
        if not self.patch_set:
            return
        for patch in self.patch_set:
            extended_names_in_patch = set()
            for hunk in patch:
                for line in hunk:
                    if line.prefix == '-':
                        continue

                    if 'extends' in line.content:
                        if 'class' in line.content:
                            m = CLASS_EXTENDS_REGEX.search(line.content.strip())
                        elif 'interface' in line.content:
                            m = INTERFACE_EXTENDS_REGEX.search(line.content.strip())
                        else:
                            continue

                        if m:
                            g = m.groups()
                            extended_str = GENERIC_REGEX.sub('', g[-1])  # remove <...>
                            extended_names_in_line = [name.rsplit('.', 1)[-1].strip() for name in
                                                      extended_str.split(',')]
                            extended_names_in_patch.update(extended_names_in_line)

            if extended_names_in_patch:
                self.extends_dict[patch.name] = extended_names_in_patch
