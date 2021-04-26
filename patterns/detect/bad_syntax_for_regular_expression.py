import regex

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class SingleDotPatternDetector(Detector):
    def __init__(self):
        self.pattern = regex.compile(r'\.\s*(replaceAll|replaceFirst|split|matches)\s*\(\s*"([.|])\s*"\s*,?([^)]*)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if any(method in line_content for method in ('replaceAll', 'replaceFirst', 'split', 'matches')) \
                and any(key in line_content for key in ('"."', '"|"')):
            its = self.pattern.finditer(line_content)
            string_ranges = get_string_ranges(line_content)
            for m in its:
                if in_range(m.start(0), string_ranges):
                    continue

                g = m.groups()
                method_name = g[0]
                arg_1 = g[1]
                arg_2 = g[2].strip()

                # Check number of parameter.
                # If method has more than 2 arguments, it might not be the one in String class.
                # arg_2 should look like `"replacement string, here"` or `var_name`.
                if ',' in arg_2 and not (arg_2.startswith('"') and arg_2.endswith('"')):
                    continue

                priority = priorities.HIGH_PRIORITY
                if method_name == 'replaceAll' and arg_1 == '.':
                    priority = priorities.MEDIUM_PRIORITY
                    if arg_2.startswith('"') and arg_2.endswith('"'):
                        if arg_2 in ('"x"', '"X"', '"-"', '"*"', '" "', '"\\*"'):
                            continue  # Ignore password mask
                        elif len(arg_2) == 3:
                            priority = priorities.LOW_PRIORITY

                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]  # m.end(0)-1 < len(line_content)
                self.bug_accumulator.append(
                    BugInstance('RE_POSSIBLE_UNINTENDED_PATTERN', priority, context.cur_patch.name, line_no,
                                '“.” or “|” used for regular expressions', sha=context.cur_patch.sha, line_content=context.cur_line.content))
                return


class FileSeparatorAsRegexpDetector(Detector):
    def __init__(self):
        self.pattern = regex.compile(
            r'(\bPattern)?\.\s*(replaceAll|replaceFirst|split|matches|compile)\s*\(\s*File\.separator\s*,?([^)]*)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if 'File.separator' in line_content and any(
                method in line_content for method in ('replaceAll', 'replaceFirst', 'split', 'matches', 'compile')):
            its = self.pattern.finditer(line_content)
            string_ranges = get_string_ranges(line_content)
            for m in its:
                if in_range(m.start(0), string_ranges):
                    continue

                g = m.groups()
                class_name = g[0]
                method_name = g[1]
                arg_2 = g[2].strip()

                # Check number of parameter.
                if ',' in arg_2 and not (arg_2.startswith('"') and arg_2.endswith('"')):
                    continue

                if method_name == 'compile' and (class_name != 'Pattern' or 'Pattern.LITERAL' in arg_2):
                    continue

                priority = priorities.HIGH_PRIORITY
                if method_name == 'matches' and not arg_2:  # Observe from spotbugs' test cases
                    priority = priorities.LOW_PRIORITY
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance('RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', priority, context.cur_patch.name,
                                line_no, 'File.separator used for regular expression', sha=context.cur_patch.sha, line_content=context.cur_line.content))
                return
