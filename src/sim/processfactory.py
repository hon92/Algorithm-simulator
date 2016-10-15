import importlib
import imp
import inspect
from sim.processes import process


class ProcessFactory():
    def __init__(self):
        self.available_processes = []
        self.scripts_paths = []

    def load_process_from_file(self, filename, class_name):
        module = importlib.import_module(filename)
        loaded_class = getattr(module, class_name)
        self._class_check(loaded_class)
        self._add_process_class(loaded_class)

    def _class_check(self, loaded_class):
        if not hasattr(loaded_class, "NAME"):
            raise Exception("Process has to have NAME attribute")
        if not hasattr(loaded_class, "DESCRIPTION"):
            raise Exception("Process has to have DESCRIPTION attribute")
        if not hasattr(loaded_class, "PARAMS"):
            raise Exception("Process has to have PARAMS attribute")
        if not issubclass(loaded_class, process.Process):
            raise Exception("Class has to extend from 'Process' class")

    def get_processes_names(self):
        return [p.NAME for p in self.available_processes]

    def get_process_description(self, name):
        p = self._get_process(name)
        if not p:
            raise Exception("Invalid process name")
        return p.DESCRIPTION

    def get_process_parameters(self, name):
        p = self._get_process(name)
        if not p:
            raise Exception("Invalid process name")
        return p.PARAMS

    def create_process(self, id, ctx, name):
        process_class = self._get_process(name)
        if not process_class:
            raise Exception("Invalid process name")
        return process_class(id, ctx)

    def _get_process(self, name):
        for p in self.available_processes:
            if p.NAME == name:
                return p
        return None

    def _add_process_class(self, process_class):
        if process_class not in self.available_processes:
            self.available_processes.append(process_class)
            return True
        return False

    def load_from_script(self, script_path):
        module = imp.load_source("", script_path)
        added_new_class = False
        for name, obj in inspect.getmembers(module, inspect.isclass):
            loaded_class = getattr(module, name)
            try:
                self._class_check(loaded_class)
            except Exception as ex:
                err_msg = "Class '{0}' from file '{1}' was skipped because {2}"
                print err_msg.format(loaded_class, script_path, ex.message)
                continue
            added = self._add_process_class(loaded_class)
            if added:
                added_new_class = True
        if added_new_class:
            self.scripts_paths.append(script_path)
        else:
            print "No scripts added from '{0}'".format(script_path)

    def get_scripts_paths(self):
        return self.scripts_paths

    def clear_scripts(self):
        self.scripts_paths = []

    def remove_script(self, script_path):
        if script_path in self.scripts_paths:
            self.scripts_paths.remove(script_path)


process_factory = ProcessFactory()
