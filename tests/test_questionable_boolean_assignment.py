import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse


params =[
    # https://github.com/TouK/sputnik-test/pull/3#discussion_r57453267
    (False, 'QBA_QUESTIONABLE_BOOLEAN_ASSIGNMENT', 'BadCode.java',
     '''private static void incorrectAssignmentInIfCondition() {
            boolean value = false;
            if (value = false) {''', 1, 3),
    # DIY
    (False, 'QBA_QUESTIONABLE_BOOLEAN_ASSIGNMENT', 'DIY_01.java',
     '''if ( a == b && value = false) {''', 1, 1),
    # https://github.com/spotbugs/spotbugs/issues/1149
    (False, 'QBA_QUESTIONABLE_BOOLEAN_ASSIGNMENT', 'DIY_02.java',
     '''if (scanning = b == true)''', 0, 0),
    (False, 'QBA_QUESTIONABLE_BOOLEAN_ASSIGNMENT', 'DIY_03.java',
     '''if (content.contains("table.MotionDetect[0].Enable=true")) {''', 0, 0),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, is_patch)
    patch.name = file_name

    engine = DefaultEngine(Context(), included_filter=['BooleanAssignmentDetector'])
    engine.visit(patch)

    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0