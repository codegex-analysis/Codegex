import regex

from patterns.models import priorities
from patterns.models.bug_instance import BugInstance
from patterns.models.detectors import Detector, get_exact_lineno
from utils import convert_str_to_int, get_string_ranges, in_range


class BadMonthDetector(Detector):
    def __init__(self):
        self.date = regex.compile(r'\b([\w$]+)\.setMonth\s*\((\d+)\s*\)')
        self.calendar = regex.compile(r'\b([\w$]+)\.set\s*\(([^,]+,\s*(\d+)\s*[,)])')
        self.gre_calendar = regex.compile(r'new\s+GregorianCalendar\s*\([^,]+,\s*(\d+)\s*,')
        Detector.__init__(self)

    def match(self, context):
        fire = False
        instance_name = None
        month = None
        priority = priorities.MEDIUM_PRIORITY

        line_content = context.cur_line.content
        string_ranges = get_string_ranges(line_content)
        offset = None
        if 'setMonth' in line_content:
            m = self.date.search(line_content)
            if m:
                if in_range(m.start(0), string_ranges):
                    return
                offset = m.end(0)
                fire = True
                g = m.groups()
                instance_name = g[0]
                month = int(g[1])
                priority = priorities.HIGH_PRIORITY
        elif 'set' in line_content:
            if 'calendar' in line_content.lower():  # To temporarily reduce unnecessary matches
                m = self.calendar.search(line_content)
                if m:
                    if in_range(m.start(0), string_ranges):
                        return
                    offset = m.end(0)
                    g = m.groups()

                    # TODO: find object type of instance_name by local search
                    if (g[1].endswith(')') and 'Calendar.MONTH' in g[1]) or \
                            (g[1].endswith(',') and 'calendar' in g[0].lower()):
                        fire = True
                        instance_name = g[0]
                        month = int(g[2])
        elif 'GregorianCalendar' in line_content and 'new' in line_content:
            m = self.gre_calendar.search(line_content)
            if m:
                if in_range(m.start(0), string_ranges):
                    return
                offset = m.end(0)
                fire = True
                month = int(m.groups()[0])

        if fire:
            if month < 0 or month > 11:
                line_no = get_exact_lineno(offset, context.cur_line)[1]
                self.bug_accumulator.append(BugInstance('DMI_BAD_MONTH', priority, context.cur_patch.name, line_no,
                                                        'Bad constant value for month.', sha=context.cur_patch.sha, line_content=context.cur_line.content))

                
class ShiftAddPriorityDetector(Detector):
    def __init__(self):
        self.pattern = regex.compile(r'\b[\w$]+\s*<<\s*([\w$]+)\s*[+-]\s*[\w$]+')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if '<<' not in line_content and '+' not in line_content:
            return

        m = self.pattern.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return
            priority = priorities.LOW_PRIORITY
            const = convert_str_to_int(m.groups()[0])

            if const is not None:
                # If (foo << 32 + var) encountered for ISHL (left shift for int), then((foo << 32) + var) is absolutely
                # meaningless, but(foo << (32 + var)) can be meaningful for negative var values.
                # The same for LSHL (left shift for long)
                if const == 32 or const == 64:
                    return

                if const == 8:
                    priority = priorities.MEDIUM_PRIORITY
            line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
            self.bug_accumulator.append(
                BugInstance('BSHIFT_WRONG_ADD_PRIORITY', priority, context.cur_patch.name, line_no,
                            'Possible bad parsing of shift operation.', sha=context.cur_patch.sha, line_content=context.cur_line.content))


class OverwrittenIncrementDetector(Detector):
    def __init__(self):
        # 提取'='左右操作数
        self.pattern = regex.compile(
            r'(\b[\w.+$]+)\s*=([\w.\s+\-*\/]+)\s*;'
        )
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if '=' in line_content and any(op in line_content for op in ('++', '--')):
            its = self.pattern.finditer(line_content)
            string_ranges = get_string_ranges(line_content)
            for m in its:
                if in_range(m.start(0), string_ranges):
                    continue
                op_1 = m.groups()[0]
                op_2 = m.groups()[1]

                # 两种可能的匹配 'a++', 'a--'
                pattern_inc = regex.compile(r'\b{}\s*\+\+|\b{}\s*--'.format(op_1, op_1))

                if pattern_inc.search(op_2):
                    line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance('DLS_OVERWRITTEN_INCREMENT', priorities.HIGH_PRIORITY, context.cur_patch.name,
                                    line_no, "DLS: Overwritten increment", sha=context.cur_patch.sha, line_content=context.cur_line.content)
                    )
                    break
