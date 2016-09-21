import argparse
import sys
from sim import processfactory as pf


class AppArgs:
    def __init__(self, app, args):
        self.app = app
        self.args = args
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-p", "--project", type = str, help = "Project file location")
        self.parser.add_argument("-s", "--select", type = list,
                            help = "Graph position in project (starting from 1)")
        self.parser.add_argument("-r", "--run", type = str, help = "Algorithm used for simulation")
        self.parser.add_argument("-pr", "--processes", type = int,
                            help = "Process count used for algorithm")
        self.parser.add_argument("-c", "--count", type = int,
                            help = "Simulation count")

    def solve(self):
        args = self.parser.parse_args(self.args)

        if args.project:
            self.app.open_project(args.project)
            if args.select:
                project_files = self.app.project.get_files()
                used = []
                for s in args.select:
                    if s == " " or s == ",":
                        continue

                    try:
                        val = int(s)
                    except:
                        self.on_arg_error("Selection must be list of integers")

                    val -= 1
                    if len(project_files) == 0:
                        msg = "Can not use selection when project has no files"
                        self.on_arg_error(msg.format(len(project_files)))
                    if val < 0 or val >= len(project_files):
                        msg = "Selection must be between 1 to {0}"
                        self.on_arg_error(msg.format(len(project_files)))
                    if val not in used:
                        used.append(val)

                files = [project_files[i] for i in used]

                sim_count = 1
                process_type = pf.get_processes_names()[0]
                process_count = 1

                if args.run:
                    if args.run not in pf.get_processes_names():
                        self.on_arg_error("Process type not valid")
                    process_type = args.run

                if args.processes:
                    if args.processes < 0 or args.processes > 50:
                        self.on_arg_error("Process count must be between 1 - 50\n")
                    process_count = args.processes

                if args.count:
                    if args.count < 0 or args.count > 100:
                        self.on_arg_error("Simulation count must be between 1 - 100")
                    sim_count = args.count

                t = self.app.project.get_project_tab()
                t.run_simulations(files,
                                  process_type,
                                  process_count,
                                  sim_count
                                  )

    def on_arg_error(self, msg):
        sys.stderr.write(msg + "\n")
        self.parser.print_help()
        sys.exit(1)

