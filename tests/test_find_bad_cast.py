import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

params = [
    # https://github.com/spotbugs/spotbugs/blob/a6f9acb2932b54f5b70ea8bc206afb552321a222/spotbugsTestCases/src/java/bugIdeas/Ideas_2010_10_11.java
    ('BC_IMPOSSIBLE_DOWNCAST_OF_TOARRAY', 'Ideas_2010_10_11',
     '''public class Ideas_2010_10_11 {

    @ExpectWarning("BC_IMPOSSIBLE_DOWNCAST_OF_TOARRAY")
    public void cascadeDelete(Collection value) throws RemoveException
    {
       if(!value.isEmpty())
       {
          EJBLocalObject[] locals = (EJBLocalObject[])value.toArray();
          for(int i = 0; i < locals.length; ++i)
          {
             locals[i].remove();
          }
       }
    }
}
     ''', 1, 8),
    # DIY
    ('BC_IMPOSSIBLE_DOWNCAST_OF_TOARRAY', 'Main02.java',
     '''public Main02.java{
     Object[] test2(Collection<String> c) {
        return (Object[]) c.toArray();
    }
}
     ''', 0, 1),
    ('BC_IMPOSSIBLE_DOWNCAST_OF_TOARRAY', 'Main03.java',
     '''public Main03.java{
     void test3(Collection<String> c) {
        Arrays.asList(new String[] { "a" }).toArray();
    }
}
     ''', 0, 1),
    ('BC_IMPOSSIBLE_DOWNCAST_OF_TOARRAY', 'Main04.java',
     '''public Main04.java{
     void test4(Collection<String> c) {
         Arrays.asList(new String[]{}).toArray();
    }
}
     ''', 0, 1),
    ('BC_IMPOSSIBLE_DOWNCAST_OF_TOARRAY', 'Main05.java',
     '''public Main05.java{
     void test5(c) {
         String[] strArr = (String[])new LinkedList<String>().toArray();
    }
}
     ''', 1, 3),
    ('BC_IMPOSSIBLE_DOWNCAST_OF_TOARRAY', 'Main06.java',
     '''public Main06.java{
     String[] test6(Collection<String> c) {
        return (String[]) c.toArray();
    }
}
     ''', 1, 3),
    # https://github.com/biojava/biojava/blob/master/biojava-structure/src/test/java/org/biojava/nbio/structure/io/mmtf/TestMmtfUtils.java#L250
    ('BC_IMPOSSIBLE_DOWNCAST_OF_TOARRAY', 'biojava/TestMmtfUtils.java',
     'assertArrayEquals(testData, (double[]) transMap.keySet().toArray()[0], 0.0);', 0, 0),
]


@pytest.mark.parametrize('pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, False)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=('FindBadCastDetector',))
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0
