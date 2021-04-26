class Context:
    """
    A context object contains state configurations and objects (patch set, patch, hunk and line) currently to be checked.
    It offers information for detectors.
    """

    def __init__(self):
        # current objects
        self.patch_set = None
        self.cur_patch = None
        self.cur_hunk = None
        self.cur_line = None
        self.cur_line_idx = -1

        # configuration
        self._online_search, self._repo_name, self._token = False, None, None
        self._local_search = True

    def set_patch_set(self, patch_set: tuple, repo_name=''):
        self.patch_set = patch_set
        self.cur_patch = None
        self.cur_hunk = None
        self.cur_line = None
        self.cur_line_idx = -1

        if repo_name:
            self._repo_name = repo_name

    def online_search(self):
        return self._online_search

    def enable_online_search(self, github_repo_name='', github_token=''):
        self._online_search = True
        if github_repo_name:
            self._repo_name = github_repo_name
        if github_token:
            self._token = github_token

    def update_repo_name(self, github_repo_name: str):
        self._repo_name = github_repo_name

    def disable_online_search(self):
        self._online_search = False
        self._repo_name = None
        self._token = None

    def get_online_search_info(self):
        return self._repo_name, self._token

    def local_search(self):
        return self._local_search

    def enable_local_search(self):
        self._local_search = True

    def disable_local_search(self):
        self._local_search = False
