import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from _microbench_common import microbench

class app(microbench):
    # The program never reads -msgsize.
    default_msg_size = 0

    def get_binary_path(self):
        return self.get_path("checker")
    
    def get_bench_name(self):
        return "Checker"