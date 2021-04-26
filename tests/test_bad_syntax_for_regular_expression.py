import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse
from patterns.models.priorities import *

params = [
    # https://github.com/spotbugs/spotbugs/blob/a6f9acb2932b54f5b70ea8bc206afb552321a222/spotbugsTestCases/src/java/bugPatterns/RE_POSSIBLE_UNINTENDED_PATTERN.java
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_01.java',
     '''@ExpectWarning("RE_POSSIBLE_UNINTENDED_PATTERN")
        String [] bug1(String any) {
            return any.split(".");
        }''', 1, 3, HIGH_PRIORITY),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_02.java',
     '''String bug2(String any, String any2) {
            return any.replaceAll(".", any2);
        }''', 1, 2, MEDIUM_PRIORITY),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_03.java',
     '''return any.replaceFirst(".", any2);''', 1, 1, HIGH_PRIORITY),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_04.java',
     '''return any.split("|");''', 1, 1, HIGH_PRIORITY),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_05.java',
     '''return any.replaceAll("|", any2);''', 1, 1, HIGH_PRIORITY),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_06.java',
     '''return any.replaceFirst("|", any2);''', 1, 1, HIGH_PRIORITY),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_07.java',
     '''return any.replaceAll("|", "*");''', 1, 1, HIGH_PRIORITY),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_08.java',
     '''return any.replaceAll(".", "*");''', 0, 1, None),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_09.java',
     '''return any.indexOf(".");''', 0, 1, None),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'RE_POSSIBLE_UNINTENDED_PATTERN_10.java',
     '''return any.indexOf("|");''', 0, 1, None),
    # DIY
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'DIY_01.java',
     '''return any.matches("|");''', 1, 1, HIGH_PRIORITY),
    (False, 'RE_POSSIBLE_UNINTENDED_PATTERN', 'DIY_02.java',
     '''return customized.replaceAll("|", any2, arg3);''', 0, 1, None),

    # ------------------------ RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION ------------------------
    # https://github.com/spotbugs/spotbugs/blob/a6f9acb2932b54f5b70ea8bc206afb552321a222/spotbugsTestCases/src/java/bugPatterns/RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION.java#L9
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_01.java',
     '''void bug1(String any1, String any2) {
            any1.replaceAll(File.separator, any2);
        }''', 1, 2, HIGH_PRIORITY),
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_02.java',
     '''void bug2(String any1, String any2) {
            any1.replaceFirst(File.separator, any2);
        }''', 1, 2, HIGH_PRIORITY),
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_03.java',
     'any1.split(File.separator);', 1, 1, HIGH_PRIORITY),
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_04.java',
     'any1.matches(File.separator);', 1, 1, LOW_PRIORITY),
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_05.java',
     'Pattern.compile(File.separator);', 1, 1, HIGH_PRIORITY),
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_06.java',
     'Pattern.compile(File.separator, Pattern.CASE_INSENSITIVE);', 1, 1, HIGH_PRIORITY),
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_07.java',
     'Pattern.compile(File.separator, Pattern.LITERAL);', 0, 1, None),
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_08.java',
     'Pattern.compile(File.separator, Pattern.DOTALL);', 1, 1, HIGH_PRIORITY),
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_09.java',
     'Pattern.compile(File.separator, Pattern.LITERAL | Pattern.CASE_INSENSITIVE);', 0, 1, None),
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION_10.java',
     'Pattern.compile(File.separator, Pattern.DOTALL | Pattern.LITERAL);', 0, 1, None),
    # DIY
    (False, 'RE_CANT_USE_FILE_SEPARATOR_AS_REGULAR_EXPRESSION', 'DIY_03.java',
     '''Pattern.matches(
            File.separator, "hh");''', 1, 2, HIGH_PRIORITY),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no,expected_priority', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int,
         line_no: int, expected_priority: int):
    patch = parse(patch_str, is_patch, name=file_name)
    engine = DefaultEngine(Context(), included_filter=('SingleDotPatternDetector', 'FileSeparatorAsRegexpDetector'))
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
        if expected_priority is not None:
            assert engine.bug_accumulator[0].priority == expected_priority
    else:
        assert len(engine.bug_accumulator) == 0