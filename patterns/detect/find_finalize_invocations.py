import re

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class ExplicitInvDetector(Detector):
    def __init__(self):
        self.pattern = re.compile(r'(\b\w+)\s*\.\s*finalize\s*\(\s*\)\s*;')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        its = self.pattern.finditer(line_content)
        string_ranges = get_string_ranges(line_content)
        for m in its:
            if in_range(m.start(0), string_ranges):
                continue
            if m.group(1) != 'super':
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance('FI_EXPLICIT_INVOCATION', priorities.HIGH_PRIORITY, context.cur_patch.name, line_no,
                                'Explicit invocation of Object.finalize()', sha=context.cur_patch.sha, line_content=context.cur_line.content)
                )


class PublicAccessDetector(Detector):
    def __init__(self):
        self.pattern = re.compile(r'public\s+void\s+finalize\s*\(\s*\)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        m = self.pattern.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return
            line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
            self.bug_accumulator.append(
                BugInstance('FI_PUBLIC_SHOULD_BE_PROTECTED', priorities.MEDIUM_PRIORITY, context.cur_patch.name,
                            line_no, 'Finalizer should be protected, not public', sha=context.cur_patch.sha, line_content=context.cur_line.content)
            )
