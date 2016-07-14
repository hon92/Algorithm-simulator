import argparse
import sys
from sim.processes import process

class AppArgs:
    def __init__(self, app, args):
        self.app = app
        self.args = args
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-project", type = str, help = "Project file location")
        self.parser.add_argument("-select", type = int,
                            help = "Graph position in project (starting from 1)")
        self.parser.add_argument("-run", type = str, help = "Algorithm used for simulation")
        self.parser.add_argument("-processes", type = int,
                            help = "Process count used for algorithm")
        self.parser.add_argument("-count", type = int,
                            help = "Simulation count")

    def solve(self):
        args = self.parser.parse_args(self.args)

        if args.project:
            self.app.open_project(args.project)
            if args.select:
                project_files = self.app.project.get_files()
                args.select -= 1
                if args.select < 0 or args.select >= len(project_files):
                    self.on_arg_error("Graph not exist in project")

                files = [project_files[args.select]]
                sim_count = 1
                process_type = process.get_process_names()[0]
                process_count = 1

                if args.run:
                    if args.run not in process.get_process_names():
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
                                  sim_count,
                                  process_type,
                                  process_count)

    def on_arg_error(self, msg):
        sys.stderr.write(msg + "\n")
        self.parser.print_help()
        sys.exit(1)
