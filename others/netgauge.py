import os
from crab.wrappers.base import base

class app(base):
    metadata = [
        {'name': 'Avg-Duration', 'unit': 'us'   , 'conv': True },
        {'name': 'EBB'         , 'unit': 'MiBps', 'conv': False}
    ]

    def get_binary_path(self):
        return os.environ["CRAB_ROOT"] + "/src/netgauge-2.4.6/netgauge"
    
    # how to extract the data
    # Returns rows: one dict per measurement, keyed by metric name
    def read_data(self):  
        out_string = self.stdout
        out_lines = out_string.split('\n')
        names = [m['name'] for m in self.metadata]
        rows = []
        for line in out_lines[2:-4]:
            data_string = line.split(':')[-1]
            data_list = data_string.split(' ')
            data1 = float(data_list[1])
            data2 = float(data_list[3][1:])
            rows.append(dict(zip(names, [data1, data2])))
        return rows

    def get_bench_name(self):
        return "Netgauge - EBB"
    
    def get_bench_input(self):
        return ""