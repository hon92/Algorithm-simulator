from xml.etree.cElementTree import Element, SubElement, parse
from xml.etree import ElementTree
from xml.dom import minidom

def get_pretty_xml(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class ProjectLoader():
    def __init__(self, filename):
        self.filename = filename

    def load(self):
        tree = parse(self.filename);
        root = tree.getroot()
        project_name = root.get("name")
        files_node = root.find("files")
        files_nodes = files_node.findall("file")
        files = []
        for filename in files_nodes:
            path = filename.get("path")
            if path:
                files.append(path)
        return (project_name, files)

    def save(self, name, files):
        try:
            root = Element("project")
            root.set("name", name)
            files_node = SubElement(root, "files")
            for filename in files:
                f_node = SubElement(files_node, "file")
                f_node.set("path", filename)
        
            with open(self.filename, "w") as f:
                f.write(get_pretty_xml(root))
                f.flush()
            return True
        except Exception:
            return False
