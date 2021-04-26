import regex
from patterns.models.bug_instance import BugInstance
from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models import priorities
from utils import get_string_ranges, in_range


class FloatEqualityDetector(Detector):
    def __init__(self):
        self.pattern_op = regex.compile(
            r'(\b\w[\w.]*(?P<aux1>\((?:[^()]++|(?&aux1))*\))*)\s*[<>!=]+\s*(\b\w[\w.]*(?&aux1)*)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if 'NaN' in line_content \
                and any(op in line_content for op in ('>', '<', '>=', '<=', '==', '!=')):
            its = self.pattern_op.finditer(line_content)
            string_ranges = get_string_ranges(line_content)
            for m in its:
                if in_range(m.start(0), string_ranges):
                    continue

                op_1 = m.groups()[0]  # m.groups()[1] is the result of named pattern
                op_2 = m.groups()[2]
                if any(op in ('Float.NaN', 'Double.NaN') for op in (op_1, op_2)):
                    line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance('FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER', priorities.HIGH_PRIORITY,
                                    context.cur_patch.name, line_no,
                                    "Doomed test for equality to NaN", sha=context.cur_patch.sha, line_content=context.cur_line.content)
                    )
                    return
