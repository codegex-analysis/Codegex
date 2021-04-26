import regex

from patterns.models.bug_instance import BugInstance
from patterns.models.detectors import Detector, get_exact_lineno
import patterns.models.priorities as Priorities
from utils import get_generic_type_ranges, get_string_ranges, in_range


class CheckForSelfComputation(Detector):
    def __init__(self):
        self.pattern = regex.compile(
            r'(\b\w(?:[\w.]|(?P<aux1>\((?:[^()]++|(?&aux1))*\)))*)\s*([|^&-])\s*(\w(?:[\w.]|(?&aux1))*)')
        Detector.__init__(self)

        self._op_precedence_dict = {
            '~': 9, '!': 9,
            '*': 8, '/': 8, '%': 8,
            '-': 7, '+': 7,
            '>>': 6, '>>>': 6, '<<': 6,
            '>': 5, '>=': 5, '<': 5, '<=': 5,
            '!=': 4, '==': 4,
            '&': 3, '^': 2, '|': 1,
        }

    def _is_precedent(self, op_1, op_2):
        assert all(op in self._op_precedence_dict for op in (op_1, op_2))
        return self._op_precedence_dict[op_1] > self._op_precedence_dict[op_2]

    def match(self, context):
        line_content = context.cur_line.content
        if all(op not in line_content for op in ('&', '|', '^', '-')):
            return

        string_ranges = get_string_ranges(line_content)
        its = self.pattern.finditer(line_content)
        for m in its:
            g = m.groups()
            obj_1 = g[0]
            op = g[2]
            op_offset = m.start(3)
            obj_2 = g[3]
            if obj_1 == obj_2 and op in ('&', '|', '^', '-') and\
                    not in_range(op_offset, string_ranges):
                # to filter method called on Random object
                if any(k in obj_1 for k in ('random', 'Random', 'next')):
                    continue

                pre_substring = line_content[:m.start(0)].rstrip()
                op_front = None
                if pre_substring[-2:] in self._op_precedence_dict:
                    op_front = pre_substring[-2:]
                elif pre_substring[-1] in self._op_precedence_dict:
                    op_front = pre_substring[-1]

                after_substring = line_content[m.end(0):].lstrip()
                op_behind = None
                if after_substring[:2] in self._op_precedence_dict:
                    op_behind = after_substring[:2]
                elif after_substring[0] in self._op_precedence_dict:
                    op_behind = after_substring[0]

                # Check operator precedence to avoid false positives
                if op_front and self._is_precedent(op_front, op):
                    continue
                if op_behind and self._is_precedent(op_behind, op):
                    continue
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance('SA_SELF_COMPUTATION', Priorities.MEDIUM_PRIORITY, context.cur_patch.name, line_no,
                                'Nonsensical self computation involving a variable or field', sha=context.cur_patch.sha, line_content=context.cur_line.content)
                )
                return


class CheckForSelfComparison(Detector):
    def __init__(self):
        self.pattern_1 = regex.compile(
            r'(\b\w[\w.]*(?P<aux1>\((?:[^()]++|(?&aux1))*\))*)\s*(==|!=|>=|<=|>|<)\s*([\w.]+(?&aux1)*)')
        self.pattern_2 = regex.compile(
            r'((?:"|\b\w|(?P<aux1>\((?:[^()]++|(?&aux1))*\)))(?:[\w\.$"\[\]]|(?&aux1))*?)\s*\.\s*(?:equals|compareTo|endsWith|startsWith|contains|equalsIgnoreCase|compareToIgnoreCase)((?&aux1))')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        string_ranges = get_string_ranges(line_content)

        hit = False
        match_end = None
        if any(op in line_content for op in ('>', '<', '>=', '<=', '==', '!=')):
            generic_type_ranges = get_generic_type_ranges(line_content)
            its = self.pattern_1.finditer(line_content)
            for m in its:
                op_offset = m.start(3)  # the start offset of relation_op
                if in_range(op_offset, string_ranges):
                    continue
                g = m.groups()
                obj_1 = g[0]
                relation_op = g[2]
                obj_2 = g[3]
                if obj_1 == obj_2:
                    # check the first non-empty character before object 1
                    pre_substring = line_content[: m.start(0)].strip()
                    if pre_substring and not pre_substring[-1].isalpha() and \
                            pre_substring[-1] not in ('(', '&', '|', '=', '>', '<'):
                        continue

                    # check the last non-empty character after object 2
                    latter_substring = line_content[m.end(0):].strip()
                    if latter_substring and not latter_substring[0].isalpha() and \
                            latter_substring[0] not in (')', ';', '|', '=', '>', '<'):
                        continue

                    # check if in generic type range
                    if relation_op in ('<', '>') and in_range(op_offset, generic_type_ranges):
                        continue

                    hit = True
                    match_end = m.end(0)
                    break

        if not hit and any(method in line_content for method in ('equals', 'compareTo', 'endsWith', 'startsWith',
                                                                 'contains', 'equalsIgnoreCase',
                                                                 'compareToIgnoreCase')):
            its = self.pattern_2.finditer(line_content)
            for m in its:
                if in_range(m.start(3), string_ranges):
                    continue
                before_method = m.group(1)
                after_method = m.group(3)[1:-1].strip()  # remove '(' and ')', then strip

                if before_method == after_method:
                    hit = True
                    match_end = m.end(0)
                    break
                elif after_method != '","':
                    elements = after_method.split(',')

                    if len(elements) == 2 and elements[0] == elements[1]:
                        hit = True
                        match_end = m.end(0)
                        break

        if hit:
            line_no = get_exact_lineno(match_end, context.cur_line)[1]
            self.bug_accumulator.append(
                BugInstance('SA_SELF_COMPARISON', Priorities.MEDIUM_PRIORITY, context.cur_patch.name, line_no,
                            'Self comparison of value or field with itself', sha=context.cur_patch.sha, line_content=context.cur_line.content)
            )
