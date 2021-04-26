import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

params = [
    # https://github.com/spotbugs/spotbugs/blob/3883a7b750fb339577be073bc45e36b6f268777b/spotbugsTestCases/src/java/bugIdeas/Ideas_2011_11_02.java
    (True, 'RV_EXCEPTION_NOT_THROWN', 'Ideas_2011_11_02.java',
     '''@@ -11,3 +11,3 @@ public class Ideas_2011_11_02 {
            public void setCheckedElements(Object[] elements) {
                 new UnsupportedOperationException();
        }''', 1, 12),
    # https://github.com/bndtools/bnd/commit/960664b12a8f8886779617a283883cdc901cef5e
    (True, 'RV_EXCEPTION_NOT_THROWN', 'Clazz.java',
     '''@@ -1114,6 +1114,7 @@ void doSignature(DataInputStream in, ElementType member, int access_flags) throw
				classSignature = signature;

		} catch (Exception e) {
+	        new RuntimeException("Signature failed for" + signature, e);
		}
	}''', 1, 1117),
     # https://github.com/AzureSDKAutomation/azure-sdk-for-java/pull/7314/files
    (True, 'RV_EXCEPTION_NOT_THROWN', 'Fake_01.java',
     '''@@ -733,6 +734,7 @@ public WorkspaceInner createOrUpdate(
                    new IllegalArgumentException(
                        "Parameter this.client.getSubscriptionId() is required and cannot be null."))''', 0, 0),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, is_patch)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=['NotThrowDetector'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0
