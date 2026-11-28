"""Visual profiler for Python."""
import os

import psutil

INITIAL_RSS_SIZE = psutil.Process(os.getpid()).memory_info().rss
