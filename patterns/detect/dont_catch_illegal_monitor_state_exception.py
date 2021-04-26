import re

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class DontCatchIllegalMonitorStateException(Detector):
    """
    匹配 catch (xxException e1, ..., xxException e2), 并分离出 Exception 类型
    TODO: java.lang.Exception　和　java.lang.Throwable 的检测
    """

    def __init__(self):
        # 匹配形如 "catch (IOException e)"
        self.p_catch = re.compile(r'catch\s*\(([^()]+)\)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        match = self.p_catch.search(line_content)
        if match:
            string_range = get_string_ranges(line_content)
            if in_range(match.start(0), string_range):
                return

            params = match.groups()[0]
            defs = params.split(',')
            for d in defs:
                exception_class = d.split()[0]

                if exception_class.endswith('IllegalMonitorStateException'):
                    line_no = get_exact_lineno('IllegalMonitorStateException', context.cur_line, keyword_mode=True)[1]
                    self.bug_accumulator.append(
                        BugInstance('IMSE_DONT_CATCH_IMSE', priorities.HIGH_PRIORITY,
                                    context.cur_patch.name, line_no,
                                    'Dubious catching of IllegalMonitorStateException', sha=context.cur_patch.sha, line_content=context.cur_line.content)
                    )
                    return
