import regex

from patterns.models import priorities
from patterns.models.bug_instance import BugInstance
from patterns.models.detectors import Detector, get_exact_lineno
from utils import get_string_ranges, in_range


class BooleanAssignmentDetector(Detector):
    def __init__(self):
        self.extract = regex.compile(r'\b(?:if|while)\s*(?P<aux>\(((?:[^()]++|(?&aux))*)\))')
        self.assignment = regex.compile(r'\b\w+\s*=\s*(?:true|false)\b')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if all(key not in line_content for key in ('if', 'while')) or \
                all(key not in line_content for key in ('true', 'false')) or '=' not in line_content:
            return

        m_1 = self.extract.search(line_content)
        if m_1:
            string_ranges = get_string_ranges(line_content)

            conditions = m_1.group(2)
            offset = m_1.start(2)
            m_2 = self.assignment.search(conditions)
            if m_2:
                offset += m_2.start(0)
                if in_range(offset, string_ranges):
                    return

                line_no = get_exact_lineno(m_1.end(2), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance('QBA_QUESTIONABLE_BOOLEAN_ASSIGNMENT', priorities.HIGH_PRIORITY, context.cur_patch.name,
                                line_no, 'Method assigns boolean literal in boolean expression',
                                sha=context.cur_patch.sha, line_content=context.cur_line.content))
