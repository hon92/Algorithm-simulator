
INSTANT_PROCESS_SPEED = 1
FAST_PROCESS_SPEED = 1.2
NORMAL_PROCESS_SPEED = 1.5
SLOW_PROCESS_SPEED = 2

INSTANT_NET_SPEED = 0
FAST_NET_SPEED = 1.2
NORMAL_NET_SPEED = 1.8
SLOW_NET_SPEED = 2.5


class Model():

    def get_default_process_speed(self):
        raise NotImplementedError()

    def get_net_speed(self):
        raise NotImplementedError()

    def get_process_speed(self, process):
        raise NotImplementedError()

    def calculate_edge_time(self, process, edge):
        raise NotImplementedError()

    def calculate_send_time(self, msg):
        raise NotImplementedError()

    def get_name(self):
        raise NotImplementedError()


class LinearModel(Model):
    def __init__(self, def_net_speed, def_process_speed):
        self.net_speed = def_net_speed
        self.process_default_speed = def_process_speed
        self.process_speed_map = {}

    def get_process_speed(self, process):
        process_speed = self.process_speed_map.get(process.get_id())
        if process_speed is None:
            return self.process_default_speed
        return process_speed

    def set_process_speed(self, process, speed):
        self.process_speed_map[process.get_id()] = speed

    def get_default_process_speed(self):
        return self.process_default_speed

    def get_net_speed(self):
        return self.net_speed

    def calculate_edge_time(self, process, edge):
        return edge.get_time() * self.get_process_speed(process)

    def calculate_send_time(self, msg):
        return msg.size * self.net_speed


class LimitlessModel(LinearModel):

    DESCRIPTION = "Without any limitations on network or processes"

    def __init__(self):
        LinearModel.__init__(self, INSTANT_NET_SPEED, INSTANT_PROCESS_SPEED)

    def get_name(self):
        return "No limit"


class SlowNetModel(LinearModel):

    DESCRIPTION = "Communication between processes is slow"

    def __init__(self):
        LinearModel.__init__(self, SLOW_NET_SPEED, INSTANT_PROCESS_SPEED)

    def get_name(self):
        return "Slow communication"


class SlowProcessModel(LinearModel):

    DESCRIPTION = "Processes are slower"

    def __init__(self):
        LinearModel.__init__(self, INSTANT_NET_SPEED, SLOW_PROCESS_SPEED)

    def get_name(self):
        return "Slow processes"

