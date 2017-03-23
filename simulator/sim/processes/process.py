import simpy
import gobject
import monitor
from simulator.gui.events import EventSource
from collections import deque


class ProcessContext():
    """
    Class processContext

    :param: env: environment for process
    :type: Environment
    :param: monitor_manager: monitor manager
    :type: MonitorManager
    :param: arguments: arguments for process
    :type: dict
    """
    def __init__(self, env, monitor_manager, arguments):
        self.env = env
        self.arguments = arguments
        self.monitor_manager = monitor_manager


class Process(EventSource):
    """
    Base process for simulations.

    :param: id: id of process
    :type: int
    :param: name: name of process
    :type: str
    :param: ctx: context of process
    :type: ProcessContext
    """
    def __init__(self, id, name, ctx):
        EventSource.__init__(self)
        self.register_event("wait")
        self.register_event("notify")
        self.register_event("sleep")
        self.register_event("log")
        self._sleep = False
        self.id = id
        self.name = name
        self.ctx = ctx
        self.block_event = ctx.env.event()
        self.clock = Clock(self)
        self.communicator = Communicator(self)
        self.communicator.connect("async_receive", self.on_async_receive)
        mm = ctx.monitor_manager
        mm.register_process_monitor(self.id, monitor.ProcessMonitor(self))
        mm.register_process_monitor(self.id, monitor.ClockMonitor(self))
        mm.register_process_monitor(self.id, monitor.CommunicationMonitor(self))
        mm.register_process_monitor(self.id, monitor.MemoryMonitor(self))

    def get_id(self):
        """
        Returns ID of process.

        :return: id of process
        :rtype: int
        """
        return self.id

    def get_name(self):
        """
        Returns name of process.

        :return: name of process
        :rtype: str
        """
        return self.name

    def is_awake(self):
        """
        Returns if process is awake.

        :return: 'True' if process is awake, 'False' otherwise.
        :rtype: bool
        """
        return not self._sleep

    def wait(self, sleep_time = None):
        """
        Sleep process for amount of 'sleep_time'. If 'sleep_time' is None,
        process will sleep until some other process will wake up.

        :param: sleep_time
        :type: int
        :return: Simpy event
        :rtype: event
        """
        now = self.ctx.env.now
        if sleep_time is not None:
            if sleep_time < 0:
                raise Exception("sleep time can't be smaller then 0")
            self.fire("sleep", now, sleep_time)
            mm = self.ctx.monitor_manager
            gtm = mm.get_monitor("GlobalTimeMonitor")
            time_evt = self.ctx.env.timeout(sleep_time)

            def time_evt_callback(e):
                gtm.add_timeout(self.ctx.env.now, sleep_time, self.id)
                self.clock.wait(sleep_time)
            time_evt.callbacks.append(time_evt_callback)
            return time_evt

        else:
            self.fire("wait", now)
            self._sleep = True
            return self.block_event

    def notify(self, val = None):
        """
        Wake up process if process slept.

        :param: val: value for event
        :type: int
        """
        if self._sleep:
            self.block_event.succeed(val)
            self.block_event = self.ctx.env.event()
            self._sleep = False
            self.fire("notify", self.ctx.env.now)

    def log(self, message, msg_tag = "out"):
        """
        Write message to simulator console.

        :param: message: message
        :type: str
        :param: msg_tag: type of message (out | err | warn)
        :type: str
        """
        gobject.idle_add(self.fire, "log", message, msg_tag, priority = gobject.PRIORITY_HIGH)

    def init_monitor_callbacks(self):
        """
        Init of monitors callbacks.
        """
        mm = self.ctx.monitor_manager
        mm.add_process_callback("wait", self.id, self)
        mm.add_process_callback("notify", self.id, self)
        mm.add_process_callback("sleep", self.id, self)
        mm.add_process_callback("log", self.id, self)
        mm.add_process_callback("async_receive", self.id, self.communicator)
        mm.add_process_callback("async_send", self.id, self.communicator)
        mm.add_process_callback("receive", self.id, self.communicator)
        mm.add_process_callback("send", self.id, self.communicator)
        mm.add_process_callback("time_stamp", self.id, self.clock)
        mm.add_process_callback("step", self.id, self.clock)
        gtm = mm.get_monitor("GlobalTimeMonitor")
        mm.add_callback("timeout", gtm)

    def post_init(self):
        """
        Post init of monitors callbacks.
        """
        mm = self.ctx.monitor_manager
        gtm = mm.get_monitor("GlobalTimeMonitor")
        gtm.add_timeout(0, 0, self.id)

    def init(self):
        """
        Abstract method for initialization of process.

        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()

    def get_used_memory(self):
        """
        Abstact method for return used memory on process.

        :return: used memory size
        :rtype: int
        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()

    def run(self):
        """
        Abstract main method for process. This method must be generator.

        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()

    def on_async_receive(self, msg):
        """
        Abstract method for receive async message.

        :param: msg: message
        :type: Message
        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()


class GraphProcess(Process):
    """
    Graph process for simulations. This process is for solving graphs of state spaces.
    """
    NAME = "Unknow"
    DESCRIPTION = "No description"
    ARGUMENTS = {}

    def __init__(self, id, name, ctx):
        Process.__init__(self, id, self.NAME, ctx)
        self.register_event("edge_discovered")
        self.register_event("edge_calculated")
        ctx.monitor_manager.register_process_monitor(id, monitor.EdgeMonitor(self))

    def solve_edge(self, edge):
        """Solve given edge. This will sleep current process for
        time based on environment and solve edge.

        :param: edge: edge
        :type: Edge
        :return: Simpy event
        :rtype: event
        """
        gs = self.ctx.graph_stats
        gs.discover_edge(edge, self)
        self.fire("edge_discovered",
                  self.ctx.env.now,
                  self.id,
                  edge.get_time(),
                  edge.get_label(),
                  edge.get_source().get_id(),
                  edge.get_target().get_id())

        def edge_gen():
            calculating_time = self.calculate_edge_time(edge)
            yield self.wait(calculating_time)
            gs.calculate_edge(edge, self)
            self.fire("edge_calculated",
                      self.ctx.env.now,
                      self.id,
                      edge.get_time(),
                      calculating_time,
                      edge.get_label(),
                      edge.get_source().get_id(),
                      edge.get_target().get_id())

        return self.ctx.env.process(edge_gen())

    def init_monitor_callbacks(self):
        Process.init_monitor_callbacks(self)
        mm = self.ctx.monitor_manager
        mm.add_process_callback("edge_discovered", self.id, self)
        mm.add_process_callback("edge_calculated", self.id, self)

    def calculate_edge_time(self, edge):
        """
        Calculate time for computing given edge.

        :param: edge: edge
        :type: Edge
        :return: time
        :rtype: int
        """
        pr_model = self.ctx.process_model
        return pr_model.evaluate_time(self.id, edge)


class StorageProcess(GraphProcess):
    """
    Storage process which has internal storage for saving nodes of graph.

    :param: storage: storage
    :type: Storage
    """
    def __init__(self, id, name, ctx, storage):
        GraphProcess.__init__(self, id, name, ctx)
        self.storage = storage
        ctx.monitor_manager.register_process_monitor(id, monitor.StorageMonitor(self))

    def get_used_memory(self):
        return self.storage.get_size()

    def notify_storage_change(self):
        """
        Notify storage when change occur.
        """
        self.storage.notify_change()

    def on_async_receive(self, msg):
        self.storage.put_item(msg.data)

    def init_monitor_callbacks(self):
        GraphProcess.init_monitor_callbacks(self)
        mm = self.ctx.monitor_manager
        mm.add_process_callback("push", self.id, self.storage)
        mm.add_process_callback("pop", self.id, self.storage)
        mm.add_process_callback("changed", self.id, self.storage)


class Message():
    """
    Message structure used for sending messages through processes.

    :param: data: data of message
    :type: Object
    :param: source: id of process which send this message
    :type: int
    :param: target: id of process which should receive message
    :type: int
    :param: tag: tag for message
    :type: str
    :param: size: size of message
    :type: int
    """
    def __init__(self, data, source, target, tag, size):
        self.data = data
        self.target = target
        self.source = source
        self.tag = tag
        self.size = size


class Communicator(EventSource):
    """
    Communicator for communication between processes.

    :param: process: process
    :type: Process
    """
    def __init__(self, process):
        EventSource.__init__(self)
        self.register_event("send")
        self.register_event("receive")
        self.register_event("async_send")
        self.register_event("async_receive")
        self.process = process
        self._msg_store = simpy.FilterStore(process.ctx.env)
        self.rec = True

    def async_send(self, data, target, tag = None, size = 1):
        """
        Asynchronous send message to other process.

        :param: data: data for other process
        :type: Object
        :param: target: id of target process
        :type: int
        :param: tag: tag of message
        :type: str
        :param: size: size of message
        :type: int
        :return: Simpy event
        :rtype: event
        """
        ctx = self.process.ctx
        msg = Message(data, self.process.id, target, tag, size)

        def asend_gen():
            send_time  = self.calculate_send_time(msg)
            self.fire("async_send", msg, send_time)
            yield self.process.wait(send_time)
            target_process = ctx.processes[target]
            target_process.communicator._async_receive(msg)

        return ctx.env.process(asend_gen())

    def _async_receive(self, data):
        self.fire("async_receive", data)
        self.process.notify()

    def _check_msg(self, m_source, m_tag, target, tag):
        if m_source == target:
            if tag is not None:
                return m_tag == tag
            return True
        return False

    def send(self, data, target, tag = None, size = 1):
        """
        Blocking send message to other process.
        Process will be wait after sending message until
        some process receive message and wake up this process.

        :param: data: data for message
        :type: Object
        :param: target: id of target process
        :type: int
        :param: tag: tag of message
        :type: str
        :param: size: size of message
        :type: int
        :return: Simpy event
        :rtype: event
        """
        ctx = self.process.ctx
        if target < 0 or target >= len(ctx.processes):
            raise Exception("Unknown target for message send")
        msg = Message(data, self.process.id, target, tag, size)

        def send_gen():
            send_time = self.calculate_send_time(msg)
            yield self.process.wait(send_time)
            target_process = ctx.processes[target]
            com = target_process.communicator
            evt = com._msg_store.put(msg)
            if evt.triggered:
                self.fire("send", evt.item, send_time)
            yield evt

        return ctx.env.process(send_gen())

    def receive(self, source = None, tag = None):
        """
        Blocking receive message from other processes.
        This will block proces until right message based on 'source'
        and 'tag' match. Then process will continue.

        :param: source: id of source process which send message
        :type: int
        :param: tag: tag of message
        :type: int
        :return: Simpy event
        :rtype: event
        """
        ctx = self.process.ctx
        if source and (source < 0 or source >= len(ctx.processes)):
            raise Exception("Unknown source for receive message")

        def match(msg):
            if source is None:
                return True
            return self._check_msg(msg.source, msg.tag, source, tag)

        evt = self._msg_store.get(match)
        if evt.triggered:
            self.fire("receive", evt.value)
        else:
            evt.callbacks.append(lambda e: self.fire("receive", evt.value))
        return evt

    def receive_now(self, source = None, tag = None):
        """
        Receive which can receive if 'source' is None
        messages from any other processes without exact match.
        Attribute 'source' can contain list of id eg. [1,2]. Then
        match will check this ids.

        If some message is available then message is returned
        otherwise None.


        :param: source: id of source process
        :type: int | list of int
        :param: tag: tag of message
        :type: str
        :return: message or None if message is available
        :rtype: Message | None
        """
        ctx = self.process.ctx

        def target_check(t):
            if t < 0 or t >= len(ctx.processes):
                raise Exception("Unknown source for receive message")

        def match(msg):
            return self._check_msg(msg.source, msg.tag, source, tag)

        def multi_match(msg):
            for s in source:
                m = self._check_msg(msg.source,
                                    msg.tag,
                                    s,
                                    None)
                if m:
                    return True
            return False

        def any_target(msg):
            return True

        if type(source) is list:
            for s in source:
                target_check(s)
            evt = self._msg_store.get(multi_match)
        elif source:
            evt = self._msg_store.get(match)
        else:
            evt = self._msg_store.get(any_target)

        if evt.triggered:
            return evt.value
        else:
            return None

    def get_n_messages(self, pids = None):
        """
        Returns count of messages on process if 'pids'
        is None. If 'pids' is list of ids of processes,
        then return sum of messages for theses proceses.

        :param: pids: list of processes ids
        :type: list of ids | None
        :return: count of messages
        :rtype: int
        """
        if pids is None:
            return len(self._msg_store.items)
        count = 0
        for msg in self._msg_store.items:
            if msg.source in pids:
                count += 1
        return count

    def calculate_send_time(self, msg):
        """
        Calculating required time for sending message
        to other process.

        :param: msg: message
        :type: Message
        :return: required time
        :rtype: int
        """
        network_model = self.process.ctx.network_model
        return network_model.evaluate_cost(msg)


class Clock(EventSource):
    """
    Clock containing time values for given process.

    :param: process: process
    :type: Process
    """
    def __init__(self, process):
        EventSource.__init__(self)
        self.register_event("time_stamp")
        self.register_event("step")
        self.process = process
        self.time = 0
        self.steps = 0

    def wait(self, time):
        self.fire("time_stamp", self.time, time)
        self.time += time

    def tick(self):
        self.fire("step", self.steps, self.steps + 1)
        self.steps += 1

    def get_time(self):
        """
        Returns time of process. This time means how long process worked.

        :return: time
        :rtype: float
        """
        return self.time

    def get_step(self):
        """
        Returns count of steps for process.

        :return: count of steps
        :rtype: int
        """
        return self.steps

    def get_simulation_time(self):
        """
        Returns time of simulations.

        :return: time of simulation
        :rtype: float
        """
        return self.process.ctx.env.now

    def get_waiting_time(self):
        """
        Returns time how long process slept.

        :return: time
        :rtype: float
        """
        return self.get_simulation_time() - self.get_time()


class Storage(EventSource):
    """
    Internal storage for saving nodes of graph.

    :param: process: process
    :type: Process
    """
    def __init__(self, process):
        EventSource.__init__(self)
        self.register_event("changed")
        self.register_event("push")
        self.register_event("pop")
        self.process = process
        self.peak = 0

    def put(self, value):
        sim_time = self.process.clock.get_simulation_time()
        self.put_item(value)
        self.fire("push", sim_time, self.get_size())
        self.fire("changed",
                  sim_time,
                  self.get_size())
        if self.get_size() > self.peak:
            self.peak = self.get_size()

    def get(self):
        sim_time = self.process.clock.get_simulation_time()
        item = self.get_item()
        self.fire("pop", sim_time, self.get_size())
        self.fire("changed",
                  sim_time,
                  self.get_size())
        return item

    def get_memory_peak(self):
        """
        Returns maximum of used memory on storage.

        :return: maximum memory on storage
        :rtype: int
        """
        return self.peak

    def get_size(self):
        """
        Abstract method returns size of storage.

        :return: size of storage
        :rtype: int
        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()

    def get_item(self):
        """
        Abstract method returns item from storage.

        :return: item from storage
        :rtype: Object
        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()

    def put_item(self, value):
        """
        Abstract method put item to storage.

        :raise NotImplementedError: must be implemented
        """
        raise NotImplementedError()


class QueueStorage(Storage):
    """
    Implementation of storage based on Queue (FIFO).
    """
    def __init__(self, process):
        Storage.__init__(self, process)
        self.container = deque()

    def put_item(self, val):
        self.container.append(val)

    def get_item(self):
        return self.container.popleft()

    def get_size(self):
        return len(self.container)


class StackStorage(Storage):
    """
    Implementation of storage based on Stack (LIFO).
    """
    def __init__(self, process):
        Storage.__init__(self, process)
        self.container = []

    def put_item(self, val):
        self.container.append(val)

    def get_item(self):
        return self.container.pop()

    def get_size(self):
        return len(self.container)

