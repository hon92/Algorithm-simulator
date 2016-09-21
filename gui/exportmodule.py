
class ExportDataModule():
    def __init__(self, simulator):
        self.simulator = simulator

    def print_to_file(self, filename):
        if filename:
            with open(filename, "w") as f:
                for row in self.get_data():
                    f.write(row)
                f.flush()

    def get_data(self):
        yield ""

"""
Csv export format
#process{process id};##monitor_name;###monitor_entry;arg1;arg2;arg3;
"""

class CSVExportDataModule(ExportDataModule):
    def __init__(self, simulator):
        ExportDataModule.__init__(self, simulator)

    def get_data(self):
        data = {}
        header = ""

        for pr in self.simulator.processes:
            mm = pr.get_monitor_manager()
            header += "#process{0};".format(pr.get_id())

            for m in mm.monitors:
                header += "##{0};".format(m.get_id())
                for entry in m.entries.values():
                    header += "###{0};".format(entry.entry_name)
                    for arg in entry.args:
                        header += arg + ";"

            monitors = mm.collect()
            for m in monitors:
                if pr.get_id() not in data:
                    data[pr.get_id()] = []
                data[pr.get_id()].append(m)

        yield header + "\n"
        line = ";"
        i = 1
        added = False

        while True:
            for pr in self.simulator.processes:
                monitors = data[pr.get_id()]
                for monitor in monitors:
                    line += ";"
                    for key in monitor:
                        line += ";"
                        values = monitor[key]
                        if len(values) >= i:
                            for v in values[i - 1]:
                                line += str(v) + ";"
                            added = True
                        else:
                            l = 1
                            mm = pr.get_monitor_manager()
                            for m in mm.monitors:
                                if key in m.entries:
                                    l = len(m.entries[key].args)
                                    break
                            line += ";"*l
                i += 1
                line += ";"
            if not added:
                break
            added = False
            yield line + "\n"
            line = ";"
