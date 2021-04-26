import pytest
from rparser import parse

params = [
    # -------------------------- test support for patch and non-patch --------------------------
    (1, True,
             '''@@ -1 +1,21 @@
             void bug(FI_EXPLICIT_INVOCATION any) throws Throwable {

                 any.finalize();
             }''', 3),
    (2, False,
               '''void bug(FI_EXPLICIT_INVOCATION any) throws Throwable {
                   any.finalize();
               }''', 3),
    # test single-line comments
    (3, False,
       '''void bug(FI_EXPLICIT_INVOCATION any) throws Throwable {
           any.finalize(); // this is a single statement
       }''', 3),
    (4, False,
       '''void bug(FI_EXPLICIT_INVOCATION any) throws Throwable {
           // this is a single statement
           any.finalize();
           // this is a single statement
       }''', 3),
    (5, True,
       '''@@ -1,0 +1,0 @@
       void bug(FI_EXPLICIT_INVOCATION any) throws Throwable {
-    // this is a single statement
+    any.finalize();
+    // this is a single statement
}''', 3),
    # -------------------------- test multi-line comments --------------------------
    (6, False,
         '''@Override
        public void onReceive(final Context context, Intent intent) {
           /*  dbhelper = new DatabaseHandler(context, "RG", null, 1);
            mURL = dbhelper.Obt_url();
            if (mURL == ""){
                mURL = "http://186.96.89.66:9090/crccoding/f?p=2560:9999";
                Log.i("SQLL","Url vacio");
            }else{
                Log.i("SQLL","Url cargado   "+mURL);
            }*/
            WebView gv = new WebView(context);''', 3),
    (7, True,
     '''@@ -1,0 +1,0 @@ @Override
    public void onReceive(final Context context, Intent intent) {
       /*  This is a multi-line comments
-       1st line
+       this is the first line
        This is the second line
-       This is the third line
        This is the final line
      */
      return false;''', 2),
    (8, True,
     '''@@ -2,0 +2,0 @@ @Override
    public void onReceive(final Context context, Intent intent) {
-       /*
        dbhelper = new DatabaseHandler(context, "RG", null, 1);
        mURL = dbhelper.Obt_url();
        if (mURL == ""){
            mURL = "http://186.96.89.66:9090/crccoding/f?p=2560:9999";
            Log.i("SQLL","Url vacio");
        }else{
            Log.i("SQLL","Url cargado   "+mURL);
        }
-        */
        WebView gv = new WebView(context);''', 10),

    # -------------------------- test multi-line comments witout '*/' --------------------------
    (9, True, '''@@ -1,0 +1,0 @@
     /*  dbhelper = new DatabaseHandler(context, "RG", null, 1);
        mURL = dbhelper.Obt_url();
        if (mURL == ""){
            mURL = "http://186.96.89.66:9090/crccoding/f?p=2560:9999";
+            Log.i("SQLL","Url vacio");
        }else{
        ''', 0),
    (10, True, '''@@ -1,0 +1,0 @@
-    /*  dbhelper = new DatabaseHandler(context, "RG", null, 1);
        mURL = dbhelper.Obt_url();
        if (mURL == ""){
            mURL = "http://186.96.89.66:9090/crccoding/f?p=2560:9999";
+            Log.i("SQLL","Url vacio");
        }else{
        ''', 5),

    # -------------------------- test multi-line comments without '/*' --------------------------
    (11, True, '''@@ -1,0 +1,0 @@ /*  dbhelper = new DatabaseHandler(context, "RG", null, 1);
            mURL = dbhelper.Obt_url();
            if (mURL == ""){
                mURL = "http://186.96.89.66:9090/crccoding/f?p=2560:9999";
                Log.i("SQLL","Url vacio");
            }else{
-                Log.i("SQLL","Url cargado   "+mURL);
+                Log.i("SQLL","Url cargado   "+mURL);} */
-            }*/
            WebView gv = new WebView(context);''', 1),
    (12, True, '''@@ -1,0 +1,0 @@ /*  dbhelper = new DatabaseHandler(context, "RG", null, 1);
            mURL = dbhelper.Obt_url();
            if (mURL == ""){
                mURL = "http://186.96.89.66:9090/crccoding/f?p=2560:9999";
-               Log.i("SQLL","Url vacio");
+               Log.i("SQLL","Url vacio   "+mURL);
            }else{
                 Log.i("SQLL","Url cargado   "+mURL);
-           } */
+           }
            WebView gv = new WebView(context);''', 8),
    (13, True, '''@@ -1,0 +1,0 @@ /*  dbhelper = new DatabaseHandler(context, "RG", null, 1);
            mURL = dbhelper.Obt_url();
            if (mURL == ""){
                mURL = "http://186.96.89.66:9090/crccoding/f?p=2560:9999";
-               Log.i("SQLL","Url vacio");
+               Log.i("SQLL","Url vacio   "+mURL);
            }else{
                 Log.i("SQLL","Url cargado   "+mURL);
            }
           */

            WebView gv = new WebView(context);''', 1),
    # switch case
    (14, False, '''switch (c) {
        case 'a':
        case 'A':
            if (csName == "ASCII" || equalEncodings(csName, "ASCII")) {
                return CS_US_ASCII;
            }
            break;

        case 'c':''', 8),
]


@pytest.mark.parametrize('test_id,is_patch,patch_str,expected_length', params)
def test_statement_length(test_id: int, is_patch:bool, patch_str: str, expected_length: int):
    patch = parse(patch_str, is_patch)
    assert len(patch.hunks[0].lines) == expected_length


def test_multi_hunks():
    patch = parse('''@@ -21,6 +21,7 @@
 import io.github.mzmine.datamodel.Frame;
 import io.github.mzmine.datamodel.featuredata.impl.SimpleIonMobilitySeries;
 import io.github.mzmine.datamodel.featuredata.impl.SummedIntensityMobilitySeries;
+import io.github.mzmine.util.MemoryMapStorage;
 import java.util.List;
 
 /**
@@ -43,4 +44,44 @@ default SimpleIonMobilitySeries getMobilogram(int index) {
   }
 
   SummedIntensityMobilitySeries getSummedMobilogram();
+
+  /**
+   * Creates a copy of this series using the same frame list, but with new mz/intensities and new
+   * mobilograms, e.g. after smoothing.
+   *
+   * @param storage
+   * @param newMzValues
+   * @param newIntensityValues
+   * @param newMobilograms
+   * @return
+   */
+  IonMobilogramTimeSeries copyAndReplace(MemoryMapStorage storage, double[] newMzValues,
+      double[] newIntensityValues, List<SimpleIonMobilitySeries> newMobilograms);
+
+  /**
+   * @param scan
+   * @return The intensity value for the given scan or 0 if the no intensity was measured at that
+   * scan.
+   */
+  @Override
+  default double getIntensityForSpectrum(Frame scan) {
+    int index = getSpectra().indexOf(scan);
+    if (index != -1) {
+      return getIntensity(index);
+    }
+    return 0;
+  }
+
+  /**
+   * @param scan
+   * @return The mz for the given scan or 0 if no intensity was measured at that scan.
+   */
+  @Override
+  default double getMzForSpectrum(Frame scan) {
+    int index = getSpectra().indexOf(scan);
+    if (index != -1) {
+      return getMZ(index);
+    }
+    return 0;
+  }
 }''')
    assert len(patch.hunks[0].lines) == 5
    assert len(patch.hunks[1].lines) == 20


def test_2():
    patch = parse('''@@ -44,39 +48,53 @@ public static OtpProjectInfo projectInfo() {
     OtpProjectInfo() {
         this(
             "0.0.0-ParseFailure",
-            new VersionControlInfo(
-                UNKNOWN,
-                UNKNOWN,
-                UNKNOWN,
-                UNKNOWN,
-                true
-            )
+            new GraphFileHeader(),
+            new VersionControlInfo()
         );
     }
     
     public OtpProjectInfo(
             String version,
+            GraphFileHeader graphFileHeaderInfo,
             VersionControlInfo versionControl
     ) {
         this.version = MavenProjectVersion.parse(version);
+        this.graphFileHeaderInfo = graphFileHeaderInfo;
         this.versionControl = versionControl;
     }
 
     public long getUID() {
         return hashCode();
     }
 
+    /**
+     * Return {@code true} if the graph file and the running instance of OTP is the
+     * same instance. If the running instance of OTP or the Graph.obj serialization id
+     * is unknown, then {@code true} is returned.
+     */
+    public boolean matchesRunningOTPInstance(GraphFileHeader graphFileHeader) {
+        if(graphFileHeader.isUnknown()) { return true; }
+        if(this.graphFileHeaderInfo.isUnknown()) { return true; }
+        return this.graphFileHeaderInfo.equals(graphFileHeader);
+    }
+
     public String toString() {
         return "OTP " + getVersionString();
     }
 
     /**
      * Return a version string:
-     * {@code version: 2.1.0, commit: 2121212.., branch: dev-2.x}
+     * {@code version: 2.1.0, graph-id: 00001, commit: 2121212.., branch: dev-2.x}
      */
     public String getVersionString() {
-        String format = "version: %s, commit: %s, branch: %s";
-        return String.format(format, version.version, versionControl.commit, versionControl.branch);
+        String format = "version: %s, graph-id: %s, commit: %s, branch: %s";
+        return String.format(
+            format,
+            version.version,
+            getExpectedGraphVersion(),
+            versionControl.commit,
+            versionControl.branch
+        );
     }
 
     /**
@@ -86,4 +104,10 @@ public String getVersionString() {
     public boolean sameVersion(OtpProjectInfo other) {
         return this.version.sameVersion(other.version);
     }
+
+    public String getExpectedGraphVersion() {
+        return graphFileHeaderInfo.isUnknown()
+            ? UNKNOWN
+            : graphFileHeaderInfo.serializationId();
+    }
 }''')
    assert len(patch.hunks[0].lines) == 27
    assert len(patch.hunks[1].lines) == 7


def test_03():
    patch = parse('''@@ -31,6 +31,16 @@ private Config(){}
     private static boolean manga;
     /** 送出即将过期礼物给此 up 的直播间 */
     private static String upLive;
+    /** 对于进行投币的视频选择是否点赞 */
-    /** test */
+    private static String selectLike;
+
+    public String getSelectLike() {
+        return selectLike;
+    }
+
+    public void setSelectLike(String selectLike) {
+        Config.selectLike = selectLike;
+    }
 
     public String getUpLive() {
         return upLive;''')
    assert len(patch.hunks[0].lines) == 11


def test_04():
    patch = parse('''@@ -86,4 +104,10 @@
        /** Total time it took to process all {@link #mProcessedFiles}. */
 		public long mProcessingTimeNanoseconds = 0;
 
-		/**
-		 * Gets the average time it took for processing a file, in seconds. This is rather crude as
-		 * it includes all of those:<br>
+		/** Gets the average time it took for processing a file, in seconds. This includes only the
+		 *  most significant computations:
+		 *  - The time to parse the XML.
 		 * ATTENTION: Not synchronized - only use this if you are sure that the Statistics object is
 		 * not being modified anymore. This is the case if you obtained it using
 		 * {@link IdentityFileProcessor#getStatistics()}. */
 		public double getAverageXMLImportTime() {
 			if (mProcessedFiles == 0) // prevent division by 0
 				return 0;
-
-			return ((double) mProcessingTimeNanoseconds / (1000 * 1000 * 1000))
+			
+			return ((double) mProcessingTimeNanoseconds / (double) SECONDS.toNanos(1))
 				/ (double) mProcessedFiles;
 		}''')
    assert len(patch.hunks[0].lines) == 6


def test_05():
    patch = parse('''@@ -86,4 +104,10 @@
    public final DContactGeom geom = new DContactGeom();
    public final DVector3 fdir1 = new DVector3();
 
-   DContact() {
+   public DContact() {
        // Nothing
    }
-   
+
    public static class DSurfaceParameters {
        /* must always be defined */
        public int mode;''', False)
    assert len(patch.hunks[0].lines) == 7


def test_06():
    patch = parse('''@@ -86,4 +104,10 @@
  * Represents the task of loading a Firestore bundle. It provides progress of bundle loading, as
  * well as task completion and error events.
  */
-/* package */ class LoadBundleTask extends Task<LoadBundleTaskProgress> {
+public class LoadBundleTask extends Task<LoadBundleTaskProgress> {
   private final Object lock = new Object();
 
   /** The last progress update, or {@code null} if not yet available. */''')
    assert len(patch.hunks[0].lines) == 3


def test_07():
    patch = parse('''@@ -86,4 +104,10 @@
   public void loadBundle(BundleReader bundleReader, LoadBundleTask resultTask) {
+    try {
+      BundleMetadata bundleMetadata = bundleReader.getBundleMetadata();
+      boolean hasNewerBundle = localStore.hasNewerBundle(bundleMetadata);
+      if (hasNewerBundle) {
+        resultTask.setResult(
+            new LoadBundleTaskProgress(
+                bundleMetadata.getTotalBytes(),
+                /* exception= */ null,
+                LoadBundleTaskProgress.TaskState.SUCCESS));
+      }
+      ImmutableSortedMap<DocumentKey, MaybeDocument> changes = bundleLoader.applyChanges();
+
+      // TODO(b/160876443): This currently raises snapshots with `fromCache=false` if users already
+      // listen to some queries and bundles has newer version.
+      emitNewSnapsAndNotifyLocalStore(changes, /* remoteEvent= */ null);
    /** Resolves the task corresponding to this write result. */
   private void notifyUser(int batchId, @Nullable Status status) {
     Map<Integer, TaskCompletionSource<Void>> userTasks = mutationUserCallbacks.get(currentUser);''')
    assert len(patch.hunks[0].lines) == 11


def test_08():
    patch = parse('''long handleException(long i, long cumulativeInterval) {
        return  i - i % cumulativeInterval + Math.min(/* obj1 =
        hhh*/ i, cumulativeInterval);
    }''', False)
    assert len(patch.hunks[0].lines) == 3


def test_09():
    patch = parse('''@@ -198,9 +203,10 @@ public PerformancePublisher(String sourceDataFiles,
                                 boolean failBuildIfNoResultFile,
                                 boolean compareBuildPrevious,
                                 boolean modeThroughput,
+                                boolean showTrendGraphs,
                                 /**
-                                 * Deprecated. Now use for support previous pipeline jobs.
-                                 */
+                                     * Deprecated. Now use for support previous pipeline jobs.
+                                     */
                                 List<PerformanceReportParser> parsers) {
         this.parsers = parsers;
         this.sourceDataFiles = sourceDataFiles;
''')

    assert len(patch.hunks[0].lines) == 5


# oshi/oshi/pulls/1526
def test_10():
    patch = parse('''@@ -174,8 +312,40 @@
      *         or processes with a state of {@link OSProcess.State#INVALID} if a
      *         process terminates during iteration.
+     * @deprecated Use {@link #getChildProcesses(int, Predicate, Comparator, int)}
+     *             with sorting constants from {@link ProcessSorting}.
+     */
+    @Deprecated
+    default List<OSProcess> getChildProcesses(int parentPid, int limit, ProcessSort sort) {
+        return getChildProcesses(parentPid, null, ProcessSorting.convertSortToComparator(sort), limit);
+    }
+
+    /**
+     * Gets currently running child processes of provided parent PID, optionally
+     * filtering, sorting, and limited to the top "N".
+     * @param limit
+     *            Max number of results to return, or 0 to return all results
+     * @return A list of {@link oshi.software.os.OSProcess} objects representing the
+     *         currently running child processes of the provided PID, optionally
+     *         filtered, sorted, and limited to the specified number.
      */
-    List<OSProcess> getChildProcesses(int parentPid, int limit, ProcessSort sort);
+    List<OSProcess> getChildProcesses(int parentPid, Predicate<OSProcess> filter, Comparator<OSProcess> sort,
+            int limit);
 
     /**
      * Gets the current process ID
''')
    assert len(patch.hunks[0].lines) == 6


# https://api.github.com/repos/checkstyle/checkstyle/pulls/9246/files
def test_11():
    patch = parse('''@@ -89,53 +89,112 @@
  * <pre>
  * &lt;module name=&quot;RequireThis&quot;/&gt;
  * </pre>
+ * <p>Example:</p>
+ * <pre>
+ * public class Test {
+ *   private int a;
+ *   private int b;
+ *
+ *   public Test(int a) {
+ *     // overlapping by constructor argument
+ *     this.a = a;       // OK, this keyword used
+ *     b = 0;            // OK, no overlap
+ *     foo(5);           // OK
+ *   }
+ * }
+ * </pre>
  * <p>
- * To configure to check the {@code this} qualifier for fields only:
+ * To configure the check for fields only:
  * </p>''')
    assert len(patch.hunks[0].lines) == 0


# src/main/java/fr/alasdiablo/janoeo/world/gen/feature/OresFeatures.java
def test_12():
    patch = parse('''@@ -231,7 +234,7 @@ public static void initDenseOre() {
                     FREQUENCY_CONFIG.DENSE_COPPER_ORE_COUNT.get(),
                     FREQUENCY_CONFIG.DENSE_COPPER_ORE_BOTTOM.get(),
                     FREQUENCY_CONFIG.DENSE_COPPER_ORE_TOP.get()
-            );
+            );*/
     }
 
     /**
''')
    assert len(patch.hunks[0].lines) == 2


# sistemafinanciero/src/main/java/ec/ups/edu/sistemafinanciero/dao/TransaccionDAO.java
def test_13():
    patch = parse('''@@ -40,7 +42,9 @@ public boolean insert(Transaccion transaccion) throws SQLException {
     	.setParameter(10, transaccion.getSladoActual())
 		.setParameter(11, transaccion.getCajero().getId())
 		.setParameter(12, transaccion.getCliente().getIdClienteLong())
-		.executeUpdate();
+		.executeUpdate();*/
+		em.persist(transaccion);
+		em.flush();
 		return true;
 	}
 	/**
''')
    assert len(patch.hunks[0].lines) == 5


def test_file_01():
    p = 'tests/data/Md4.java'
    with open(p, 'r') as f:
        patch = parse(f.read(), is_patch=False, name=p)
        assert len(patch.hunks[0].lines) == 152


def test_file_02():
    p = 'tests/data/DotPlotPanel.java'
    with open(p, 'r') as f:
        patch = parse(f.read(), is_patch=False, name=p)
        assert len(patch.hunks[0].lines) == 101
