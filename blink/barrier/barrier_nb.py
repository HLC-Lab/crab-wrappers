import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from _microbench_common import microbench

class app(microbench):
    # A barrier sends no payload, so -msgsize means nothing to it.
    default_msg_size = 0

    def get_binary_path(self):
        return self.get_path("barrier_nb")
    
    def get_bench_name(self):
        return "IBarrier"