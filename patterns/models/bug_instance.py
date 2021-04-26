confidence_map = {
    1: 'HIGH Confidence',
    2: 'MEDIUM Confidence',
    3: 'LOW Confidence',
    4: 'EXPERIMENTAL',
    5: 'IGNORE Confidence'
}


class BugInstance:
    def __init__(self, pattern_type: str, priority: int, file_name: str, line_no: int, description='', sha='',
                 line_content=''):
        self.type = pattern_type
        self.file_name = file_name
        self.commit_sha = sha
        self.line_no = line_no
        self.priority = priority
        self.description = description
        self.line_content = line_content

    def __str__(self):
        return '%s:%s:%s:%s' % (self.file_name, self.line_no, confidence_map[self.priority], self.type)
