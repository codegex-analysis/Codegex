import regex

from patterns.models import priorities
from patterns.models.bug_instance import BugInstance
from patterns.models.detectors import Detector, get_exact_lineno
from utils import get_string_ranges, in_range


class EqualsClassNameDetector(Detector):
    def __init__(self):
        self.pattern = regex.compile(
            r'\b((?:[\w\.$"]|(?:\(\s*\)))+)\s*\.\s*equals(?P<aux1>\(((?:[^()]++|(?&aux1))*)\))')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if not all(key in line_content for key in ('equals', 'getClass', 'getName')):
            return

        its = self.pattern.finditer(line_content)
        string_ranges = get_string_ranges(line_content)
        for m in its:
            if in_range(m.start(2), string_ranges):  # m.start(2) is offset of the naming group
                continue
            g = m.groups()
            before_equals = g[0]
            after_equals = g[-1].strip()

            comparing_class_name = False
            if before_equals == 'Objects' and ',' in after_equals:
                elements = after_equals.split(',')
                comparing_class_name = True
                for elem in elements:
                    if not elem.replace(' ', '').endswith('getClass().getName()'):
                        comparing_class_name = False
                        break
            else:
                if before_equals.replace(' ', '').endswith('getClass().getName()') and \
                        after_equals.replace(' ', '').endswith('getClass().getName()'):
                    comparing_class_name = True

            if comparing_class_name:
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance('EQ_COMPARING_CLASS_NAMES', priorities.MEDIUM_PRIORITY, context.cur_patch.name,
                                line_no, 'Equals method compares class names rather than class objects',
                                sha=context.cur_patch.sha, line_content=context.cur_line.content))
                return
