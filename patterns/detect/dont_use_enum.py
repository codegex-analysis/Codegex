import regex

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class DontUseEnumDetector(Detector):
    def __init__(self):
        self.p_identifier = regex.compile(r'\b\w+\b(?:\s+|(\s*\.\s*)?)\b(enum|assert)\b\s*(?(1)[^\w$\s]|\()')
        self.p = regex.compile(r'\b(enum|assert)\b\s*[^\w$\s(!-]')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if not any(key in line_content for key in ('assert', 'enum')):
            return

        string_range = get_string_ranges(line_content)
        its = self.p_identifier.finditer(line_content)
        for m in its:
            if not in_range(m.start(2), string_range):
                # m.end(2) is the offset of keyword "enum" or "assert"
                line_no = get_exact_lineno(m.end(2), context.cur_line)[1]
                # In spotbugs, it checks methods and fields.
                # We check method definition and calls like `obj.field` or `obj.method()`
                self.bug_accumulator.append(
                    BugInstance('NM_FUTURE_KEYWORD_USED_AS_MEMBER_IDENTIFIER', priorities.MEDIUM_PRIORITY,
                                context.cur_patch.name, line_no,
                                'Nm: Use of identifier that is a keyword in later versions of Java',
                                sha=context.cur_patch.sha, line_content=context.cur_line.content)
                )
                return

        its = self.p.finditer(line_content)
        for m in its:
            if not in_range(m.start(0), string_range):
                # m.start(0) is the offset of keyword "enum" or "assert"
                line_no = get_exact_lineno(m.start(0), context.cur_line)[1]
                # In spotbugs, it checks local variables, here we check local variables and fields.
                self.bug_accumulator.append(
                    BugInstance('NM_FUTURE_KEYWORD_USED_AS_IDENTIFIER', priorities.MEDIUM_PRIORITY,
                                context.cur_patch.name, line_no,
                                'Nm: Use of identifier that is a keyword in later versions of Java',
                                sha=context.cur_patch.sha, line_content=context.cur_line.content)
                )
                return
