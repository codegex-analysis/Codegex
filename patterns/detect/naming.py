import regex

from patterns.models.detectors import Detector, get_exact_lineno
from patterns.models.bug_instance import BugInstance
from patterns.models.priorities import *
from utils import get_string_ranges, in_range

GENERIC_REGEX = regex.compile(r'(?P<gen><(?:[^<>]++|(?&gen))*>)')
CLASS_EXTENDS_REGEX = regex.compile(r'\bclass\s+([\w$]+)\s*(?P<gen><(?:[^<>]++|(?&gen))*>)?\s+extends\s+([\w$.]+)')
INTERFACE_EXTENDS_REGEX = regex.compile(r'\binterface\s+([\w$]+)\s*(?P<gen><(?:[^<>]++|(?&gen))*>)?\s+extends\s+([^{]+)')
ENUM_REGEX = regex.compile(r'\benum\s+\w+\s*(?:\b(?:extends|implements)\s+[\w<>,\s]+)*\s*{')


class SimpleSuperclassNameDetector(Detector):
    def __init__(self):
        # class can extend only one superclass, but implements multiple interfaces
        # extends clause must occur before implements clause
        self.pattern = CLASS_EXTENDS_REGEX
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if not all(key in line_content for key in ('class', 'extends')):
            return

        m = self.pattern.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return
            g = m.groups()
            class_name = g[0]
            super_classes = GENERIC_REGEX.sub('', g[2])  # remove <...>
            super_classes_list = [name.rsplit('.', 1)[-1].strip() for name in super_classes.split(',')]

            if class_name in super_classes_list:
                if len(line_content) == len(line_content.lstrip()):  # if do not have leading space
                    line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance('NM_SAME_SIMPLE_NAME_AS_SUPERCLASS', HIGH_PRIORITY,
                                    context.cur_patch.name, line_no,
                                    'Class names shouldn’t shadow simple name of superclass', sha=context.cur_patch.sha, line_content=context.cur_line.content)
                    )


class SimpleInterfaceNameDetector(Detector):
    def __init__(self):
        # Check interfaces implemented by a class
        self.pattern1 = regex.compile(
            r'class\s+([\w$]+)\b.*\bimplements\s+([^{]+)', flags=regex.DOTALL)
        # Check interfaces extended by a interface
        # No implements clause allowed for interface
        # Interface can extend multiple super interfaces
        self.pattern2 = INTERFACE_EXTENDS_REGEX
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if all(key in line_content for key in ('class', 'implements')):
            m = self.pattern1.search(line_content)
        elif all(key in line_content for key in ('interface', 'extends')):
            m = self.pattern2.search(line_content)
        else:
            return

        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return

            g = m.groups()
            class_name = g[0]
            super_interfaces = GENERIC_REGEX.sub('', g[-1])  # remove <...>
            super_interface_list = [name.rsplit('.', 1)[-1].strip() for name in super_interfaces.split(',')]

            if class_name in super_interface_list:
                if len(line_content) == len(line_content.lstrip()):
                    line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance('NM_SAME_SIMPLE_NAME_AS_INTERFACE', MEDIUM_PRIORITY,
                                    context.cur_patch.name, line_no,
                                    'Class or interface names shouldn’t shadow simple name of implemented interface',
                                    sha=context.cur_patch.sha, line_content=context.cur_line.content)
                    )


class HashCodeNameDetector(Detector):
    def __init__(self):
        # Check hashcode method exists
        self.pattern = regex.compile(r'\bint\s+hashcode\s*\(\s*\)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if line_content.strip().startswith('private') or any(key not in line_content for key in ('int', 'hashcode')):
            return

        m = self.pattern.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return
            line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
            self.bug_accumulator.append(
                BugInstance('NM_LCASE_HASHCODE', HIGH_PRIORITY, context.cur_patch.name, line_no,
                            "Class defines hashcode(); should it be hashCode()?", sha=context.cur_patch.sha, line_content=context.cur_line.content))


class ToStringNameDetector(Detector):
    def __init__(self):
        # Check hashcode method exists
        self.pattern = regex.compile(r'\bString\s+tostring\s*\(\s*\)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if line_content.strip().startswith('private') or any(key not in line_content for key in ('String', 'tostring')):
            return
        m = self.pattern.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return
            line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
            self.bug_accumulator.append(
                BugInstance('NM_LCASE_TOSTRING', HIGH_PRIORITY, context.cur_patch.name, line_no,
                            'Class defines tostring(); should it be toString()?', sha=context.cur_patch.sha, line_content=context.cur_line.content))


class EqualNameDetector(Detector):
    def __init__(self):
        # Check hashcode method exists
        self.pattern = regex.compile(r'\bboolean\s+equal\s*\(\s*Object\s+[\w$]+\s*\)')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if line_content.strip().startswith('private') or 'equals' in line_content \
                or any(key not in line_content for key in ('boolean', 'equal')):
            return
        m = self.pattern.search(line_content)
        if m:
            string_ranges = get_string_ranges(line_content)
            if in_range(m.start(0), string_ranges):
                return
            line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
            self.bug_accumulator.append(
                BugInstance('NM_BAD_EQUAL', HIGH_PRIORITY, context.cur_patch.name, line_no,
                            'Class defines equal(Object); should it be equals(Object)?', sha=context.cur_patch.sha, line_content=context.cur_line.content))


class ClassNameConventionDetector(Detector):
    def __init__(self):
        # Match class name
        self.cn_pattern = regex.compile(r'class\s+([a-z][\w$]+)[^{]*{')
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if 'class ' in line_content and '{' in line_content:
            its = self.cn_pattern.finditer(line_content)
            string_ranges = get_string_ranges(line_content)
            for m in its:
                if in_range(m.start(0), string_ranges):
                    continue

                class_name = m.groups()[0]
                if "Proto$" in class_name:
                    return
                # reference from https://github.com/spotbugs/spotbugs/blob/a6f9acb2932b54f5b70ea8bc206afb552321a222
                # /spotbugs/src/main/java/edu/umd/cs/findbugs/detect/Naming.java#L389
                if '_' not in class_name:
                    priority = LOW_PRIORITY
                    if any(access in line_content for access in ('public', 'protected')):
                        priority = MEDIUM_PRIORITY

                    line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance('NM_CLASS_NAMING_CONVENTION', priority, context.cur_patch.name, line_no,
                                    'Nm: Class names should start with an upper case letter',
                                    sha=context.cur_patch.sha, line_content=context.cur_line.content))


class MethodNameConventionDetector(Detector):
    def __init__(self):
        # Extract the method name
        self.mn_pattern = regex.compile(
            r'@?(\b\w+\s+)?(?:\b\w+\s*\.\s*)*(\b\w+)\s*\(\s*((?:(?!new)\w)+(?P<gen><(?:[^<>]++|(?&gen))*>)?\s+\w+)?')
        self.patch, self.is_enum = None, False
        Detector.__init__(self)

    def match(self, context):
        line_content = context.cur_line.content
        if '(' in line_content:
            its = self.mn_pattern.finditer(line_content)
            string_ranges = get_string_ranges(line_content)
            for m in its:
                # skip annotations
                if line_content[m.start(0)] == '@':
                    continue
                if in_range(m.start(0), string_ranges):
                    continue
                g = m.groups()
                pre_token = g[0].strip() if g[0] else g[0]
                method_name = g[1]
                args_def = g[2]

                # skip statements like "new Object(...)"
                if pre_token == 'new':
                    continue
                # skip constructor definitions, like "public Object(int i)"
                if pre_token in ('public', 'private', 'protected', 'static'):
                    continue
                # skip constructor definitions without access modifier, like "Object (int i)", "Object() {"
                is_def = args_def or line_content.rstrip().endswith('{') or line_content.rstrip().endswith('}')
                if not pre_token and is_def:
                    continue

                if len(method_name) >= 2 and method_name[0].isalpha() and not method_name[0].islower() and \
                        method_name[1].isalpha() and method_name[1].islower() and '_' not in method_name:
                    if not is_def:
                        # i.e. obj.MethodName(param), or MethodName(param)
                        self._local_search(context)
                        if self.is_enum:  # skip elements defined in enum
                            continue
                        else:
                            priority = IGNORE_PRIORITY
                    else:
                        priority = LOW_PRIORITY
                        if any(access in line_content for access in ('public', 'protected')):
                            priority = MEDIUM_PRIORITY

                    line_no = get_exact_lineno(m.end(0), context.cur_line)[1]
                    self.bug_accumulator.append(
                        BugInstance('NM_METHOD_NAMING_CONVENTION', priority, context.cur_patch.name, line_no,
                                    'Nm: Method names should start with a lower case letter',
                                    sha=context.cur_patch.sha, line_content=context.cur_line.content))
                    return

    def _local_search(self, context):
        # check if patch is updated
        if context.cur_patch != self.patch:
            self.patch = context.cur_patch
            for hunk in self.patch:
                for line in hunk:
                    if line.prefix == '-':
                        continue
                    m = ENUM_REGEX.search(line.content)
                    if m:
                        string_ranges = get_string_ranges(line.content)
                        if not in_range(m.start(0), string_ranges):
                            self.is_enum = True
                            return
            self.is_enum = False
