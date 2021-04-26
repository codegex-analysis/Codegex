import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

params = [
    # https://github.com/sstrickx/yahoofinance-api/pull/152/files#diff-8d68307bdbd437a4c6e7bece19d314248059d2a5d13240a33b631ab83af4b2abR236
    (True, 'STCAL_STATIC_CALENDAR_INSTANCE', 'Fake.java',
     '''@@ -0,0 +1,34 @@
      public static Calendar parseDateTime(String date, String time, TimeZone timeZone) {
        String datetime = date + " " + time;
        SimpleDateFormat format = new SimpleDateFormat("M/d/yyyy h:mma", Locale.US);''', 0, 1),
    # From spotBugs: https://github.com/spotbugs/spotbugs/blob/3883a7b750fb339577be073bc45e36b6f268777b/spotbugsTestCases/src/java/sfBugs/Bug3441912.java
    (True, 'STCAL_STATIC_CALENDAR_INSTANCE', 'Fake.java',
     '''@@ -0,0 +1,34 @@
        import java.util.Calendar;
        public class Main{
            public static final Calendar cal = Calendar.getInstance();
        }''', 1, 3),

    # From spotBugs: https://github.com/spotbugs/spotbugs/blob/3883a7b750fb339577be073bc45e36b6f268777b/spotbugsTestCases/src/java/sfBugs/Bug3441912.java
    (True, 'STCAL_STATIC_SIMPLE_DATE_FORMAT_INSTANCE', 'Bug3441912.java',
     '''@@ -0,0 +1,34 @@
        import java.text.DateFormat;
        import java.text.SimpleDateFormat;
        public class Main{
            public static final SimpleDateFormat FORMAT_DB_DATE = new SimpleDateFormat("yyyyMMdd");
            public static final DateFormat FORMAT_DB_DATE2 = new SimpleDateFormat("yyyyMMdd");
            public static  DateFormat formatDBDate3;
        }''', 3, 4),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int, line_no: int):
    patch = parse(patch_str, is_patch)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=['StaticDateFormatDetector'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0
