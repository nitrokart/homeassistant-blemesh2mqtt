import collections
import logging


class LogBuffer(logging.Handler):
    """
    Keeps the most recent log lines for the web UI
    """

    def __init__(self, size=300):
        super().__init__()
        self._lines = collections.deque(maxlen=size)
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%H:%M:%S"))

    def emit(self, record):
        self._lines.append(self.format(record))

    def lines(self):
        return list(self._lines)
