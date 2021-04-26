import regex

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class StaticDateFormatDetector(Detector):
    def __init__(self):
        self.p = regex.compile(
            r'^([\w\s]*?)\bstatic\s*(?:final)?\s+(DateFormat|SimpleDateFormat|Calendar|GregorianCalendar)\s+(\w+)\s*[;=]')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if not any(key in line_content for key in ('DateFormat', 'Calendar')):
            return

        m = self.p.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return

            groups = m.groups()
            access = groups[0].strip()
            if access and 'private' in access.split():
                return
            class_name = groups[1]
            field_name = groups[2]
            line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
            if class_name.endswith('DateFormat'):
                self.bug_accumulator.append(
                    BugInstance('STCAL_STATIC_SIMPLE_DATE_FORMAT_INSTANCE',
                                priorities.MEDIUM_PRIORITY, context.cur_patch.name, line_no,
                                f"{field_name} is a static field of type java.text.DateFormat, which isn't thread safe",
                                sha=context.cur_patch.sha, line_content=context.cur_line.content))
            else:
                self.bug_accumulator.append(
                    BugInstance('STCAL_STATIC_CALENDAR_INSTANCE',
                                priorities.MEDIUM_PRIORITY, context.cur_patch.name, line_no,
                                f"{field_name} is a static field of type java.util.Calendar, which isn't thread safe",
                                sha=context.cur_patch.sha, line_content=context.cur_line.content))
