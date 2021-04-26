import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

params = [
    #  From other repository: https://github.com/vavr-io/vavr/pull/1752#discussion_r92956593
    (True, 'IL_CONTAINER_ADDED_TO_ITSELF', 'Fake.java',
    '''@@ -14,8 +15,9 @@
    final java.util.List<Object> testee = empty();
    testee.add(testee);
    assertThat(testee.containsAll(testee)).isTrue();
    ''', 1, 16),
    # From other repository: https://github.com/powsybl/powsybl-core/pull/1316/files#diff-ec7fd47ba0877273594bf79f852d46fde2adb8c2319c39467c7fe162d4c0c80bR34
    (True, 'IL_CONTAINER_ADDED_TO_ITSELF', 'Fake.java',
     '''@@ -1,0 +1,0 @@ Substation substation = network.newSubstation()
                .setId("S")
                .add();''', 0, 2),
    # DIY
    (True, 'IL_CONTAINER_ADDED_TO_ITSELF', 'Fake.java',
         '''@@ -1,0 +1,0 @@ Substation substation = network.newSubstation()
                    .add();''', 0, 2),
    (False, 'IL_CONTAINER_ADDED_TO_ITSELF', 'DIY_01.java',
     'return obj.testee.add(testee);', 0, 2),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, is_patch)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=['CollectionAddItselfDetector'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0