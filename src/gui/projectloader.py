from xml.etree.cElementTree import Element, SubElement, parse
from misc import utils
from gui.project import Project


class ProjectLoader():

    @staticmethod
    def create_empty_project(filename, name):
        project = Project(filename, name)
        ProjectLoader.save(project)
        return project

    @staticmethod
    def load_project(filename, error_callback = None):
        tree = parse(filename);
        root = tree.getroot()
        project_name = root.get("name")
        files_node = root.find("files")
        files_nodes = files_node.findall("file")

        project = Project(filename, project_name)
        if error_callback:
            project.connect("error", error_callback)

        for file_el in files_nodes:
            file_path = file_el.get("path")
            if file_path:
                project.add_file(file_path)

        return project

    @staticmethod
    def save_project(project):
        root = Element("project")
        root.set("name", project.get_name())
        files_node = SubElement(root, "files")
        for filename in project.get_files():
            f_node = SubElement(files_node, "file")
            f_node.set("path", filename)

        with open(project.get_file(), "w") as f:
            f.write(utils.get_pretty_xml(root))
            f.flush()
