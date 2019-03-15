from dataclasses import dataclass, field, fields
from typing import List
import xml.etree.ElementTree as ET

@dataclass
class Node:
    seq: int
    type: int

    @classmethod
    def tree_from_xml(cls, node):
        name = node.tag
        for cls in cls.__subclasses__():
            if cls.__name__.upper() == name:
                return cls.node_from_xml(node)

    @classmethod
    def node_from_xml(cls, node, **kwargs):
        fieldargs = {f.name: node.attrib.get(f.name.upper()) for f in fields(cls)}
        fieldargs['seq'] = int(fieldargs['seq'])
        fieldargs['type'] = int(fieldargs['type'])
        fieldargs.update(kwargs)
        return cls(**fieldargs)

@dataclass
class BoolOp(Node):
    boolop: str
    operands: List[Node] = field(default_factory=list)

    def __str__(self):
        joined = f' {self.boolop} '.join(map(str, self.operands))
        return f'({joined})'

    @classmethod
    def node_from_xml(cls, node):
        operands = (Node.tree_from_xml(child) for child in node)
        return super().node_from_xml(node, operands=[op for op in operands if op])

@dataclass
class Fragment(Node):
    func1: str
    func2: str
    nullaction: str
    op: str
    prop1: str
    prop2: str

    def __str__(self):
        return f'{self.func1}({self.prop1}) {self.op} {self.func2}({self.prop2})'


tree = ET.parse('xml_files/test_1.xml')
rules = []


def remove_value(listOfDicts, key):
    for subVal in listOfDicts:
        if key in subVal:
            del subVal[key]

def get_children(parent):

    return [child for child in parent if "ACTION" not in child.tag]


def get_parent_children_mapping(tree):
    return { parent: get_children(parent) for parent in tree.iter() if "ACTION" not in parent.tag }


def rule_parser():
    for movie in tree.findall("MODEL/RULE"):

        if movie.findall("./ACTION/ACTIONITEM/[@max='1']") and movie.findall("./ACTION/ACTIONITEM/[@min='0']") and movie.findall("./ACTION/ACTIONITEM/[@qty='1']"):
            print(movie.attrib['NAME'])
            bool_op = movie.find("BOOLOP")
            rule = Node.tree_from_xml(bool_op)
            rules.append("{0}".format(rule))
            print(rule)

    return rules


print(rule_parser())


