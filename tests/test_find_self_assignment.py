import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

params = [
    # --------------- SA_SELF_ASSIGNMENT ---------------
    # https://github.com/emilianbold/main-silver/commit/b0b69ce5e52786362bb18d9f0b582cd9866e2a4f
    (True, 'SA_SELF_ASSIGNMENT', 'CountLimit.java',
     '''@@ -111,10 +107,11 @@ public CountLimit(String text) {
	} else if (text.equals(Action_DISABLE) ||
		   text.trim().equals("")) { // NOI18N
	    text = null;
	} else {
	    // Let Node, validateText2(0, do further validation
	    text = text;
	}''', 1, 112),
    # DIY
    (False, 'SA_SELF_ASSIGNMENT', 'Test01.java', '''int foo = foo;''', 1, 1),
    (False, 'SA_SELF_ASSIGNMENT', 'Test02.java', '''this.foo = foo;''', 0, 1),
    (False, 'SA_DOUBLE_ASSIGNMENT', 'FP_01.java', '''this.getGameSetup().whitePlayer = whitePlayer;''', 0, 0),

    # --------------- SA_DOUBLE_ASSIGNMENT ---------------
    # https://github.com/shweta1021/jenkins/commit/7aa09f4674f41b8514da2acee531a1d01d1d3071
    (True, 'SA_DOUBLE_ASSIGNMENT', 'core/src/main/java/hudson/model/View.java',
     '''@@ -1355,7 +1355,7 @@ public static View create(StaplerRequest req, StaplerResponse rsp, ViewGroup own
    private static View copy(StaplerRequest req, ViewGroup owner, String name) throws IOException {
        View v;
        String from = req.getParameter("from");
        View src = src = owner.getView(from);
        if(src==null) {
            if(Util.fixEmpty(from)==null)''', 1, 1358),
    # DIY
    (False, 'SA_DOUBLE_ASSIGNMENT', 'Test02.java', '''int foo = foo = 17;''', 1, 1),
    (False, 'SA_DOUBLE_ASSIGNMENT', 'Test03.java', '''foo = foo = 17 + methodCall(arg1, "arg2");''', 1, 1),
    (False, 'SA_DOUBLE_ASSIGNMENT', 'Test04.java', '''this.foo = foo = 10;''', 0, 1),
    (False, 'SA_DOUBLE_ASSIGNMENT', 'Test05.java', '''boolean foo = False;
foo = foo == True;''', 0, 1),
    (False, 'SA_DOUBLE_ASSIGNMENT', 'Test06.java', '''this.getGameSetup().whitePlayer = whitePlayer = 17;''', 0, 0),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, is_patch)
    engine = DefaultEngine(Context(), included_filter=['CheckForSelfAssignment', 'CheckForSelfDoubleAssignment'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0