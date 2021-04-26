import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

params = [
    # https://github.com/spotbugs/spotbugs/blob/a6f9acb2932b54f5b70ea8bc206afb552321a222/spotbugsTestCases/src/java/sfBugs/Bug1911620.java
    ('DLS_DEAD_LOCAL_INCREMENT_IN_RETURN', 'Bug1911620.java',
     '''@ExpectWarning("DLS_DEAD_LOCAL_INCREMENT_IN_RETURN")
        public int getIntMinus1Bad(String intStr) {
            int i = Integer.parseInt(intStr);
            return i--;
        }''', 1, 4),

    # DIY
    ('DLS_DEAD_LOCAL_INCREMENT_IN_RETURN', 'DLS_DEAD_LOCAL_INCREMENT_IN_RETURN',
     '''return arr[i]++;''', 0, 1),
]


@pytest.mark.parametrize('pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, False)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=('FindDeadLocalIncrementInReturn',))
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0