

class Model():

    def get_name(self):
        raise NotImplementedError()

    def get_description(self):
        return "No description"


class NetworkModel(Model):

    def get_latency(self):
        raise NotImplementedError()

    def get_speed(self):
        raise NotImplementedError()

    def evaluate_cost(self, msg):
        raise NotImplementedError()


class LinearNetworkModel(NetworkModel):

    def evaluate_cost(self, msg):
        return (msg.size * self.get_speed()) + self.get_latency()


class ProcessModel(Model):

    def get_process_speed(self, pid):
        raise NotImplementedError()

    def evaluate_time(self, pid, edge):
        return self.get_process_speed(pid) * edge.get_time()


class DefaultProcessModel(ProcessModel):

    def get_process_speed(self, pid):
        return 1

    def get_name(self):
        return "DefaultProcessModel"

    def get_description(self):
        return "Default process model with constant speed of processes"


class DefaultNetworkModel(LinearNetworkModel):

    def get_name(self):
        return "DefaultNetworkModel"

    def get_description(self):
        return "Default network model with no network penalty"

    def get_latency(self):
        return 0

    def get_speed(self):
        return 0


class SlowNetworkModel(LinearNetworkModel):

    def get_name(self):
        return "Slow network"

    def get_description(self):
        return "Modeling slow network communication"

    def get_latency(self):
        return 1.88

    def get_speed(self):
        return 1.2


class SlowProcessModel(ProcessModel):

    def get_name(self):
        return "Slow process model"

    def get_description(self):
        return "Model with 2x slower processes"

    def get_process_speed(self, pid):
        return 2

