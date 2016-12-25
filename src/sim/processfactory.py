import importlib
import imp
import inspect
import collections
from sim.processes import process
from src.gui.events import EventSource
from src.sim.processes import model


class ProcessFactory(EventSource):
    def __init__(self):
        EventSource.__init__(self)
        self.register_event("algorithm_added")
        self.register_event("algorithm_remove")
        self.available_processes = []
        self.scripts = []
        self.network_models = collections.OrderedDict()
        self.process_models = collections.OrderedDict()

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

    def get_process_params_dict(self, name):
        params = self.get_process_parameters(name)
        d = {}
        for k, (val, _) in params.iteritems():
            d[k] = val
        return d

    def create_process(self, pid, ctx, name):
        process_class = self._get_process(name)
        if not process_class:
            raise Exception("Invalid process name")
        return process_class(pid, ctx)

    def _get_process(self, name):
        for p in self.available_processes:
            if p.NAME == name:
                return p
        return None

    def load_from_script(self, script):
        if script in self.scripts:
            msg = "Script '{0}' already loaded"
            print msg.format(script)
            return

        loaded_class_names = [c.NAME for c in self.available_processes]
        classes = self._get_process_classes(script)

        added = False
        for c in classes:
            if c.NAME not in loaded_class_names:
                self.available_processes.append(c)
                self.fire("algorithm_added", self, c)
                print "Added algorithm '{0}'".format(c.NAME)
                added = True
            else:
                print "Algorithm '{0}' is already loaded".format(c.NAME)
                continue

        if added:
            self.scripts.append(script)
        else:
            print "No new algorithms found in '{}'" + script

    def get_scripts(self):
        return self.scripts

    def clear_scripts(self):
        for script in self.scripts:
            self.remove_script(script)
        self.scripts = []

    def remove_script(self, script):
        if script in self.scripts:
            classes = self._get_process_classes(script)
            for c in classes:
                for pr in self.available_processes:
                    if c.NAME == pr.NAME:
                        self.available_processes.remove(pr)
                        self.fire("algorithm_remove", self, c)
                        break
            self.scripts.remove(script)

    def _get_process_classes(self, script):
        classes = []
        module = imp.load_source("", script)

        for class_name, _ in inspect.getmembers(module, inspect.isclass):
            clazz = getattr(module, class_name)
            try:
                self._class_check(clazz)
                classes.append(clazz)
                delattr(module, class_name)
            except Exception as ex:
                err_msg = "Class '{0}' from file '{1}' was skipped because {2}"
                print err_msg.format(class_name, script, ex.message)
                delattr(module, class_name)
                continue
        return classes

    def add_network_model(self, model):
        self.network_models[model.get_name()] = model

    def add_process_model(self, model):
        self.process_models[model.get_name()] = model

    def get_network_model(self, name):
        return self.network_models.get(name)

    def get_process_model(self, name):
        return self.process_models.get(name)

    def get_network_models(self):
        return self.network_models.keys()

    def get_process_models(self):
        return self.process_models.keys()

    def get_network_model_desc(self, model_name):
        model = self.get_network_model(model_name)
        if not model:
            raise Exception("Model '{0}' not exists in network models".format(model_name))

        return model.get_description()

    def get_process_model_desc(self, model_name):
        model = self.get_process_model(model_name)
        if not model:
            raise Exception("Model '{0}' not exists in process models".format(model_name))

        return model.get_description()


process_factory = ProcessFactory()
process_factory.add_process_model(model.DefaultProcessModel())
process_factory.add_network_model(model.DefaultNetworkModel())
process_factory.add_network_model(model.SlowNetworkModel())
process_factory.add_process_model(model.SlowProcessModel())

