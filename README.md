## Getting Start

### Preprocessing

Given a patch ([see examples](https://github.com/codegex-analysis/codegex-evaluation/blob/main/result/pull-request/crawl-pr/java/files/094698200/NanoHomework/pulls/54/files.json)), call `parse(stream, is_patch=True, name='')` in `parser.py` to split the patch into "statements" by terminators like `;`, `{`, `}`.

```python
from rparser import parse

diff_string = "@@ -0,0 +1,21 @@\n+public class ArrayJava {\n+    public static void main(String[] args) {\n+        int[] mas = {3, 3, 8, 9, 7, 8, 4, 6, 6, 8, 6, 9, 8, 6, 3, 3, 3, 5};\n+\n+        int a = 0;\n+        int d = 0;\n+        for (int i = 0; i < mas.length; i++) {\n+            for (int j = i + 1; j < mas.length - 1; j++) {\n+                if (mas[i] == mas[j]) {\n+                    a = mas[i];\n+                    d++;\n+\n+                }\n+\n+            }\n+            System.out.println(\"элемент \" + a + \" встречается \" + d + \" раз\\n\");\n+            d = 0;\n+            break;\n+        }\n+    }\n+}"

patch = parse(diff_string, name='src/ArrayJava.java')
```

If you want to patch the content of a Java file, you should set `is_patch` as `False`.

```python
with open(java_file_path, 'r') as f:
     patch = parse(f.read(), is_patch=False, name=file_name)
```



### Analyzing

First, create a `DefaultEngine` instance with a `Context` instance. An engine will call detectors to check each statements, while the context contains some pointers to currently detected patch set, patch, hunk and line that may be used by detectors.

```java
from patterns.models.context import Context
from patterns.models.engine import DefaultEngine
  
context = Context()
# context.enable_online_search()  # Time-consuming operation that searches code via Github API
engine = DefaultEngine(context)
  
engine.visit(*patchset)   # Here, patchset is a list of patch and you can only pass a single patch
bug_instances = engine.filter_bugs(level='low')  # Return a list of warning objects of BugInstance type Codegex found.
```

You can include/exclude detectors by passing a list of detector names to `included_filter`/`excluded_filter` of the constructor of an engine. All available detector names are in [gen_detectors.py](https://github.com/codegex-analysis/Codegex/blob/main/gen_detectors.py)



### Automatically Comment Generating

The code is in [codegex-evaluation](https://github.com/codegex-analysis/codegex-evaluation/tree/main/result/pull-request/scripts/auto-comment).