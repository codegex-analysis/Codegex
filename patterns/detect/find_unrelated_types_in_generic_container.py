import regex

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class SuspiciousCollectionMethodDetector(Detector):
    def __init__(self):
        self.pattern = regex.compile(
            r'(\b\w[\w.]*(?P<aux1>\((?:[^()]++|(?&aux1))*\))*+)\s*\.\s*((?:remove|contains|retain)(?:All)?)\s*\(\s*([\w.]+(?&aux1)*)\s*\)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if not any(method in line_content for method in ['remove', 'contains', 'retain']):
            return

        its = self.pattern.finditer(line_content)
        string_ranges = get_string_ranges(line_content)
        for m in its:
            if in_range(m.start(0), string_ranges):
                continue
            g = m.groups()
            obj_1 = g[0]
            method_name = g[2]
            obj_2 = g[3]

            if obj_1 == obj_2:
                pattern_type, description, priority = None, None, None
                if method_name == 'removeAll':
                    pattern_type = 'DMI_USING_REMOVEALL_TO_CLEAR_COLLECTION'
                    description = 'removeAll used to clear a collection'
                    priority = priorities.MEDIUM_PRIORITY
                elif method_name in ['containsAll', 'retainAll']:
                    pattern_type = 'DMI_VACUOUS_SELF_COLLECTION_CALL'
                    description = 'Vacuous call to collections'
                    priority = priorities.MEDIUM_PRIORITY
                elif method_name in ['contains', 'remove']:
                    pattern_type = 'DMI_COLLECTIONS_SHOULD_NOT_CONTAIN_THEMSELVES'
                    description = 'Collections should not contain themselves'
                    priority = priorities.HIGH_PRIORITY

                if pattern_type:
                    line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance(pattern_type, priority, context.cur_patch.name, line_no, description,
                                    sha=context.cur_patch.sha, line_content=context.cur_line.content)
                    )
                    return
