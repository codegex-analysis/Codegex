import pytest
from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

params = [
    # From other repositories: https://github.com/usgs/warc-iridium-sbd-decoder/commit/505f5832c975be601acf9ccdfcd729e0134d79f7
    (True, 'DMI_USING_REMOVEALL_TO_CLEAR_COLLECTION', 'OBlock.java',
     '''@@ -963,6 +967,7 @@ public void dispose() {
                 // remove portal and stub paths through portal in opposing block
                 opBlock.removePortal(portal);
             }
             _portals.removeAll(_portals);
             List<Path> pathList = getPaths();
             for (int i = 0; i < pathList.size(); i++) {
                 removePath(pathList.get(i));''',
     1, 970),
    # From other repositories: https://github.com/erzhen1379/hbase2.1.4/blob/fc65d24aa0043529f3d44ad4b6e50835b0beb056/hbase-common/src/test/java/org/apache/hadoop/hbase/util/TestConcatenatedLists.java#L129
    (True, 'DMI_VACUOUS_SELF_COLLECTION_CALL', 'TestConcatenatedLists.java',
     '''@@ -963,6 +967,7 @@   private void verify(ConcatenatedLists<Long> c, int last) {
            assertEquals((last == -1), c.isEmpty());
            assertEquals(last + 1, c.size());
            assertTrue(c.containsAll(c));''',
     1, 969),
    # DIY
    (True, 'DMI_VACUOUS_SELF_COLLECTION_CALL', 'OBlock.java',
     '''@@ -963,6 +967,7 @@   private void verify(ConcatenatedLists<Long> c, int last) {
            assertEquals((last == -1), c.isEmpty());
            assertEquals(last + 1, c.size());
            assertTrue(c.retainAll(c));''',
     1, 969),
    # DIY
    (True, 'DMI_VACUOUS_SELF_COLLECTION_CALL', 'OBlock.java',
     '''@@ -963,6 +967,7 @@    private void verify(ConcatenatedLists<Long> c, int last) {
                 assertEquals((last == -1), c.isEmpty());
                 assertEquals(last + 1, c.size());
                 assertTrue(c.getlist().retainAll(c.getlist()));''',
     1, 969),
    # https://github.com/josephearl/findbugs/blob/fd7ec8b5cc0b1b143589674cdcdb901fa5dc0dda/findbugsTestCases/src/java/gcUnrelatedTypes/Ideas_2011_06_30.java#L13
    (True, 'DMI_COLLECTIONS_SHOULD_NOT_CONTAIN_THEMSELVES', 'OBlock.java',
     '''@@ -963,6 +967,7 @@
                   @ExpectWarning("DMI_COLLECTIONS_SHOULD_NOT_CONTAIN_THEMSELVES")
                    public static void testTP(Collection<Integer> c) {
                        assertTrue(c.contains(c));
                    }''',
     1, 969),
    # DIY
    (True, 'DMI_COLLECTIONS_SHOULD_NOT_CONTAIN_THEMSELVES',
     'Ideas_2011_06_30.java',
     '''@@ -963,6 +967,7 @@
                             @ExpectWarning("DMI_COLLECTIONS_SHOULD_NOT_CONTAIN_THEMSELVES")
                             public static void testTP(Collection<Integer> c) {
                                 return c.remove(c);
                             }
                 ''',
     1, 969),
    # DIY
    (True, 'DMI_COLLECTIONS_SHOULD_NOT_CONTAIN_THEMSELVES',
     'Ideas_2011_06_30.java',
     '''@@ -963,6 +967,7 @@
                            @ExpectWarning("DMI_COLLECTIONS_SHOULD_NOT_CONTAIN_THEMSELVES")
                        public static void testTP(Collection<Integer> c) {
                            return c.getlist().remove(c.getlist());
                        }
            ''',
     1, 969),
    # DIY
    (False, 'DMI_COLLECTIONS_SHOULD_NOT_CONTAIN_THEMSELVES',
     'DIY_01.java', 'obj._portals.removeAll(_portals);', 0, 1),
    (False, 'DMI_VACUOUS_SELF_COLLECTION_CALL',
     'DIY_01.java', 'obj.myList.removeAll(myList);', 0, 1),
    (False, 'DMI_COLLECTIONS_SHOULD_NOT_CONTAIN_THEMSELVES',
     'DIY_01.java', 'obj.myList.remove(myList);', 0, 1),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int,
         line_no: int):
    patch = parse(patch_str, is_patch)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=['SuspiciousCollectionMethodDetector'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0
