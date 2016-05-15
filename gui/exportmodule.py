
class ExportDataModule():
    def __init__(self, simulator):
        self.simulator = simulator

    def print_to_file(self, filename):
        print "export data to " + filename

    def get_data(self):
        yield ""
            
class CSVExportDataModule(ExportDataModule):
    def __init__(self, simulator):
        ExportDataModule.__init__(self, simulator)

    def print_to_file(self, filename):
        if filename:
            with open(filename.get_path(), "w") as f:
                for row in self.get_data():
                    f.write(row)
                f.flush()

    def get_data(self):
        row_index = 0
        end = True
        header_line = ""

        for i in xrange(len(self.simulator.processes)):
            process = self.simulator.processes[i]
            header_line += process.get_name() + " " + str(i)
            monitor = process.monitor
            for m in monitor.monitors:
                header_line += ";" + m + ";"
            header_line += ";"
        yield header_line + "\n"

        while True:
            line = ""
            full_line = ""
            for i in xrange(len(self.simulator.processes)):
                process = self.simulator.processes[i]
                monitor = process.monitor
                line = ";"
                for m in monitor.monitors:
                    x = monitor.monitors[m]["x"]
                    y = monitor.monitors[m]["y"]
                    if row_index < len(x):
                        xval = x[row_index]
                        yval = y[row_index]
                        line += str(xval) + ";" + str(yval) + ";"
                        end = False
                    else:
                        line += ";" + ";"
                full_line += line
            yield full_line + "\n"
            row_index += 1
            line = ""
            if end:
                break
            end = True
