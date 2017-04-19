

class Model():
    """
    Base class of model for simulation environment.
    """
    def get_name(self):
        """
        Returns model name.

        :return: name of model
        :rtype: str
        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()

    def get_description(self):
        """
        Returns model description.

        :return: description of model
        :rtype: str
        """
        return "No description"


class NetworkModel(Model):
    """
    Base class for network model.
    """
    def get_latency(self):
        """
        Returns latency of network.

        :return: latency of network
        :rtype: int
        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()

    def get_speed(self):
        """
        Returns speed of network.

        :return: speed of network
        :rtype: int
        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()

    def evaluate_cost(self, msg):
        """
        Returns network cost based on model settings and given message.

        :param: msg: message
        :type: Message
        :return: network cost
        :rtype: int
        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()


class LinearNetworkModel(NetworkModel):
    """
    Network model with linear implementation of evaluate method.
    """
    def evaluate_cost(self, msg):
        return (msg.size * self.get_speed()) + self.get_latency()


class ProcessModel(Model):
    """
    Base class for process model.
    """
    def get_process_speed(self, pid):
        """
        Returns speed of process based on given process id.

        :param: pid: id of process
        :type: int
        :return: speed of process
        :rtype: int
        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()

    def evaluate_time(self, pid, edge):
        """
        Returns time to compute edge based on process speed
        and given edge.

        :param: pid: id of process
        :type: int
        :param: edge: edge
        :type: Edge
        :return: time to compute edge
        :rtype: int
        """
        return self.get_process_speed(pid) * edge.get_time()


class DefaultProcessModel(ProcessModel):
    """
    Default speed process model.
    """
    def get_process_speed(self, pid):
        return 1

    def get_name(self):
        return "DefaultProcessModel"

    def get_description(self):
        return "Default process model with constant speed of processes"


class DefaultNetworkModel(LinearNetworkModel):
    """
    Default network model.
    """
    def get_name(self):
        return "DefaultNetworkModel"

    def get_description(self):
        return "Default network model with no network penalty"

    def get_latency(self):
        return 0

    def get_speed(self):
        return 0


class SlowNetworkModel(LinearNetworkModel):
    """
    Slow network model.
    """
    def get_name(self):
        return "Slow network"

    def get_description(self):
        return "Modeling slow network with 30ms latency and speed 100Mbit/s."

    def get_latency(self):
        return 0.03

    def get_speed(self):
        return 0.00001


class SlowProcessModel(ProcessModel):
    """
    Slow process model.
    """
    def get_name(self):
        return "Slow process model"

    def get_description(self):
        return "Model with 2x slower processes"

    def get_process_speed(self, pid):
        return 2

