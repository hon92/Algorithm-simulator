

class ExportDataModule():
    def __init__(self, filename):
        self.filename = filename

    def print_to_file(self):
        data = self.get_data()
        with open(self.filename, "w") as f:
            f.write(data)
            f.flush()

    def get_data(self):
        return ""

"""
Csv export format
#process{process id};##monitor_name;###monitor_entry;arg1;arg2;arg3;
"""

class CSVExportDataModule(ExportDataModule):
    def __init__(self, filename, simulation):
        ExportDataModule.__init__(self, filename)
        self.simulation = simulation

    def get_data(self):
        processes = self.simulation.ctx.processes
        mm = self.simulation.ctx.monitor_manager

        def get_header():
            head = []
            pr_h = "#process{0};" #process
            m_h = "##{0};" #monitor
            e_h = "###{0};" #entry
            v_h = "{0};" #value

            for pr in processes:
                head.append(pr_h.format(pr.id))
                pr_monitors = mm.get_process_monitors(pr.id)
                if not pr_monitors:
                    continue
                for m in pr_monitors:
                    head.append(m_h.format(m.get_id()))
                    for e in m.entries.values():
                        head.append(e_h.format(e.entry_name))
                        for arg in e.args:
                            head.append(v_h.format(arg))
            return "".join(head)

        header = get_header()

        measured_data = {} # key -> process id, value -> data
        lines = []
        lines.append(header)
        lines.append("\n")
        v = "{0};"
        e = ";"

        for pr in processes:
            data_gen = mm.collect(pr.id)
            for m_data in data_gen:
                data = measured_data.get(pr.id)
                if data:
                    data.append(m_data)
                else:
                    measured_data[pr.id] = [m_data]

        added = False
        i = 0
        while True:
            for pr in processes:
                lines.append(e)
                md = measured_data[pr.id]
                for d in md:
                    lines.append(e)
                    for entry in d:
                        lines.append(e)
                        values = d[entry]
                        if len(values) > i:
                            for vv in values[i]:
                                lines.append(v.format(vv))
                            added = True
                        else:
                            l = 1
                            for m in mm.get_process_monitors(pr.id):
                                skipped_entry = m.entries.get(entry)
                                if skipped_entry:
                                    l = len(skipped_entry.args)
                                    break
                            lines.append(e*l)
            i += 1
            lines.append(e)
            if not added:
                break
            added = False
            lines.append("\n")
        return "".join(lines)

