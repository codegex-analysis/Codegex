import pytest

from patterns.models.context import Context
from rparser import parse
from patterns.models.engine import DefaultEngine

params = [
    # // https://github.com/eclipsesource/J2V8/pull/504/files#diff-a892003576f3e242006668a1b63c89dff9144c4e4b343020847ad103b53e6b03R79
    ('FI_EXPLICIT_INVOCATION', 'Fake.java',
     '''@@ -0,0 +1,7 @@ @Override protected void finalize() {
            try {
                super.finalize();
            } catch (Throwable t) { }

            if (!receiver.isReleased()) {
                receiver.release();
            }

            if (!function.isReleased()) {
                function.release();
            }
        }''', 0, 2),
    # From spotBugs: https://github.com/spotbugs/spotbugs/blob/3883a7b750fb339577be073bc45e36b6f268777b/spotbugsTestCases/src/java/bugPatterns/FI_EXPLICIT_INVOCATION.java
    ('FI_EXPLICIT_INVOCATION', 'Fake.java',
     '''@@ -622,7 +622,7 @@     void bug(FI_EXPLICIT_INVOCATION any) throws Throwable {
                         any.finalize();
                     }''', 1, 622),
    # From other repository: https: // github.com / ustcweizhou / libvirt - java / commit / c827e87d958d1cb7a969747fcb6c8c1724a7889d
    ('FI_PUBLIC_SHOULD_BE_PROTECTED', 'Connect.java',
     '''@@ -533,6 +533,7 @@ public String domainXMLToNative(String nativeFormat, String domainXML, int flags
             }
    
             @Override
        +    public void finalize() throws LibvirtException {
               close();
                    }''', 1, 536)
]


@pytest.mark.parametrize('pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=('ExplicitInvDetector', 'PublicAccessDetector'))
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0
