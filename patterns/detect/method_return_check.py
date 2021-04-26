import regex

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class NotThrowDetector(Detector):
    def __init__(self):
        super().__init__()
        self.pattern = regex.compile(r'^\s*new\s+(\w+?)(?:Exception|Error)\s*(?P<aux1>\((?:[^()]++|(?&aux1))*\))\s*;')

    def match(self, context):
        line_content = context.cur_line.content
        m = self.pattern.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return
            line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
            self.bug_accumulator.append(
                BugInstance('RV_EXCEPTION_NOT_THROWN', priorities.MEDIUM_PRIORITY,
                            context.cur_patch.name, line_no,
                            "Exception created and dropped rather than thrown", sha=context.cur_patch.sha, line_content=context.cur_line.content)
            )