import regex

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class NewLineDetector(Detector):
    def __init__(self):
        self.pre_part = regex.compile(r'(\b\w[\w.]*)\s*\.\s*(format|printf|\w*fmt)\s*\(')
        self.params_part = regex.compile(r'(?P<aux>\(((?:[^()]++|(?&aux))*)\))')
        self.var_def_regex = regex.compile(r'\b(Formatter|PrintStream|\w*Writer|\w*Logger)\s+(\w+)\s*[;=]')
        self.newline_regex = regex.compile(r'[^\\](\\n)')
        self.patch, self.interesting_vars = None, dict()
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        string_ranges = get_string_ranges(line_content)
        # if the line contains strings with double quote and key words
        if any(key in line_content for key in ('format', 'printf', 'fmt')):
            its = self.pre_part.finditer(line_content)
            for m in its:
                if in_range(m.start(2), string_ranges):
                    continue
                g = m.groups()
                obj_name = g[0]
                method_name = g[1]

                offset = m.end(0)-1
                m_2 = self.params_part.match(line_content[offset:])
                if m_2:
                    params = m_2.group(2)
                    offset += m_2.start(2)
                else:
                    params = line_content[m.end(0):]
                # Check if strings within params contains '\\n' which only occurs in a string
                its_newline = self.newline_regex.finditer(params)
                for m_newline in its_newline:
                    # Adjust priority
                    priority = priorities.LOW_PRIORITY
                    obj_name_lower = obj_name.lower()

                    if method_name == 'format' and (obj_name == 'String' or obj_name_lower.endswith('formatter')
                                                    or obj_name_lower.endswith('writer')):
                        priority = priorities.MEDIUM_PRIORITY
                    elif method_name == 'printf' and (obj_name == 'System.out' or obj_name_lower.endswith('writer')):
                        priority = priorities.MEDIUM_PRIORITY
                    elif method_name == 'fmt' and obj_name_lower.endswith('logger'):
                        priority = priorities.MEDIUM_PRIORITY
                    else:
                        type_name = self._local_search(obj_name, context)
                        if type_name:
                            priority = priorities.MEDIUM_PRIORITY

                    # get exact line number
                    line_no = get_exact_lineno(offset+m_newline.start(1), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance('VA_FORMAT_STRING_USES_NEWLINE', priority, context.cur_patch.name, line_no,
                                    'Format string should use %n rather than \\n', sha=context.cur_patch.sha, line_content=context.cur_line.content)
                    )
                    return

    def _local_search(self, var_name: str, context):
        # check if patch is updated
        if context.cur_patch != self.patch:
            self.patch = context.cur_patch
            self._init_interesting_vars()

        # check if the var_name is in interesting variable list
        if var_name in self.interesting_vars:
            return self.interesting_vars[var_name]

        return None

    def _init_interesting_vars(self):
        self.interesting_vars.clear()
        if not self.patch:
            return
        for hunk in self.patch:
            for line in hunk:
                if line.prefix == '-':
                    continue
                if any(key in line.content for key in ('Formatter', 'PrintStream', 'Writer', 'Logger')):
                    m = self.var_def_regex.search(line.content)
                    if m:
                        string_ranges = get_string_ranges(line.content)
                        if in_range(m.start(0), string_ranges):
                            continue
                        type_name = m.groups()[0]
                        var_name = m.groups()[1]
                        self.interesting_vars[var_name] = type_name

