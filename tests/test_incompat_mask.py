import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse
from patterns.models.priorities import *

params = [
    # From other repository: https://github.com/albfan/jmeld/commit/bab5df4d96b511dd1e4be36fce3a2eab52c24c4e
    (True, 'BIT_SIGNED_CHECK', "Fake.java",
     '''@@ -51,7 +51,7 @@ public void hierarchyChanged(HierarchyEvent e)
             {
               JRootPane rootPane;

              if ((e.getChangeFlags() & 1) > 0)
               {
                 rootPane = getRootPane();
                 if (rootPane == null)}''', 1, 54),
    # From other repository: https://github.com/bndtools/bnd/commit/68c73f78ef7de5234714b350a7d0b8760f9eaf1a
    (True, 'BIT_SIGNED_CHECK', "Fake.java",
     '''@@ -222,7 +222,7 @@ public void resourceChanged(IResourceChangeEvent event) {
             if (delta == null)
                 return;

    +        if ((delta.getKind() & 4) > 0 && (delta.getFlags() & MARKERS) > 0) {
                 getEditorSite().getShell().getDisplay().asyncExec(new Runnable() {
                     public void run() {
                         loadProblems();''', 1, 225),
    # DIY from https://github.com/SpigotMC/BungeeCord/blob/master/protocol/src/main/java/net/md_5/bungee/protocol/Varint21LengthFieldPrepender.java
    (False, 'BIT_AND_ZZ', 'Varint21LengthFieldPrepender.java',
     '''private static int varintSize(int paramInt){
                if ( ( paramInt & 0xFFFFFF80 ) == 0 ) { return 1;}
                if ( ( paramInt & 0xFFFFC000 ) == 0 ) { return 2;}
                if ( ( paramInt & 0x00000000 ) == 0 ) { return 3;}
                if ( ( paramInt & 0xF0000000 ) == 0 ) { return 4;}
                return 5;
            }''', 1, 4),

    (False, 'BIT_SIGNED_CHECK_HIGH_BIT', 'TMP.java', 'if ((x | 0x80000000) < 0)', 1, 1),

    # from https://github.com/betterlife/betterlifepsi/issues/158
    (False, 'BIT_IOR', 'BitIOR1.java', 'if ((x | 0x1) == 0x0) {', 1, 1),

    # https://github.com/threerings/getdown/commit/f33527284f04db3daf4b916c74549d96008140f4
    (False, 'BIT_IOR', 'BitIOR2.java', 'if ((e | 1) != 0) {', 1, 1),

    # https://github.com/avrora-framework/avrora/issues/6
    (False, 'BIT_AND', 'BitAnd1.java', 'if ((e & 0x40) == 0x1){', 1, 1),

    # https://github.com/HighTechRedneck42/JMRI/commit/a6dbbcb302286dedf085dfc763d58726cfe31288
    (False, 'BIT_AND', 'BitAnd2.java', '''if (((e & 4) == 4)
                    || ((e & 2) == 4)) {''', 1, 2),

    # DIY two bug instances
    (False, 'BIT_IOR', 'BitAnd3.java', '''if (((e | 1) == 0)
                    || ((e & 2) == 4)) {''', 2, 1),
    # fastjson/src/main/java/com/alibaba/fastjson/util/UTF8Decoder.java
    (False, 'BIT_SIGNED_CHECK', 'UTF8Decoder.java',
     'int uc = ((b1 & 0x07) << 18) | ((b2 & 0x3f) << 12) | ((b3 & 0x3f) << 06) | (b4 & 0x3f);', 0, 1),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int,
         line_no: int):
    patch = parse(patch_str, is_patch)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=['IncompatMaskDetector'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0


testcases = [
    # high long
    ('''public boolean bugHighGT(long x) {
            if (( 0x8000000000000000L & x) > 0)
                return true;
            return false;
        }''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, HIGH_PRIORITY),
    ('''public boolean bugHighGE(long x) {
            if ((x & 0x8000000000000000L) >= 0)
                return true;''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, MEDIUM_PRIORITY),
    ('''public boolean bugHighLT(long x) {
            if ((x & 0x8000000000000000L) < 0)
                return true;''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, MEDIUM_PRIORITY),
    ('''public boolean bugHighLE(long x) {
            if ((x & 0x8000000000000000L) <= 0)
                return true;''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, HIGH_PRIORITY),
    # low int
    ('''public boolean bugLowGT(long x) {
                if ((x & 0x1) > 0)
                    return true;
                return false;
            }''', 'BIT_SIGNED_CHECK', 1, 2, LOW_PRIORITY),
    ('''public boolean bugLowGE(long x) {
                if ((x & 0x1) >= 0)
                    return true;''', 'BIT_SIGNED_CHECK', 1, 2, LOW_PRIORITY),
    ('''public boolean bugLowLT(long x) {
                if ((x & 0x1) < 0)
                    return true;''', 'BIT_SIGNED_CHECK', 1, 2, LOW_PRIORITY),
    ('''public boolean bugLowLE(long x) {
                if ((x & 0x1) <= 0)
                    return true;''', 'BIT_SIGNED_CHECK', 1, 2, LOW_PRIORITY),
    # high int
    ('''public boolean bugHighGT(int x) {
            if ((x & 0x80000000) > 0)
                return true;
            return false;
        }''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, HIGH_PRIORITY),
    ('''public boolean bugHighGE(int x) {
            if ((x & 0x80000000) >= 0)
                return true;''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, MEDIUM_PRIORITY),
    ('''public boolean bugHighLT(int x) {
            if ((x & 0x80000000) < 0)
                return true;''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, MEDIUM_PRIORITY),
    ('''public boolean bugHighLE(int x) {
            if ((x & 0x80000000) <= 0)
                return true;''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, HIGH_PRIORITY),

    # medium int
    ('''public boolean bugMediumGT(int x) {
            if ((x & 0x10000000) > 0)
                    return true;
                return false;
            }''', 'BIT_SIGNED_CHECK', 1, 2, MEDIUM_PRIORITY),
    ('''public boolean bugMediumGE(int x) {
                if ((x & 0x10000000) >= 0)
                    return true;''', 'BIT_SIGNED_CHECK', 1, 2, MEDIUM_PRIORITY),
    ('''public boolean bugMediumLT(int x) {
                if ((x & 0x10000000) < 0)
                    return true;''', 'BIT_SIGNED_CHECK', 1, 2, MEDIUM_PRIORITY),
    ('''public boolean bugMediumLE(int x) {
                if ((x & 0x10000000) <= 0)
                    return true;''', 'BIT_SIGNED_CHECK', 1, 2, MEDIUM_PRIORITY),
    # not
    ('''public boolean bugNotMediumMask(int x) {
            if ((x & ~0x10000000) > 0)
                return true;''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, HIGH_PRIORITY),
    # DIY
    ('''public boolean DIY(int x) {
            if ((x & -10) <= 0)
                return true;''', 'BIT_SIGNED_CHECK_HIGH_BIT', 1, 2, HIGH_PRIORITY),
]


@pytest.mark.parametrize('patch_str,expected_warning,expected_length,expected_line_no,expected_priority', testcases)
def test_spotbugs_cases(patch_str: str, expected_warning: str, expected_length: str, expected_line_no: int,
                        expected_priority: int):
    patch = parse(patch_str, is_patch=False)
    engine = DefaultEngine(Context(), included_filter=['IncompatMaskDetector'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].type == expected_warning
        assert engine.bug_accumulator[0].line_no == expected_line_no
        assert engine.bug_accumulator[0].priority == expected_priority

    else:
        assert len(engine.bug_accumulator) == 0


# https://github.com/gavioto/findbugs/blob/master/findbugsTestCases/src/java/IncompatMaskTest.java
def test_1():
    patch = parse('''public static void foo(int i) {
        if ((i & 16) == 2)
            System.out.println("warn");
        if ((i & 16) != 2)
            System.out.println("warn");
        if ((i | 16) == 2)
            System.out.println("warn");
        if ((i | 16) != 2)
            System.out.println("warn");

        if ((i & 16) < 2)
            System.out.println("unsupp");
        if ((i | 16) < 2)
            System.out.println("unsupp");

        if ((i & 3) == 2)
            System.out.println("bogus");
        if ((i & 3) != 2)
            System.out.println("bogus");
        if ((i | 3) == 7)
            System.out.println("bogus");
        if ((i | 3) == 7)
            System.out.println("bogus");

         if ((i & 16L) == 2) System.out.println("warn");
         if ((i & 16L) != 2) System.out.println("warn");
         if ((i | 16L) == 2) System.out.println("warn");
         if ((i | 16L) != 2) System.out.println("warn");
    }''', is_patch=False)
    engine = DefaultEngine(Context(), included_filter=['IncompatMaskDetector'])
    engine.visit(patch)
    assert len(engine.bug_accumulator) == 8
    assert engine.bug_accumulator[0].type == 'BIT_AND'
    assert engine.bug_accumulator[0].line_no == 2
    assert engine.bug_accumulator[1].type == 'BIT_AND'
    assert engine.bug_accumulator[1].line_no == 4
    assert engine.bug_accumulator[2].type == 'BIT_IOR'
    assert engine.bug_accumulator[2].line_no == 6
    assert engine.bug_accumulator[3].type == 'BIT_IOR'
    assert engine.bug_accumulator[3].line_no == 8

    assert engine.bug_accumulator[4].type == 'BIT_AND'
    assert engine.bug_accumulator[4].line_no == 25
    assert engine.bug_accumulator[5].type == 'BIT_AND'
    assert engine.bug_accumulator[5].line_no == 26
    assert engine.bug_accumulator[6].type == 'BIT_IOR'
    assert engine.bug_accumulator[6].line_no == 27
    assert engine.bug_accumulator[7].type == 'BIT_IOR'
    assert engine.bug_accumulator[7].line_no == 28


def test_2():
    patch = parse('''public static void bar(int i) {
        if ((i & 16) == 2)
            return; /* always unequal */
        if ((i & 16) != 2)
            return; /* always unequal */
        if ((i | 16) == 2)
            return; /* always unequal */
        if ((i | 16) != 0)
            return; /* always unequal */
        if ((i & 0) == 1) // Eclipse optimizes this away so we can't catch it
            return; /* never equal */
        if ((i & 0) != 1) // Eclipse optimizes this away so we can't catch it
            return; /* never equal */
        if ((i & 0) == 0) // Eclipse optimizes this away so we can't catch it
            return; /* always equal */
        if ((i & 0) != 0) // Eclipse optimizes this away so we can't catch it
            return; /* always equal */
        if ((i | 1) == 0)
            return; /* never equal */
        if ((i | 1) != 0)
            return; /* never equal */
        if ((i & 16L) == 2)
            return; /* always unequal */
        if ((i & 16L) != 2)
            return; /* always unequal */
        if ((i | 16L) == 2)
            return; /* always unequal */
        if ((i | 16L) != 0)
            return; /* always unequal */
        if ((i & 0L) == 0) // Eclipse optimizes this away so we can't catch it
            return; /* always equal */
        if ((i & 0L) != 0) // Eclipse optimizes this away so we can't catch it
            return; /* always equal */
        if ((i | 1L) == 0)
            return; /* never equal */
        if ((i | 1L) != 0)
            return; /* never equal */
        System.out.println("foo");
    }''', is_patch=False)
    engine = DefaultEngine(Context(), included_filter=['IncompatMaskDetector'])
    engine.visit(patch)
    assert len(engine.bug_accumulator) == 18


def test_3():
    patch = parse('''public static void moreBars(short i) {
        if ((i | 0xff00) == 0xFFFF0000) {
            System.out.println();
        }

        if ((i | 0xff00) == 0x00FF) {
            System.out.println();
        }
    }''', is_patch=False)
    engine = DefaultEngine(Context(), included_filter=['IncompatMaskDetector'])
    engine.visit(patch)
    assert len(engine.bug_accumulator) == 2
    assert engine.bug_accumulator[0].type == 'BIT_IOR'
    assert engine.bug_accumulator[0].line_no == 2
    assert engine.bug_accumulator[1].type == 'BIT_IOR'
    assert engine.bug_accumulator[1].line_no == 6
