
class GraphException(Exception):
    def __init__(self, graph_file):
        Exception.__init__(self, graph_file)

class VisibleGraphException(Exception):
    def __init__(self, graph_file):
        Exception.__init__(self, graph_file)

class ProjectException(Exception):
    def __init__(self, project_file):
        Exception.__init__(self, project_file)