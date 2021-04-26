from patterns.models.context import Context
from rparser import parse
from patterns.models.engine import DefaultEngine

import pytest

params = [
    # ============== RV_01_TO_INT ==============
    # DIY
    (True, 'RV_01_TO_INT', 'Fake.java',
     '''@@ -0,0 +1,2 @@
        Random rand = new Random();
        System.out.println(
            (int) rand.nextFloat());
        System.out.println((int) rand.nextDouble());''', 2, 3),
    (True, 'RV_01_TO_INT', 'Fake.java',
     '''@@ -3,1 +5,1 @@
     System.out.println((int) Math.random());''', 1, 5),
    (True, 'RV_01_TO_INT', 'Fake.java',
     '''@@ -0,0 +1,2 @@
     Scanner scanner = new Scannner(System.in);
     int a = (int)scanner.nextFloat();''', 0, 0),

    # ============== DM_RUN_FINALIZERS_ON_EXIT ==============
    # From other repository
    (True, 'DM_RUN_FINALIZERS_ON_EXIT', 'StdEntropyDecoder.java',
     "@@ -622,7 +622,7 @@ public StdEntropyDecoder(CodedCBlkDataSrcDec src, DecoderSpecs decSpec,\n"
     "         if (DO_TIMING) {\n"
     "             time = new long[src.getNumComps()];\n"
     "             // If we are timing make sure that 'finalize' gets called.\n"
     "+            System.runFinalizersOnExit(true);\n"
     "         }\n \n"
     "         // Initialize internal variables", 1, 625),
    # ============== DMI_RANDOM_USED_ONLY_ONCE ==============
    # From other repository: https://github.com/jenkinsci/android-emulator-plugin/commit/0e104f3f0fc18505c13932fccd3b2297e78db694#diff-238b9af87181bb379670392cdb1dcd6bL173
    (True, 'DMI_RANDOM_USED_ONLY_ONCE', 'MonkeyBuilder.java',
     "@@ -166,11 +167,10 @@ private static void addArguments(String parameters, String flag, StringBuilder a\n"
     "        }\n"
     "    }\n\n"
     "-    @SuppressFBWarnings(\"DMI_RANDOM_USED_ONLY_ONCE\")\n"
     "    private static long parseSeed(String seed) {\n"
     "        long seedValue;\n"
     "        if (\"random\".equals(seed)) {\n"
     "            seedValue = new Random().nextLong();\n"
     "        } else if (\"timestamp\".equals(seed)) {\n", 1, 173),
    # From other repository: https://github.com/adaptris/interlok/commit/8dd32e9b89a4b17662faa7ca986756f3cc348cc7#diff-1e0469ce35c1d148418525088df452a2L405
    (True, 'DMI_RANDOM_USED_ONLY_ONCE', 'MonkeyBuilder.java',
     '''@@ -393,15 +396,13 @@ protected synchronized void sendMessageLifecycleEvent(AdaptrisMessage msg) {
        private GenericObjectPool<Worker> createObjectPool() {
        GenericObjectPool<Worker> pool = new GenericObjectPool<>(new WorkerFactory());
        pool.setMaxTotal(poolSize());
        pool.setMinIdle(minIdle());
        pool.setMaxIdle(maxIdle());
        pool.setMaxWaitMillis(-1L);
        pool.setBlockWhenExhausted(true);
+       pool.setMinEvictableIdleTimeMillis(threadLifetimeMs());
+       pool.setTimeBetweenEvictionRunsMillis(threadLifetimeMs() + 
+                                               new Random(threadLifetimeMs()).nextLong());
+    return pool;''', 1, 405),
    # From other repository: https://github.com/adaptris/interlok/commit/8dd32e9b89a4b17662faa7ca986756f3cc348cc7#diff-766b5e25592ad321e107f1f856d8a08bL102
    (True, 'DMI_RANDOM_USED_ONLY_ONCE', 'MonkeyBuilder.java',
     '''@@ -99,7 +98,8 @@ private Service cloneService(Service original) throws Exception {
         pool.setMaxWait(-1L);
         pool.setWhenExhaustedAction(org.apache.commons.pool.impl.GenericObjectPool.WHEN_EXHAUSTED_BLOCK);
         pool.setMinEvictableIdleTimeMillis(EVICT_RUN);
         pool.setTimeBetweenEvictionRunsMillis(EVICT_RUN + new Random(EVICT_RUN).nextLong());''', 1, 101),
    # DIY
    (True, 'DMI_RANDOM_USED_ONLY_ONCE', 'Fake.java',
     "@@ -166,11 +167,10 @@ private static void addArguments(String parameters, String flag, StringBuilder a\n"
     "        }\n"
     "    }\n\n"
     "-    @SuppressFBWarnings(\"DMI_RANDOM_USED_ONLY_ONCE\")\n"
     "    private static long parseSeed(String seed) {\n"
     "        long seedValue;\n"
     "        if (\"random\".equals(seed)) {\n"
     "            seedValue = new java.util.Random().nextLong();\n"
     "        } else if (\"timestamp\".equals(seed)) {\n", 1, 173),
    (False, 'DMI_RANDOM_USED_ONLY_ONCE', 'Benchmark/BenchmarkTest02415.java',
     'new java.util.Random().nextBytes(bytes);', 1, 1),

    # ============== DM_STRING_VOID_CTOR ==============
    # From other repository: https://github.com/universAAL/middleware/commit/daf0a4ca23297f08713e722d5f2fd891699aa95f
    (True, 'DM_STRING_VOID_CTOR', 'SimpleProperties.java',
     '''@@ -1153,7 +1153,7 @@ public String toStringRecursive(String prefix, boolean prefixAtStart,
     if (visitedElements == null)
         visitedElements = new Hashtable();

     String s = new String();
     if (prefixAtStart)
         s += prefix;
     s += this.getClass().getName() + "\n";''', 1, 1156),
    # DIY
    (True, 'DM_STRING_VOID_CTOR', 'Fake.java',
     '''@@ -1153,7 +1153,7 @@ public String toStringRecursive(String prefix, boolean prefixAtStart,
                 String s = new String(  );''', 1, 1153),

    # ============== DM_STRING_CTOR ==============
    # From other repository: https://github.com/test-pki/dogtag-pki/commit/a4db0f39e257950a5c89203452c1184c7080e5bd#diff-a73d367ef2afa1ab0151ca0df88ac96d
    (True, 'DM_STRING_CTOR', 'SimpleProperties.java',
     "@@ -191,6 +191,7 @@ public synchronized void load(InputStream inStream) throws IOException {  \n"
     "   if (whiteSpaceChars.indexOf(nextLine.charAt(startIndex)) == -1)\n"
     " break;\n"
     "   nextLine = nextLine.substring(startIndex, nextLine.length());\n"
     "+     line = new String(loppedLine + nextLine);\n"
     "   }\n"
     " // Find start of key\n"
     " int len = line.length();", 0, 194),
    # From other repository: https://github.com/HighTechRedneck42/JMRI/commit/e0f5ae298a1bad0b7abca627d7ab15e2b6d2fd69
    (True, 'DM_STRING_CTOR', 'DCCppSimulatorAdapter.java',
     '''@@ -467,7 +467,7 @@ private void generateRandomSensorReply() {
     Random valueGenerator = new Random();
     int value = valueGenerator.nextInt(2); // Generate state value betweeon 0 and 1

     String reply = new String((value == 1 ? "Q " : "q ")+ Integer.toString(sensorNum));''', 0, 470),
    # From other repository: https://github.com/exedio/persistence/commit/cb142171ce28704f463dfb2b95307ac203d3fd39
    (True, 'DM_STRING_CTOR', 'ReserializeTest.java',
     '''@@ -23,10 +23,12 @@
     import static org.junit.Assert.assertNotSame;
     import static org.junit.Assert.assertSame;

     import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
     import org.junit.Test;

     public class ReserializeTest
     {
         @SuppressFBWarnings("DM_STRING_CTOR")
         @Test public void testIt()
         {
             final String[] original = new String[]{
                                            new String("hallo"), new String("hallo")};''', 1, 35),
    # From other repository: https://github.com/nus-cs2103-AY1920S1/duke/pull/307/files?file-filters%5B%5D=.java
    (True, 'DM_STRING_CTOR', 'ReserializeTest.java',
     '''@@ -23,10 +23,12 @@
     import static org.junit.Assert.assertNotSame;
     import static org.junit.Assert.assertSame;

     import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
     import org.junit.Test;

     public class ReserializeTest
     {
         @SuppressFBWarnings("DM_STRING_CTOR")
         @Test public void testIt()
         {
            String content = new String(Files.readAllBytes(Paths.get(filePath)), "UTF-8");''', 0, 34),
    # https://github.com/code-differently/Assessment-PAIN/pull/15/files#diff-478b2349e8da512b9f501d8ece255e9445998876e9bac0eeb9fd8e5f69af77c2R11
    (True, 'DM_STRING_CTOR', 'ReserializeTest.java',
     '''@@ -23,10 +23,12 @@
     import static org.junit.Assert.assertNotSame;
     import static org.junit.Assert.assertSame;

     import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
     import org.junit.Test;

     public class ReserializeTest
     {
         @SuppressFBWarnings("DM_STRING_CTOR")
         @Test public void testIt()
         {
            data = new String(Files.readAllBytes(Paths.get("RawData.txt")));''', 0, 34),

    # ============== DM_INVALID_MIN_MAX ==============
    # From spotbugs https://github.com/spotbugs/spotbugs/blob/a6f9acb2932b54f5b70ea8bc206afb552321a222/spotbugsTestCases/src/java/sfBugsNew/Feature329.java
    (False, 'DM_INVALID_MIN_MAX', 'Feature329.java',
     '''public int checkBounds(int rawInput) {
        return Math.min(0, Math.max(100, rawInput));
    }''', 1, 2),
    (False, 'DM_INVALID_MIN_MAX', 'Feature329.java',
     '''        return Math.min(0, Math.max(rawInput, 100));''', 1, 1),
    (False, 'DM_INVALID_MIN_MAX', 'Feature329.java',
     '''        return Math.min(Math.max(rawInput, 100), 0);''', 1, 1),
    (False, 'DM_INVALID_MIN_MAX', 'Feature329.java',
     '''        return Math.min(Math.max(100, rawInput), 0);''', 1, 1),
    (False, 'DM_INVALID_MIN_MAX', 'Feature329.java',
     '''        return Math.max(Math.min(0, rawInput), 100);''', 1, 1),
    (False, 'DM_INVALID_MIN_MAX', 'Feature329.java',
     '''    public int getScore(int totalCount, int failCount, double scaleFactor) {
                // Based on https://github.com/marksinclair/junit-plugin/commit/c0dc11e08923edd23cee90962da638e4a7eb47d5
                int score = (totalCount == 0) ? 100 : (int) (
                        100.0 * Math.max(1.0, Math.min(0.0, 1.0 - (scaleFactor * failCount) / totalCount)));
                return score;
    }''', 1, 4),
    (False, 'DM_INVALID_MIN_MAX', 'Feature329.java',
     '''        return Math.max(Math.min(0.1, rawInput), 100);''', 1, 1),
    (False, 'DM_INVALID_MIN_MAX', 'Feature329.java',
     '''        return Math.min(100, Math.max(0, rawInput));''', 0, 1),
    (False, 'DM_INVALID_MIN_MAX', 'Feature329.java',
     '''        return Math.max(0, Math.min(100, rawInput));''', 0, 1),
    (False, 'DM_INVALID_MIN_MAX', 'jmh/LinuxPerfNormProfiler.java',
     'multiplier = Math.max(1D, Math.min(0D, multiplier));', 1, 1),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, is_patch)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=('FinalizerOnExitDetector', 'RandomOnceDetector', 'RandomD2IDetector',
                                            'StringCtorDetector', 'InvalidMinMaxDetector'))
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0
