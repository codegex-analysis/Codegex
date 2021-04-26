import pytest

from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
from rparser import parse

params = [
    # From other repositories: https://github.com/usgs/warc-iridium-sbd-decoder/commit/505f5832c975be601acf9ccdfcd729e0134d79f7
    (True, 'VA_FORMAT_STRING_USES_NEWLINE', 'PseudobinaryBPayloadDecoder.java',
     '''@@ -278,7 +278,7 @@ Status processLine(final List<String> p_Line,
 		if (!findFirst.isPresent())
 		{
 			log.warn(String.format(
					"No matching data type for (name: %s, units: %s) among:\\n - %s",
 					name, units,
 					p_DataTypes.stream()
 							.map(type -> String.format(''', 1, 281),
    # From other repositories: https://github.com/jenkinsci/fortify-plugin/commit/c455799062f84d2d79a1c3f198816f73916d157d    (False, FindFinalizeInvocations(), 'VA_FORMAT_STRING_USES_NEWLINE', 'SutronStandardCsvPayloadDecoder.java',
    (True, 'VA_FORMAT_STRING_USES_NEWLINE', 'ProjectCreationService.java',
     "@@ -181,10 +181,10 @@ public Long createProject(ProjectDataEntry projectData) throws IOException, ApiE\n \t\t\t}\n \n \t\t\tif (issueTemplate != null) {\n+\t\t\t\tlogWriter.printf(\"Selected Issue Template is '%s'\\n\", issueTemplate.getName()); // Issue template found\n \t\t\t} else {\n \t\t\t\tissueTemplate = defaultIssueTemplate; // selected issue template is not valid so use default template\n+\t\t\t\tlogWriter.printf(\"Specified Issue Template ='%s' doesn't exist, template '%s' is used instead!\\n\",\n \t\t\t\t\t\tselectedIssueTemplateName, issueTemplate.getName());\n \t\t\t}\n \t\t}\n",
     2, 184),
    # https://api.github.com/repos/usgs/warc-iridium-sbd-decoder/commits/505f5832c975be601acf9ccdfcd729e0134d79f7
    (True, 'VA_FORMAT_STRING_USES_NEWLINE', 'PseudobinaryBPayloadDecoder.java',
     '''@@ -58,7 +58,7 @@ public PseudobinaryBPayloadDecoder()
				\"Invalid payload type for this decoder.\");

		final byte[] payload = p_Payload.getPayload();
		log.info(String.format(\"Payload:\\n%s\", new String(payload)));''', 1, 61),
    # https://github.com/jenkinsci/fortify-plugin/commit/c455799062f84d2d79a1c3f198816f73916d157d
    (True, 'VA_FORMAT_STRING_USES_NEWLINE', 'ProjectCreationService.java',
     '''@@ -171,7 +171,7 @@ public Long createProject(ProjectDataEntry projectData) throws IOException, ApiE

		if (selectedIssueTemplateName == null) {
			issueTemplate = defaultIssueTemplate;
			logWriter.printf(\"No Issue Template selected. Using default template '%s'.\\n\", issueTemplate.getName());''',
     1, 174),

    # DIY
    (True, 'VA_FORMAT_STRING_USES_NEWLINE', 'Fake_01.java',
     "@@ -58,7 +58,7 @@ public PseudobinaryBPayloadDecoder()\n \t\t\t\t\"Invalid payload type for this decoder.\");\n \n \t\tfinal byte[] payload = p_Payload.getPayload();\n+\t\tlog.info(String.format( Locale.US, \"Payload:\\n%s\", new String(payload))); \n \t\tfinal Queue<Byte> payloadQueue = Queues\n \t\t\t\t.newArrayBlockingQueue(payload.length);",
     1, 61),
    # DIY
    (True, 'VA_FORMAT_STRING_USES_NEWLINE', 'Fake_02.java',
     "@@ -280,7 +280,7 @@ private void setIntegerValue(final String projectAttributeValue,\n			value.setIntegerValue(Long.valueOf(projectAttributeValue));\n		} catch (NumberFormatException e) {\n			logWriter.printf(\"[WARN] Failed to set an integer value\\n\");",
     1, 282),
    (False, 'VA_FORMAT_STRING_USES_NEWLINE', 'Fake_03.java',
     '''if (expectedSha.equals(sha) == false) {
            final String exceptionMessage = String.format(
                Locale.ROOT,
                "SHA has changed! Expected %s for %s but got %s."
                    + "\\nThis usually indicates a corrupt dependency cache or artifacts changed upstream."
                    + "\\nEither wipe your cache, fix the upstream artifact, or delete %s and run updateShas",
                expectedSha,
                jarName,
                sha,
                shaFile
            );''', 1, 5),
    (False, 'VA_FORMAT_STRING_USES_NEWLINE', 'Fake_04.java',
     'warningMsg += String.format(\"\\\\n%s) %s: %s\", ++count, idName, resultId);', 0, 0),
]


@pytest.mark.parametrize('is_patch,pattern_type,file_name,patch_str,expected_length,line_no', params)
def test(is_patch: bool, pattern_type: str, file_name: str, patch_str: str, expected_length: int,
         line_no: int):
    patch = parse(patch_str, is_patch)
    patch.name = file_name
    engine = DefaultEngine(Context(), included_filter=['NewLineDetector'])
    engine.visit(patch)
    if expected_length > 0:
        assert len(engine.bug_accumulator) == expected_length
        assert engine.bug_accumulator[0].line_no == line_no
        assert engine.bug_accumulator[0].type == pattern_type
    else:
        assert len(engine.bug_accumulator) == 0


# DIY
def test_local_search():
    patch = parse('''PrintStream out = new PrintStream();
    out.format(\"Payload:\\n%s\", new String(payload)));''', is_patch=False)
    engine = DefaultEngine(Context(), included_filter=['NewLineDetector'])
    engine.visit(patch)
    assert len(engine.filter_bugs(level='medium')) == 1
