import regex

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class CollectionAddItselfDetector(Detector):
    def __init__(self):
        self.pattern = regex.compile(
            r'(\b\w[\w.]*(?P<aux1>\((?:[^()]++|(?&aux1))*\))*+)\s*\.\s*add\s*\(\s*([\w.]+(?&aux1)*)\s*\)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if "add" not in line_content:
            return
        its = self.pattern.finditer(line_content)
        string_ranges = get_string_ranges(line_content)
        for m in its:
            if in_range(m.start(0), string_ranges):
                continue
            g = m.groups()
            if g[0] == g[2]:
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance('IL_CONTAINER_ADDED_TO_ITSELF', priorities.HIGH_PRIORITY, context.cur_patch.name,
                                line_no, 'A collection is added to itself', sha=context.cur_patch.sha, line_content=context.cur_line.content)
                )
