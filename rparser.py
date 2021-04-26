import copy
import re
from io import StringIO
from utils import logger, get_string_ranges, in_range
import traceback


class Hunk:
    """ Parsed hunk data container (hunk starts with @@ -R +R @@) """

    def __init__(self, startsrc=1, linessrc=0, starttgt=1, linestgt=0):
        '''
        :param startsrc: the line number of the start line in the source file
        :param linessrc: the number of lines of source files, including non-modified lines and deleted lines
        :param startsrc: the line number of the start line in the target file
        :param linessrc: the number of lines of source files, including non-modified lines and added lines
        :param lines: collections of Line objects
        :param dellines: indexes of deleted lines in @lines
        :param addlines: indexes of added lines in @lines
        '''
        self.startsrc = startsrc  #: line count starts with 1
        self.linessrc = linessrc
        self.starttgt = starttgt
        self.linestgt = linestgt
        self.lines = []
        self.dellines = []  # index of Line objects in self.text
        self.addlines = []

    def __iter__(self):
        for h in self.lines:
            yield h


class Line:
    def __init__(self, content, lineno=(-1, -1), is_patch=True):  # lineno的第一位是src里的lineno,第二位是tgt里的lineno
        self.lineno = lineno
        if is_patch and len(content) > 1:
            # In patch, the first character is reserved to indicate if the line is deleted or added
            self.prefix = content[0].strip()
            self.content = content[1:]
        else:
            self.prefix = ''
            self.content = content

    def __str__(self):
        if self.prefix:
            return self.prefix + self.content
        else:
            return self.content


class VirtualStatement(Line):
    """
    A virtual statement contains multiple lines ending with '\n'.
    It ends with ';', '{' or '}'. Its prefix should be set manually.
    """

    def __init__(self, line_obj: Line):
        super().__init__('', line_obj.lineno)
        self.sub_lines = []
        self.append_sub_line(line_obj)

    def append_sub_line(self, line_obj: Line):
        self.sub_lines.append(line_obj)
        self.content += line_obj.content

    def merge_vt_stmt(self, vt_stmt):
        self.sub_lines.extend(vt_stmt.sub_lines)
        self.content += vt_stmt.content

    def get_exact_lineno_by_keyword(self, key: str):
        """
        Get exact line number by keyword
        :param key: keyword string
        :return: lineno of Line object, or None if fail
        """
        for line in self.sub_lines:
            if key in line.content or line.content in key:
                return line.lineno
        return None

    def get_exact_lineno_by_offset(self, offset: int, if_strip=False):
        """
        Get exact line number by offset in line content
        :param offset: offset in line content string
        :param if_strip: if true, left strip the first sub-line and right strip the last sub-line
        :return: lineno of Line object, or None for invalid offset
        """
        size = len(self.sub_lines)
        i = 0
        while i < size:
            if i == 0 and if_strip:
                offset -= len(self.sub_lines[i].content.lstrip())
            elif i == size - 1 and if_strip:
                offset -= len(self.sub_lines[i].content.rstrip())
            else:
                offset -= len(self.sub_lines[i].content)

            if offset <= 0:
                return self.sub_lines[i].lineno

            i += 1
        return None


class Patch:
    """ Patch for a single file.
        If used as an iterable, returns hunks.
    """

    def __init__(self):
        self.name = ''
        self.hunks = []
        self.type = None
        self.sha = ''

    def __iter__(self):
        for h in self.hunks:
            yield h


# --------------------------------------------------------------------------------------
re_stmt_end = re.compile(r'[;{}]\s*$')
re_annotation = re.compile(r'^@[\w\_$]+(?:\(.*\))?$')
ann_left = re.compile(r'/\*')
ann_right = re.compile(r'\*/')
ann_slash = re.compile(r'//')


def _check_statement_end(line: str):
    """
    :param line: string without '+' or '-'
    :return: True or False
    """
    strip_line = line.strip()

    if strip_line.startswith('*'):  # skip possible lines in multi-line comments
        return False

    if (not strip_line) or re_stmt_end.search(strip_line) or re_annotation.match(strip_line) \
            or strip_line.endswith('*/') or strip_line.startswith('//'):
        return True
    if strip_line.startswith('case ') and strip_line.endswith(':'):
        return True
    return False


def _check_multiline_comment_start(line: str):
    return line.strip().startswith('/*')


def _check_multiline_comment_end(line: str):
    return line.strip().endswith('*/')


def _add_virtual_statement_to_hunk(vt_stmt: VirtualStatement, hunk: Hunk, prefix=''):
    # skip multiline comments
    if _check_multiline_comment_start(vt_stmt.content) or _check_multiline_comment_end(vt_stmt.content):
        return

    if prefix == '+':
        hunk.addlines.append(len(hunk.lines))
    elif prefix == '-':
        hunk.dellines.append(len(hunk.lines))

    vt_stmt.prefix = prefix
    hunk.lines.append(vt_stmt)


def _finish_vt_statement(line_obj: Line, vt_stmt: VirtualStatement, hunk: Hunk, prefix=''):
    """
    Add line object to the virtual statement, add virtual statement to the hunk
    """
    if line_obj:
        vt_stmt.append_sub_line(line_obj)
    _add_virtual_statement_to_hunk(vt_stmt, hunk, prefix)


def _skip_started_incomplete_multi_line_comments(comment_end_line_obj: Line, hunk: Hunk):
    prefix_tgt = comment_end_line_obj.prefix

    hunk.dellines.clear()
    hunk.addlines.clear()

    if prefix_tgt == '':
        # 更改前后的开头都是多行注释，清空 hunk
        hunk.lines.clear()
        return

    to_del_stmt = []

    # find lines to be remove
    for line_obj in hunk:
        prefix_cur = line_obj.prefix
        if prefix_tgt == prefix_cur:
            to_del_stmt.append(line_obj)

    # remove lines
    for line_obj in to_del_stmt:
        hunk.lines.remove(line_obj)

    # reset prefix of common lines, set hunk.dellines and hunk.addlines
    for i, line_obj in enumerate(hunk.lines):
        if line_obj.prefix == '':
            if prefix_tgt == '-':
                line_obj.prefix = '+'
            else:  # prefix_tgt == '+'
                line_obj.prefix = '-'

        if line_obj.prefix == '-':
            hunk.dellines.append(i)
        elif line_obj.prefix == '+':
            hunk.addlines.append(i)


def _parse_hunk(stream, is_patch, hunk=None):
    """
    Parse the content of a hunk
    :param stream: content to parse, exclude hunk header (i.e. '@@ -d,d +d,d @@')
    :param hunk: a hunk object with info
    :return: the hunk object
    """
    cnt_dict = {'linessrc': hunk.startsrc - 1, 'linestgt': hunk.starttgt - 1}

    # init statement. Priority: del_statement == add_statement > common_statement
    del_statement, add_statement, common_statement = None, None, None
    del_multi_comment, add_multi_comment = False, False
    # if a common_statement meets a del_statement, the first 'False' will be 'True',
    # similar relationship to the second 'False' and add_statement
    incomplete_common_statement = [False, False]
    all_lines_start_with_star = True

    for line in StringIO(stream):
        line_obj = Line(line, is_patch=is_patch)

        # remove single-line annotation from line content
        string_ranges = get_string_ranges(line_obj.content)

        left_stars = [m for m in ann_left.finditer(line_obj.content) if not in_range(m.start(), string_ranges)]
        right_stars = [m for m in ann_right.finditer(line_obj.content) if not in_range(m.start(), string_ranges)]
        if left_stars and right_stars:
            left, right = left_stars[0], right_stars[-1]
            if left.end()-1 != right.start():  # fix "/*/"
                old_content = line_obj.content
                line_obj.content = old_content[:left.start()] + old_content[right.end():]
                string_ranges = get_string_ranges(line_obj.content)

        slash_starts = [m.start() for m in ann_slash.finditer(line_obj.content) if not in_range(m.start(), string_ranges)]
        if slash_starts:
            line_obj.content = line_obj.content[:slash_starts[0]]

        # trim empty line, it will be skip in following branches
        strip_content = line_obj.content.strip()
        if not strip_content:
            line_obj.content = strip_content

        # flag for special hunk
        if strip_content and not strip_content.startswith("*"):
            all_lines_start_with_star = False

        # -------------------------- Del line -----------------------------
        if line_obj.prefix == "-":
            cnt_dict['linessrc'] += 1
            line_obj.lineno = (cnt_dict['linessrc'], -1)

            if common_statement:
                incomplete_common_statement[0] = True

            if not (del_multi_comment and add_multi_comment) and _check_multiline_comment_start(line_obj.content):
                del_multi_comment = True
                if del_statement:
                    # store the last del_statement
                    _add_virtual_statement_to_hunk(del_statement, hunk, '-')
                # new a del_statement for the multiline comment
                del_statement = VirtualStatement(line_obj)
                # then goto reset common_statement
            elif del_multi_comment:
                if not del_statement and common_statement:
                    del_statement = copy.deepcopy(common_statement)

                if _check_multiline_comment_end(line_obj.content):
                    _finish_vt_statement(line_obj, del_statement, hunk, '-')
                    del_statement = None
                    del_multi_comment = False
                else:
                    del_statement.append_sub_line(line_obj)  # then goto reset common_statement
            elif not del_multi_comment and _check_multiline_comment_end(line_obj.content):
                _skip_started_incomplete_multi_line_comments(line_obj, hunk)
                del_statement = None
                if common_statement and not incomplete_common_statement[1]:
                    add_multi_comment = True
            elif _check_statement_end(line_obj.content):  # whether line is a complete statement or not
                if not line_obj.content:
                    continue  # skip blank line or single line comments

                if not del_statement:
                    if (common_statement and add_multi_comment) or not common_statement:
                        hunk.dellines.append(len(hunk.lines))
                        hunk.lines.append(line_obj)
                        continue
                # line_obj belongs to a del_statement
                if not del_statement and common_statement:
                    del_statement = copy.deepcopy(common_statement)
                _finish_vt_statement(line_obj, del_statement, hunk, '-')
                del_statement = None
            else:
                # if line_obj is a incomplete statement, it must belong to del_statement
                if not del_statement:
                    if common_statement:
                        del_statement = copy.deepcopy(common_statement)
                        del_statement.append_sub_line(line_obj)
                    else:
                        del_statement = VirtualStatement(line_obj)
                else:
                    del_statement.append_sub_line(line_obj)
        # -------------------------- Add line -----------------------------
        elif line_obj.prefix == "+":
            cnt_dict['linestgt'] += 1
            line_obj.lineno = (-1, cnt_dict['linestgt'])

            if common_statement:
                incomplete_common_statement[1] = True

            if not (del_multi_comment and add_multi_comment) and _check_multiline_comment_start(line_obj.content):
                add_multi_comment = True
                if add_statement:
                    # store the last add_statement
                    _add_virtual_statement_to_hunk(add_statement, hunk, '+')
                # new a add_statement for the multiline comment
                add_statement = VirtualStatement(line_obj)
                # then goto reset common_statement
            elif add_multi_comment:
                if not add_statement and common_statement:
                    add_statement = copy.deepcopy(common_statement)

                if _check_multiline_comment_end(line_obj.content):
                    _finish_vt_statement(line_obj, add_statement, hunk, '+')
                    add_statement = None
                    add_multi_comment = False
                else:
                    add_statement.append_sub_line(line_obj)  # then goto reset common_statement
            elif not add_multi_comment and _check_multiline_comment_end(line_obj.content):
                _skip_started_incomplete_multi_line_comments(line_obj, hunk)
                add_statement = None
                if common_statement and not incomplete_common_statement[0]:
                    del_multi_comment = True
            elif _check_statement_end(line_obj.content):
                if not line_obj.content:
                    continue  # skip blank line or single line comments

                if not add_statement:
                    if (common_statement and del_multi_comment) or not common_statement:
                        hunk.addlines.append(len(hunk.lines))
                        hunk.lines.append(line_obj)
                        continue

                # line_obj belongs to a add_statement
                if common_statement and not add_statement:
                    add_statement = copy.deepcopy(common_statement)
                _finish_vt_statement(line_obj, add_statement, hunk, '+')
                add_statement = None
            else:
                # if line_obj is a incomplete statement, it must belong to add_statement
                if not add_statement:
                    if common_statement:
                        add_statement = copy.deepcopy(common_statement)
                        add_statement.append_sub_line(line_obj)
                    else:
                        add_statement = VirtualStatement(line_obj)
                else:
                    add_statement.append_sub_line(line_obj)
        # -------------------------- common line -----------------------------
        else:
            cnt_dict['linessrc'] += 1
            cnt_dict['linestgt'] += 1
            line_obj.lineno = (cnt_dict['linessrc'], cnt_dict['linestgt'])

            if not (del_multi_comment or add_multi_comment) and _check_multiline_comment_start(line_obj.content):
                add_multi_comment = True
                del_multi_comment = True

                if common_statement:
                    _add_virtual_statement_to_hunk(common_statement, hunk)
                common_statement = VirtualStatement(line_obj)
                # reset incomplete_common_statement
                incomplete_common_statement[0], incomplete_common_statement[1] = False, False

                if del_statement:
                    _add_virtual_statement_to_hunk(del_statement, hunk, '-')
                    del_statement = None
                if add_statement:
                    _add_virtual_statement_to_hunk(add_statement, hunk, '+')
                    add_statement = None

            elif add_multi_comment and del_multi_comment:
                if _check_multiline_comment_end(line_obj.content):
                    if common_statement:
                        _finish_vt_statement(line_obj, common_statement, hunk)
                        common_statement = None
                    if del_statement:
                        _finish_vt_statement(line_obj, del_statement, hunk, '-')
                        del_statement = None
                    if add_statement:
                        _finish_vt_statement(line_obj, add_statement, hunk, '+')
                        add_statement = None
                    add_multi_comment, del_multi_comment = False, False
                else:
                    if common_statement:
                        common_statement.append_sub_line(line_obj)
                    if del_statement:
                        del_statement.append_sub_line(line_obj)
                    if add_statement:
                        add_statement.append_sub_line(line_obj)
            elif del_multi_comment and not add_multi_comment:
                if _check_multiline_comment_end(line_obj.content):
                    _finish_vt_statement(line_obj, del_statement, hunk, '-')
                    del_statement, del_multi_comment = None, False
                else:
                    # multi-line comments
                    del_statement.append_sub_line(line_obj)

                    # code branch: turn common line to added line
                    line_obj = copy.deepcopy(line_obj)
                    line_obj.prefix = '+'

                    if _check_statement_end(line_obj.content):
                        if not line_obj.content:
                            continue  # skip blank line or single line comments

                        if not add_statement:
                            hunk.addlines.append(len(hunk.lines))
                            hunk.lines.append(line_obj)
                        else:
                            _finish_vt_statement(line_obj, add_statement, hunk, '+')
                            add_statement = None
                    else:
                        if not add_statement:
                            add_statement = VirtualStatement(line_obj)
                        else:
                            add_statement.append_sub_line(line_obj)
            elif not del_multi_comment and add_multi_comment:
                if _check_multiline_comment_end(line_obj.content):
                    _finish_vt_statement(line_obj, del_statement, hunk, '+')
                    add_statement, add_multi_comment = None, False
                else:
                    # multi-line comments
                    add_statement.append_sub_line(line_obj)

                    # code branch: turn common line to added line
                    line_obj = copy.deepcopy(line_obj)
                    line_obj.prefix = '-'

                    if _check_statement_end(line_obj.content):
                        if not line_obj.content:
                            continue  # skip blank line or single line comments

                        if not del_statement:
                            hunk.dellines.append(len(hunk.lines))
                            hunk.lines.append(line_obj)
                        else:
                            _finish_vt_statement(line_obj, del_statement, hunk, '-')
                            del_statement = None
                    else:
                        if not del_statement:
                            del_statement = VirtualStatement(line_obj)
                        else:
                            del_statement.append_sub_line(line_obj)
            elif not del_multi_comment and not add_multi_comment and _check_multiline_comment_end(line_obj.content):
                _skip_started_incomplete_multi_line_comments(line_obj, hunk)
                common_statement, add_statement, del_statement = None, None, None
            elif _check_statement_end(line_obj.content):
                if not line_obj.content:
                    continue  # skip blank line or single line comments

                if not (common_statement or del_statement or add_statement):
                    hunk.lines.append(line_obj)
                    continue

                # if both add_statement and del_statement are not None, common_statement must be none
                if common_statement:
                    _finish_vt_statement(line_obj, common_statement, hunk)
                    common_statement = None
                if del_statement:
                    _finish_vt_statement(line_obj, del_statement, hunk, '-')
                    del_statement = None
                if add_statement:
                    _finish_vt_statement(line_obj, add_statement, hunk, '+')
                    add_statement = None
            else:
                if not (common_statement or add_statement or del_statement):
                    common_statement = VirtualStatement(line_obj)
                    continue

                if common_statement:
                    common_statement.append_sub_line(line_obj)
                if del_statement:
                    del_statement.append_sub_line(line_obj)
                if add_statement:
                    add_statement.append_sub_line(line_obj)
        # -------------------------- Reset Common_Statement -----------------------------
        if common_statement and incomplete_common_statement[0] and incomplete_common_statement[1]:
            common_statement = None
            incomplete_common_statement[0], incomplete_common_statement[1] = False, False
        elif not common_statement and (incomplete_common_statement[0] or incomplete_common_statement[1]):
            incomplete_common_statement[0], incomplete_common_statement[1] = False, False

    if not all_lines_start_with_star:
        if common_statement:
            _add_virtual_statement_to_hunk(common_statement, hunk)

        if del_statement:
            _add_virtual_statement_to_hunk(del_statement, hunk, '-')

        if add_statement:
            _add_virtual_statement_to_hunk(add_statement, hunk, '+')

    return hunk


re_hunk_start = re.compile(r'@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@[^\n]*\n')


def parse(stream, is_patch=True, name=''):
    """
    parse modifications of a file
    :param name: name of file
    :param stream: content of a patch or a hunk
    :param is_patch: stream contains lines like '@@ -d,d +d,d @@' or not
    :return: a patch object
    """

    patch = Patch()
    patch.name = name
    try:
        if not is_patch:
            patch.hunks.append(_parse_hunk(stream, is_patch, Hunk()))
        else:
            hunk_bounds = []

            matches = re_hunk_start.finditer(stream)
            for match in matches:
                g = match.groups()
                startsrc = int(g[0])
                linessrc = int(g[1]) if g[1] else 0  # fix case like '@@ -1 +1,21 @@'
                starttgt = int(g[2])
                linestgt = int(g[3]) if g[3] else 0

                patch.hunks.append(Hunk(startsrc, linessrc, starttgt, linestgt))
                hunk_bounds.append((match.start(), match.end()))

            last_end = hunk_bounds[0][1]
            for i in range(1, len(hunk_bounds)):
                hunk_content = stream[last_end:hunk_bounds[i][0]]
                _parse_hunk(hunk_content, is_patch, patch.hunks[i - 1])
                last_end = hunk_bounds[i][1]
            _parse_hunk(stream[last_end:], is_patch, patch.hunks[-1])
    except Exception as e:
        logger.error(f'[Parser Error] {name}\n{e}\n{traceback.format_exc()}')
    return patch
