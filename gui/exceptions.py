
#graph file is corrupted
class GraphException(Exception):
    def __init__(self, graph_file):
        Exception.__init__(self, graph_file)

#visible graph file is corrupted
class VisibleGraphException(Exception):
    def __init__(self, graph_file):
        Exception.__init__(self, graph_file)

#project file is corrupted
class ProjectException(Exception):
    def __init__(self, project_file):
        Exception.__init__(self, project_file)

#existing graph file exception
class ExistingGraphException(Exception):
    def __init__(self, graph_file):
        Exception.__init__(self, graph_file)