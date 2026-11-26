import os
import sys
sys.path.append(os.path.dirname(__file__))
from _cp_base import cp_base


class app(cp_base):

    @property
    def benchmark_id(self) -> str:
        return "qe-v7"
