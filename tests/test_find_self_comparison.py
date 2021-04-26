import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

params = [
    # https://github.com/mhagnumdw/bean-info-generator/pull/5/files#diff-71bf0b35fa483782180f548a1a7d6cc4b3822ed12aa4bb86640f80dde9df3077R13
    (False, 'SA_SELF_COMPUTATION', 'Ideas_2013_11_06.java ',
     '''@NoWarning("SA_FIELD_SELF_COMPUTATION")
        public int testUpdate() {
            return flags ^(short) flags;
        }''', 0, 0),
    # https://github.com/spotbugs/spotbugs/blob/3883a7b750fb339577be073bc45e36b6f268777b/spotbugsTestCases/src/java/SelfFieldOperation.java#L25
    (False, 'SA_SELF_COMPUTATION', 'SelfFieldOperation_01.java',
     '''@ExpectWarning("SA_FIELD_SELF_COMPARISON,SA_FIELD_SELF_COMPUTATION")
        int f() {
            if (x < x)
                x = (int) ( y ^ y);
            if (x != x)
                y = x | x;
            if (x >= x)
                x = (int)(y & y);
            if (y > y)
                y = x - x;
            return x;
        }''', 8, 4),
    # DIY
    (False, 'SA_SELF_COMPUTATION', 'DIY_01.java',
     '''return capabilities.level - level;''', 0, 0),
    (False, 'SA_SELF_COMPUTATION', 'DIY_02.java',
     '    $(".lolkek").shouldNotBe(and("visible&visible", visible, visible));    // visible&visible', 0, 0),
    (False, 'SA_SELF_COMPUTATION', 'DIY_03.java',
     'final AtomicReference<String> latest = new AtomicReference<>("2015-01-01-00-00-00");', 0, 0),
    (False, 'SA_SELF_COMPUTATION', 'DIY_04.java',
     'long expectUnacked = msgOutCounter - (i - i % cumulativeInterval);', 0, 0),
    (False, 'SA_SELF_COMPUTATION', 'DIY_05.java',
     ' return i | i & j;', 0, 0),
    # https://github.com/Vardan2020/VardanHomeWork/pull/20/files
    (False, 'SA_SELF_COMPUTATION', 'VardanHomeWork.java',
     'if (a > b & b>c) {', 0, 0),
    # https://github.com/oracle/graal/pull/3183/files
    (False, 'SA_SELF_COMPUTATION', 'graal.java',
     'int imm5Encoding = (index << eSize.bytes() | eSize.bytes()) << ASIMDImm5Offset;', 0, 0),
    (False, 'SA_SELF_COMPUTATION', 'DIY_06.java',
     'immTwice = immTwice | immTwice << 32;', 0, 0),
    (False, 'SA_SELF_COMPUTATION', 'DIY_07.java',
     'return i | j & j;', 0, 0),
    (False, 'SA_SELF_COMPUTATION', 'DIY_08.java',
     'return i | j & j | z;', 0, 0),
    (False, 'SA_SELF_COMPUTATION', 'DIY_09.java',
     'double second = requestMetrics.endDate.getTime() - requestMetrics.endDate.getTime();', 1, 1),
    (False, 'SA_SELF_COMPUTATION', 'DIY_10.java',
     'player.world.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ENTITY_ITEM_PICKUP, SoundCategory.PLAYERS, 0.2F, ((player.getRandom().nextFloat() - player.getRandom().nextFloat()) * 0.7F + 1.0F) * 2.0F);', 0, 0),
    # ---------------- SA_SELF_COMPARISON ----------------------
    (False, 'SA_SELF_COMPARISON', 'SelfFieldOperation_02.java',
     '''@NoWarning("SA_FIELD_SELF_COMPARISON")
        public boolean test() {
            boolean result = false;
            result |= flags == (short) flags;
            result |= flags == (char) flags;
            result |= flags == (byte) flags;
            return result;
        }''', 0, 3),
    (False, 'SA_SELF_COMPARISON', 'SelfFieldOperation_03.java',
     '''@ExpectWarning("SA_FIELD_SELF_COMPARISON")
        public boolean testTP() {
            boolean result = false;
            result |= flags == flags;
            return result;
        }''', 1, 4),
    (False, 'SA_SELF_COMPARISON', 'SelfFieldOperation_04.java',
     '''@ExpectWarning(value="SA_FIELD_SELF_COMPARISON", confidence = Confidence.LOW)
    boolean volatileFalsePositive() {
        return z == z;
    }''', 1, 3),
    (False, 'SA_SELF_COMPARISON', 'SelfFieldOperation_05.java',
     '''@ExpectWarning("SA_FIELD_SELF_COMPARISON")
        boolean e() {
            return a.equals(a);
        }''', 1, 3),
    (False, 'SA_SELF_COMPARISON', 'SelfFieldOperation_06.java',
     '''@ExpectWarning("SA_FIELD_SELF_COMPARISON")
        int c() {
            return a.compareTo(a);
        }
    ''', 1, 3),
    (False, 'SA_SELF_COMPARISON', 'SelfFieldOperation_07.java',
     ''' Objects.equals(requestCount, throttlingPolicy.requestCount) &&
         Objects.equals(unitTime, throttlingPolicy.unitTime) &&
         Objects.equals(timeUnit, throttlingPolicy.timeUnit) &&
         Objects.equals(tierPlan, throttlingPolicy.tierPlan) &&
         Objects.equals(stopOnQuotaReach, throttlingPolicy.stopOnQuotaReach) &&
         Objects.equals(monetizationProperties, throttlingPolicy.monetizationProperties);''', 0, 0),
    #  https://github.com/google/ExoPlayer/pull/8462
    (False, 'SA_SELF_COMPARISON', 'Fake_01.java',
    'if (capabilities.profile == profile && capabilities.level >= level) { ', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_02.java', 'private <T> T triggerBeforeConvert(T aggregateRoot) {', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_03.java',
     'public <C, R> R accept(AnalyzedStatementVisitor<C, R> analyzedStatementVisitor, C context) {', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_04.java',
     'public <T> T unwrap(String wrappingToken, Class<T> resultClass) {', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_05.java',
     'private <T> T exec(HttpRequest<Buffer> request, Object body, Class<T> resultClass, int expectedCode) {', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_06.java',
     'ArrayList<ArrayList<RecyclerView.ViewHolder>> mAdditionsList = new ArrayList<>();', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_07.java',
     '''private static final List<String> STEP_NAMES = Arrays.asList("Given a \\"stock\\" of symbol <symbol> and a threshold <threshold>",
                        "When the stock is traded at price <price>",
                        "Then the alert status should be status <status>"
        );''', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_08.java',
     'private static final List<String> STEP_NAMES = Arrays.asList("Given a stock of symbol <symbol> and a threshold <threshold>', 0, 0),
    # https://github.com/PowerOlive/Mysplash/pull/1/files
    (False, 'SA_SELF_COMPARISON', 'Mysplash.java',
     'return newModel instanceof AppObject && ((AppObject) newModel).iconId == iconId;', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_09.java',
     'if (disjunction.get(t).variable == variable)', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_10.java',
     'if (this.matriz[fila][col].valor == valor){', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_11.java',
     "if (email.length()-email.indexOf('.')-1 <= 1){", 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_12.java',
     "if (c >= c*b){", 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_13.java',
     'await().atMost(atMost, TimeUnit.SECONDS).until(() -> tmpDir.toFile().listFiles().length == length);', 0, 0),
    # https://github.com/DurankGts/CodenameOne/pull/40/files
    (False, 'SA_SELF_COMPARISON', 'CodenameOne.java',
     'mergeMode = inputPath.contains(",") || mergedFile != null;', 0, 0),
    # https://github.com/sunjincheng121/incubator-iotdb/blob/9d40954fdcbe67bf20fed063208b31b23d5650dd/cli/src/main/java/org/apache/iotdb/tool/ExportCsv.java#L343
    (False, 'SA_SELF_COMPARISON', 'incubator_iotdb.java',
     '} else if (value.contains(",")) {', 0, 0),
    # https://github.com/biojava/biojava/blob/master/biojava-ontology/src/main/java/org/biojava/nbio/ontology/utils/AbstractAnnotation.java#L236
    (False, 'SA_SELF_COMPARISON', 'biojava/AbstractAnnotation.java',
     'return ((Annotation) o).asMap().equals(asMap());', 0, 0),
    # https://github.com/micromata/projectforge/blob/develop/projectforge-wicket/src/main/java/org/projectforge/web/task/TaskTreeProvider.java#L198
    (False, 'SA_SELF_COMPARISON', 'biojava/AbstractAnnotation.java',
     'return ((TaskNodeModel) obj).id.equals(id);', 0, 0),
    (False, 'SA_SELF_COMPARISON', 'Fake_14.java',
     '"abc".equals("abc");', 1, 1),
    (False, 'SA_SELF_COMPARISON', 'asmsupport/ClassReader.java',
     'if (attrs[i].type.equals(type)) {}', 0, 0),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, is_patch)
    engine = DefaultEngine(Context(), included_filter=['CheckForSelfComputation', 'CheckForSelfComparison'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0
