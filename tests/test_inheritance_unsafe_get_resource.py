import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

import time


params = [
    # From other repository: https://github.com/jenkinsci/jenkins/pull/575/files/8006b61102a86b3d1600983a09edf31b4f6686f2#diff-cf9443fc2936d5d87f5f013dd6917bc4
    (True, 'UI_INHERITANCE_UNSAFE_GETRESOURCE',
     'XStreamDOMTest.java', '''@@ -58,7 +59,11 @@ public void testMarshal() throws IOException {
        Foo foo = createSomeFoo();
        String xml = xs.toXML(foo);
        System.out.println(xml);
        assertEquals(IOUtils.toString(getClass().getResourceAsStream("XStreamDOMTest.data1.xml")).trim(),xml.trim());
        ''', 1, 62),
    # From other repository: https://github.com/Taskana/taskana/pull/860/files/6544684da30391ceabab9b8b8148f2ef24bfacaf#diff-04a019f76e3d7144121a7ada3ac69e79
    (True, 'UI_INHERITANCE_UNSAFE_GETRESOURCE',
     'DbSchemaCreator.java', '''@@ -44,12 +44,12 @@ public void run() throws SQLException {
          runner.setStopOnError(true);
          runner.setLogWriter(logWriter);
          runner.setErrorLogWriter(errorLogWriter);
          InputStream resourceAsStream = this.getClass().getResourceAsStream(DB_SCHEMA);''', 1, 47),
    # From other repository: https://github.com/shermanfcm/stendhal_2015_Q5/commit/22a81c94654a2f9ece5d0928a0e3764e80dfff2d
    (True, 'UI_INHERITANCE_UNSAFE_GETRESOURCE',
     'ItemListImageViewerEvent.java', '''@@ -154,7 +154,7 @@ private URL getItemImageURL(RPObject item) {
        }
        String itemName = item.get("class") + "/" + itemSubclass;
        String imagePath = "/data/sprites/items/" + itemName + ".png";
        URL url = this.getClass().getResource(imagePath);
        URL url = ItemListImageViewerEvent.class.getResource(imagePath);''', 1, 157)
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, is_patch, file_name)
    context = Context()
    engine = DefaultEngine(context, ['GetResourceDetector'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0


@pytest.mark.skip(reason="Time consuming due to involving network requests")
def test_online_search():
    patch_1 = parse('''File expectedFile = new File(getClass().getResource(name).getFile());''', False)
    patch_1.name = 'animated-gif-lib-for-java/src/main/java/com/madgag/gif/fmsware/NanoHTTPD.java'
    patch_2 = parse('''File expectedFile = new File(getClass().getResource(name).getFile());''', False)
    patch_2.name = 'animated-gif-lib-for-java/src/test/java/com/madgag/gif/fmsware/TestAnimatedGifEncoder.java'
    context = Context()
    context.enable_online_search('NanoHttpd/nanohttpd')

    engine = DefaultEngine(context, included_filter=('GetResourceDetector',))

    start = time.time()
    engine.visit(patch_1, patch_2)
    time_elapsed = time.time() - start
    # print(time_elapsed)
    assert len(engine.filter_bugs('low')) == 1

    start = time.time()
    engine.visit(patch_1, patch_2)
    time_elapsed_2 = time.time() - start
    # print(time_elapsed_2)
    assert time_elapsed > time_elapsed_2 * 10**3  # 9.473357200622559 seconds > 1.1396408081054688-04 seconds
    assert len(engine.filter_bugs('low')) == 1


def test_local_search():
    patch_1 = parse('''File expectedFile = new File(getClass().getResource(name).getFile());''', is_patch=False,
                    name='animated-gif-lib-for-java/src/main/java/com/madgag/gif/fmsware/NanoHTTPD.java')
    patch_2 = parse('''class TMP {
                            String doSomething() {
                                InputStream resourceAsStream = this.getClass().getResourceAsStream(DB_SCHEMA);''',
                    is_patch=False, name='TMP.java')
    patch_3 = parse('''interface Bingo extends OtherClass<String, Integer>, madgag.gif.fmsware.NanoHTTPD, AnotherClass
    {''', is_patch=False, name='Bingo.java')

    context = Context()  # local_search is enabled by default
    engine = DefaultEngine(context, included_filter=('GetResourceDetector',))
    engine.visit(patch_1, patch_2, patch_3)
    assert len(engine.filter_bugs()) == 2
    assert len(engine.filter_bugs('low')) == 2
