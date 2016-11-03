import argparse
import sys
import json
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
        self.parser.add_argument("-m", "--model", type = str, help = "Model used for simulation")
        self.parser.add_argument("-pr", "--processes", type = int,
                            help = "Process count used for algorithm")
        self.parser.add_argument("-c", "--count", type = int,
                            help = "Simulation count")
        self.parser.add_argument("-args", "--arguments", type = json.loads,
                                 help = "Arguments used for algorithm\n \
(ALL process arguments MUST be specified in JSON format with theirs property names and property values in quotes)\n \
Example: ... -args \"{\\\"prop\\\":\\\"val\\\"}\"")

    def solve(self):
        args = self.parser.parse_args(self.args)

        if args.project:
            try:
                self.app.open_project(args.project)
            except Exception as ex:
                self.on_arg_error(ex.message)

            if args.select:
                available_processes_names = pf.process_factory.get_processes_names()
                model_names = pf.process_factory.get_models_names()

                if len(available_processes_names) == 0:
                    self.on_arg_error("No available processes")
                if len(model_names) == 0:
                    self.on_arg_error("No model available")

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
                process_type = available_processes_names[0]
                process_count = 1
                model = pf.process_factory.get_model(model_names[0])
                arguments = pf.process_factory.get_process_params_dict(process_type)

                if args.run:
                    if args.run not in available_processes_names:
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

                if args.model:
                    model = pf.process_factory.get_model(args.model)
                    if model is None:
                        self.on_arg_error("Unknown model name '{0}'".format(args.model))

                if args.arguments:
                    pr_args = args.arguments
                    params = pf.process_factory.get_process_parameters(process_type)
                    if len(pr_args) != len(params):
                        self.on_arg_error("Wrong process arguments length (should be {0})".format(len(params)))

                    arguments = {}
                    for name, (val, t) in params.iteritems():
                        v = pr_args.get(name)
                        if v is None:
                            self.on_arg_error("Missing process argument '{0}'".format(name))
                        try:
                            new_v = t(v)
                            arguments[name] = new_v
                        except Exception as ex:
                            self.on_arg_error("Invalid process argument value '{0}'".format(ex.message))

                t = self.app.project.get_project_tab()
                t.run_simulations(files,
                                  process_type,
                                  process_count,
                                  sim_count,
                                  model,
                                  arguments
                                  )

    def on_arg_error(self, msg):
        sys.stderr.write(msg + "\n")
        self.parser.print_help()
        sys.exit(1)

