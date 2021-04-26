from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import convert_str_to_int, get_string_ranges, in_range

import regex


class IncompatMaskDetector(Detector):
    def __init__(self):
        self.regexpSign = regex.compile(
            r'\(\s*([~-]?(?:(?P<aux1>\((?:[^()]++|(?&aux1))*\))|[\w.-])++)\s*([&|])\s*([~-]?(?:(?&aux1)|[\w.])++)\s*\)\s*([><=!]+)\s*([0-9a-zA-Z]+)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if not any(bitop in line_content for bitop in ('&', '|')) and \
                not any(op in line_content for op in ('>', '<', '>=', '<=', '==', '!=')):
            return

        its = self.regexpSign.finditer(line_content)
        string_ranges = get_string_ranges(line_content)
        for m in its:
            if in_range(m.start(0), string_ranges):
                continue
            g = m.groups()
            operand_1 = g[0]
            bitop = g[2]
            operand_2 = g[3]
            relation_op = g[4]
            tgt_const_str = g[5]

            tgt_const = convert_str_to_int(tgt_const_str)
            if tgt_const is None:
                return

            op1 = convert_str_to_int(operand_1)
            op2 = convert_str_to_int(operand_2)

            if op1 is None and op2 is None:
                return

            if op1:
                const = op1
                const_str = operand_1
            else:
                const = op2
                const_str = operand_2
            is_long = True if const_str.endswith(('L', 'l')) else False

            priority = priorities.HIGH_PRIORITY
            p_type, description = None, None

            if relation_op in ('>', '<', '>=', '<=') and tgt_const == 0:
                if is_long:
                    max_positive = 0x7fffffffffffffff  # 9223372036854775807
                    min_negative = 0x8000000000000000  # -9223372036854775808
                    max_negative = 0xffffffffffffffff  # -1
                else:
                    max_positive = 0x7fffffff  # 2147483647
                    min_negative = 0x80000000  # -2147483648
                    max_negative = 0xffffffff  # -1

                if min_negative <= const <= max_negative:
                    p_type = 'BIT_SIGNED_CHECK_HIGH_BIT'
                    description = 'Check for sign of bitwise operation involving negative number.'
                    if relation_op in ('<', '>='):
                        priority = priorities.MEDIUM_PRIORITY
                elif 0 <= const <= max_positive:
                    p_type = 'BIT_SIGNED_CHECK'
                    description = 'Check for sign of bitwise operation.'
                    # at most 12 bits: -4096 <= const <= -1 or 0 <= const <= 4095
                    only_low_bits = const <= 0xfff
                    priority = priorities.LOW_PRIORITY if only_low_bits else priorities.MEDIUM_PRIORITY

            elif relation_op in ('==', '!='):
                priority = priorities.HIGH_PRIORITY
                p_type, description = None, None

                if bitop == '|':
                    if (const & ~tgt_const) != 0:
                        p_type = 'BIT_IOR'
                        description = 'Incompatible bit masks in yields a constant result.'
                elif const != 0 or tgt_const != 0:
                    if (tgt_const & ~const) != 0:
                        p_type = 'BIT_AND'
                        description = 'Incompatible bit masks in yields a constant result.'
                else:
                    p_type = 'BIT_AND_ZZ'
                    description = 'The expression of the form (e & 0) to 0 will always compare equal.'

            if p_type is not None:
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(BugInstance(p_type, priority, context.cur_patch.name, line_no, description,
                                                        sha=context.cur_patch.sha, line_content=context.cur_line.content))



