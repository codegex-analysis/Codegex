import re

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models import priorities
from utils import get_string_ranges, in_range


class DefSerialVersionID(Detector):
    def __init__(self):
        self.pattern = re.compile(r'((?:static|final|\s)*)\b(long|int)\s+serialVersionUID\b')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if 'serialVersionUID' not in line_content:
            return

        m = self.pattern.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return
            g = m.groups()
            prefix = None
            g1 = g[0].strip()
            if g1:
                prefix = g1.split()

            pattern_name = None
            message = None
            priority = priorities.LOW_PRIORITY

            if prefix:
                if 'static' not in prefix:
                    pattern_name = 'SE_NONSTATIC_SERIALVERSIONID'
                    message = "serialVersionUID isn't static."
                    priority = priorities.MEDIUM_PRIORITY
                elif 'final' not in prefix:
                    pattern_name = 'SE_NONFINAL_SERIALVERSIONID'
                    message = "serialVersionUID isn't final."
                    priority = priorities.MEDIUM_PRIORITY

            if not pattern_name and 'int' == g[1]:
                pattern_name = 'SE_NONLONG_SERIALVERSIONID'
                message = "serialVersionUID isn't long."

            if pattern_name:
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance(pattern_name, priority, context.cur_patch.name, line_no, message,
                                sha=context.cur_patch.sha, line_content=context.cur_line.content))


class DefReadResolveMethod(Detector):
    def __init__(self):
        self.pattern = re.compile(
            r'((?:static|final|\s)*)\b([^\s]+)\s+readResolve\s*\(\s*\)\s+throws\s+ObjectStreamException')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if any(const not in line_content for const in ['readResolve', 'throws', 'ObjectStreamException']):
            return

        m = self.pattern.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return

            g = m.groups()
            pattern_name = None
            message = None

            if g[1] != 'Object':
                pattern_name = 'SE_READ_RESOLVE_MUST_RETURN_OBJECT'
                message = 'The readResolve method must be declared with a return type of Object.'
            elif g[0] and 'static' in g[0].split():
                pattern_name = 'SE_READ_RESOLVE_IS_STATIC'
                message = 'The readResolve method must not be declared as a static method.'

            if pattern_name:
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance(pattern_name, priorities.MEDIUM_PRIORITY, context.cur_patch.name, line_no, message,
                                sha=context.cur_patch.sha, line_content=context.cur_line.content))


class DefPrivateMethod(Detector):
    def __init__(self):
        self.pattern = re.compile(
            r'void\s+(writeObject|readObject|readObjectNoData)\s*\(([\s\w.$]*)\)\s*throws\s+')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if any(key not in line_content for key in ('void', 'throws')) or all(
                key not in line_content for key in ('writeObject', 'readObject', 'readObjectNoData')):
            return

        strip_line = line_content.strip()
        m = self.pattern.search(strip_line)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return

            g = m.groups()
            method_name = g[0]
            param_str = g[1].strip()

            # check method signature
            if len(param_str) == 0:
                if method_name != 'readObjectNoData':
                    return
            else:
                param = param_str.split()[0]
                if method_name == 'readObject':
                    if not param.endswith('ObjectInputStream'):
                        return
                else:
                    # method_name == 'writeObject'
                    if not param.endswith('ObjectOutputStream'):
                        return

            # TODO: local search and global search for "implements Serializable" and "implements Externalizable"

            # check bug pattern
            if not strip_line.startswith('private'):
                line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                self.bug_accumulator.append(
                    BugInstance('SE_METHOD_MUST_BE_PRIVATE', priorities.MEDIUM_PRIORITY, context.cur_patch.name,
                                line_no, 'Method must be private in order for serialization to work.',
                                sha=context.cur_patch.sha, line_content=context.cur_line.content))

