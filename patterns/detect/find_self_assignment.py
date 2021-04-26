import regex

from patterns.models.bug_instance import BugInstance
from patterns.models.detectors import Detector, get_exact_lineno
import patterns.models.priorities as Priorities
from utils import in_range, get_string_ranges


class CheckForSelfAssignment(Detector):
    def __init__(self):
        self.pattern = regex.compile(
            r'(\b\w(?:[\w.]|(?P<aux1>\((?:[^()]++|(?&aux1))*\)))*)\s*=\s*(\w(?:[\w.]|(?&aux1))*)\s*;')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if '=' in line_content:
            m = self.pattern.search(line_content)
            string_ranges = get_string_ranges(line_content)
            if m:
                if in_range(m.start(0), string_ranges):
                    return
                g = m.groups()
                if g[0] == g[2]:
                    line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance('SA_SELF_ASSIGNMENT', Priorities.HIGH_PRIORITY, context.cur_patch.name, line_no,
                                    'SA: Self assignment of field or variable', sha=context.cur_patch.sha, line_content=context.cur_line.content)
                    )


class CheckForSelfDoubleAssignment(Detector):
    def __init__(self):
        self.pattern = regex.compile(
            r'\b(\w(?:[\w.]|(?P<aux1>\((?:[^()]++|(?&aux1))*\)))*)\s*=\s*(\w(?:[\w.]|(?&aux1))*)\s*=[^=]')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if '=' in line_content:
            m = self.pattern.search(line_content)
            if m:
                g = m.groups()
                if g[0] == g[2]:
                    line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance('SA_DOUBLE_ASSIGNMENT', Priorities.HIGH_PRIORITY, context.cur_patch.name,
                                    line_no,
                                    'SA: Double assignment of field or local variable', sha=context.cur_patch.sha, line_content=context.cur_line.content)
                    )
