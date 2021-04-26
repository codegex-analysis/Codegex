import pytest

from patterns.models.context import Context
from rparser import parse
from patterns.models.engine import DefaultEngine

params = [
    # DIY
    (False, 'FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER', 'Main.java',
     '''public class FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER {
    boolean test1(int op){
        return 0 > Float.NaN;
    }
}
     ''', 1, 3),
    # DIY
    (False, 'FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER', 'Main.java',
     '''public class FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER {
    boolean test1(int op){
        return 1.0 < Float.NaN;
    }
}
     ''', 1, 3),
    # DIY
    (False, 'FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER', 'Main.java',
     '''public class FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER {
    boolean test1(int op){
        return 0.0001 != Double.NaN;
    }
}
     ''', 1, 3),
    # DIY
    (False, 'FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER', 'Main.java',
     '''public class FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER {
    boolean test1(int op){
        return 3f < Double.NaN;
    }
}
     ''', 1, 3),
    # DIY
    (False, 'FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER', 'Main.java',
     '''public class FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER {
    double x = 1.0;
    if (x == Double.NaN){
        System.out.println("hit");
    }
}
     ''', 1, 3),
    # DIY
    (False, 'FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER', 'Main.java',
     '''public class FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER {
    double x = 1.0;
    if (x >= Double.NaN){
        System.out.println("hit");
    }
}
     ''', 1, 3),
    # DIY
    (False, 'FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER', 'Main.java',
     '''public class FE_TEST_IF_EQUAL_TO_NOT_A_NUMBER {
    double x = 1.0;
    if (x <= Double.NaN){
        System.out.println("hit");
    }
}
     ''', 1, 3)
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, is_patch)
    patch.name = file_name

    engine = DefaultEngine(Context(), included_filter=['FloatEqualityDetector'])
    engine.visit(patch)

    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0