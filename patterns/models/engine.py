from rparser import Patch
from utils import log_message
from gen_detectors import DETECTOR_DICT
from .priorities import *
from .context import Context
from timer import Timer


class BaseEngine:
    """
    The interface which all bug pattern detectors must implement.
    An engine maintains a Context object, and assigns tasks to detectors.
    """

    def __init__(self, context: Context, included_filter=None, excluded_filter=None):
        """
        Init detectors according to included_filter or excluded_filter
        :param included_filter: a list or tuple of detector class names to include
        :param excluded_filter: a list or tuple of detector class names to exclude
        """
        self.bug_accumulator = list()  # every patch set should own a new bug_accumulator
        self._detectors = dict()
        assert isinstance(context, Context)
        self.context = context

        if included_filter:
            for name in included_filter:
                detector_class = DETECTOR_DICT.get(name, None)
                if detector_class:
                    self._detectors[name] = detector_class()
        elif excluded_filter:
            for name, detector_class in DETECTOR_DICT.items():
                if name not in excluded_filter:
                    self._detectors[name] = detector_class()
        else:
            for name, detector_class in DETECTOR_DICT.items():
                self._detectors[name] = detector_class()

    def visit(self, *patch_set):
        self.context.set_patch_set(patch_set)
        self.bug_accumulator = list()  # reset

        for patch in self.context.patch_set:
            self._visit_patch(patch)

    def _visit_patch(self, patch):
        """
        Update context and assign tasks to detectors
        :param patch: code from a single file to visit
        :return: bug instances
        """
        pass

    def filter_bugs(self, level=None):
        if not level:
            return self.bug_accumulator

        if level == 'low':
            bound = LOW_PRIORITY
        elif level == 'medium':
            bound = MEDIUM_PRIORITY
        elif level == 'high':
            bound = HIGH_PRIORITY
        elif level == 'exp':
            bound = EXP_PRIORITY
        elif level == 'ignore':
            bound = IGNORE_PRIORITY
        else:
            raise ValueError('Invalid level value. Hint: ignore, exp, low, medium, high')

        return tuple(bug for bug in self.bug_accumulator if bug.priority <= bound)

    def report(self, level='low'):
        """
        This method is called after all patches to be visited.
        """
        for bug_ins in self.filter_bugs(level):
            log_message(str(bug_ins), 'info')


class DefaultEngine(BaseEngine):
    """
    ParentDetector and SubDetector are for multiple single-line patterns in the same file
    """

    def _visit_patch(self, patch: Patch):
        """
        Update context and assign tasks to detectors
        :param patch:
        :return: None
        """

        self.context.cur_patch = patch

        # detect patch
        for hunk in patch:
            self.context.cur_hunk = hunk

            for i in range(len(hunk.lines)):
                # detect all lines in the patch rather than the addition
                if i in hunk.dellines:
                    continue

                self.context.cur_line_idx = i
                self.context.cur_line = hunk.lines[i]

                detector_timers = dict()
                for name, detector in self._detectors.items():
                    if name not in detector_timers:
                        detector_timers[name] = Timer(name=name, logger=None)
                    detector_timers[name].start()
                    detector.match(self.context)
                    detector_timers[name].stop()

        # collect bug instances
        for detector in list(self._detectors.values()):
            if detector.bug_accumulator:
                self.bug_accumulator += detector.bug_accumulator
                detector.reset_bug_accumulator()
