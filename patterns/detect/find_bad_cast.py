import regex
from patterns.models.bug_instance import BugInstance
from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models import priorities
from utils import get_string_ranges, in_range


class FindBadCastDetector(Detector):
    def __init__(self):
        self.pattern = regex.compile(
            r'\(\s*(\w+)\s*\[\s*\]\s*\)\s*((?:(?P<aux1>\((?:[^()]++|(?&aux1))*\))|[\w.$<>\s])+?)\s*\.\s*toArray\s*\(\s*\)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if 'toArray' not in line_content:
            return

        its = self.pattern.finditer(line_content)
        string_ranges = get_string_ranges(line_content)
        for m in its:
            start_offset = m.start(0)
            if in_range(start_offset, string_ranges):
                continue

            right_substring = line_content[m.end(0):].strip()
            if right_substring[0] == '[':
                continue

            if m.group(1) != 'Object' and 'Arrays.asList' not in line_content:
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance('BC_IMPOSSIBLE_DOWNCAST_OF_TOARRAY', priorities.HIGH_PRIORITY, context.cur_patch.name,
                                line_no, "BC: Impossible downcast of toArray() result", sha=context.cur_patch.sha, line_content=context.cur_line.content)
                )

