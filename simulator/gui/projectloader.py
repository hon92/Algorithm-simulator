import os
from xml.etree.cElementTree import Element, SubElement, parse
from simulator.misc import utils
from project import Project


class ProjectLoader():

    @staticmethod
    def create_empty_project(filename, name):
        project = Project(filename, name)
        ProjectLoader.save_project(project)
        return project

    @staticmethod
    def load_project(filename):
        if not os.path.exists(filename):
            raise Exception("File '{0}' not exists".format(filename))

        tree = parse(filename);
        project_node = tree.getroot()
        if project_node.tag != "project":
            raise Exception("Project don't have 'project' root tag")

        project_name = project_node.get("name", "")
 
        files_node = project_node.find("files")

        files_nodes = []
        if files_node:
            files_nodes = files_node.findall("file")

        project = Project(filename, project_name)

        for file_el in files_nodes:
            file_path = file_el.get("path")
            if not file_path:
                raise Exception("Some file in project has unspecified 'path' attribute")
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

