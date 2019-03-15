import xml.etree.ElementTree as ET
from collections import defaultdict
import xlwt
from pathlib import Path
from  xlrd import open_workbook
from xlutils.copy import copy


def iter_xml_model_file():
    result = list(Path("xml_files").glob('**/*.xml'))
    for k in result:
        yield str(k)


def get_rule_name(tree):
    list_rules = []
    for movie in tree.findall("MODEL/RULE"):
        if movie.findall("./ACTION/ACTIONITEM/[@max='1']") and movie.findall("./ACTION/ACTIONITEM/[@min='0']") and movie.findall("./ACTION/ACTIONITEM/[@qty='1']"):
            list_rules.append(movie.attrib['NAME'])
    return list_rules

def etree_iter_path(node, tag=None, path=''):
    if tag == "*":
        tag = None
    if tag is None or node.tag == tag:
        yield node, path
    for child in node:
        if len(child.attrib) != 0 and 'NAME' in child.attrib:
            _child_path = '%s.%s' % (path, child.attrib['NAME'])
            for child, child_path in etree_iter_path(child, tag, path=_child_path):
                yield child, child_path



def rule_attached(root,model,tree):
    rule_item = defaultdict(list)
    count= 0
    count_rule = 0
    for i in get_rule_name(tree):
        count_rule += 1
        for elem in root.findall(".//*[@NAME='"+ i + "']..."):
            if elem.tag == 'ITEM' or elem.tag == 'CLASS':
                desc = (elem.find('LOCALES/LOCALE/DESCRIPTION')).text
                for elems, path in etree_iter_path(root):
                    if elems.tag == 'ITEM' and elems.attrib['NAME'] == elem.attrib['NAME']:
                            rule_item[i].append([model,path,elem.attrib['SKU'] , i])
                            count += 1

    return dict(rule_item)


def remove_value(listOfDicts, key):
    for subVal in listOfDicts:
        if key in subVal:
            del subVal[key]

def get_children(parent):
    for child in parent:
        if "ACTION" in child.tag:
            continue
        if 'BOOLOP' in child.attrib:
            yield child.attrib['BOOLOP']
        else:
            yield child.attrib


def get_parent_children_mapping(tree):
    return { parent: list(get_children(parent)) for parent in tree.iter() if "ACTION" not in parent.tag }


def rule_prop_attached(tree):
    boolop_count = 1
    frag_list = []
    entries = ['NULLACTION', 'SEQ', 'TYPE']
    pb_ignore = ["PB:SALES_TYPE", "PB:PRICELIST", "PB:SOURCE_SYSTEM", "_amEntitled", "._amEntitled","PB:COUNTRY"]
    prop_val_item_map = defaultdict(list)
    prop_item_rule_simple = defaultdict(list)
    rule_count = 1
    for movie in tree.findall("MODEL/RULE"):

        if movie.findall("./ACTION/ACTIONITEM/[@max='1']") and movie.findall("./ACTION/ACTIONITEM/[@min='0']") and movie.findall("./ACTION/ACTIONITEM/[@qty='1']"):
            #print(rule_count,movie.attrib['NAME'])
            rule_count += 1
            boolop_count += 1
            for parent, children in get_parent_children_mapping(movie).items():
                if children:
                    for vals in entries:
                        remove_value(children, vals)
                    if 'NAME' in parent.attrib:
                        pass

                    elif 'BOOLOP' in parent.attrib:
                        for j in children:
                            if isinstance(j,dict):
                                if j['PROP1'] not in pb_ignore:
                                    if j['FUNC1'] == 'value' and j['FUNC2'] == 'literal':
                                        prop_val_item_map[movie.attrib['NAME']].append(
                                            [j['FUNC1'], j['PROP1'], j['FUNC2'], j['PROP2']])
                                    for item in tree.findall(
                                            './/*PROPVAL[@VALUE="' + j['PROP2'] + '"][@NAME="' + j[
                                                'PROP1'] + '"]...'):
                                        if j['FUNC1'] == 'value' and j['FUNC2'] == 'literal':
                                            if item.attrib['SKU'] == None:
                                                continue
                                            #print(movie.attrib['NAME'],item.tag, item.attrib['SKU'], j['PROP1'], j['PROP2'])
                                            prop_item_rule_simple[movie.attrib['NAME']].append([j['PROP1']+"="+j['PROP2'],item.attrib['SKU']])

                    else:
                        pass

    return dict(prop_item_rule_simple)



def get_childrens(parent):
    for child in parent:
        if "LOCALES" not in child.tag and "ITEMRULE" not in child.tag:
            if child.tag == "PROPVAL":
                if 'VALUE' in child.attrib:
                    yield [child.attrib['NAME'],child.attrib['VALUE']]



def get_parent_children_mappings(tree):
    return { parent: list(get_childrens(parent)) for parent in tree.iter() if "LOCALES" not in parent.tag and "ITEMRULE" not in parent.tag and "LOCALE" not in parent.tag }


def default_sel(tree,root,model):
    prop_book = []
    for item in tree.findall(
            './/*PROPVAL[@NAME="UI: DEFAULT SELECTION"][@VALUE="yes"]...'):
        for elems, path in etree_iter_path(root):
            if elems.tag == 'ITEM' and elems.attrib['NAME'] == item.attrib['NAME']:
                prop_book.append([model,path, item.attrib['SKU'],"ITEM SELECTED BY DEFAULT",
                                  "UI: DEFAULT SELECTION:yes",""])

    return  prop_book


def update_rule_attached(root,model,tree):
    update_rule = rule_attached(root,model,tree)
    update_prop = rule_prop_attached(tree)
    for i in list(update_rule.keys()):
        if i not in list(update_prop.keys()) :
            del update_rule[i]

    del_key = (set(update_prop) - set(update_rule))
    for i in del_key:
        del update_prop[i]

    return update_rule,update_prop




def merge_all_output(rule_picked,rule_pick,selected_by_default):
    merge_l = []
    for k, k2 in zip(rule_picked,rule_pick):

        for i in rule_picked[k]:
            for j in rule_pick[k2]:
                merge_l.append(i + j)
    final_output = merge_l + selected_by_default
    return final_output




def ok_write(filename,merge_out):
    wob = open_workbook(filename)
    wos = wob.sheet_by_index(0)
    rowCount = wos.nrows
    wb = copy(wob)
    sheet = wb.get_sheet(0)
    for rownum, sublist in enumerate(merge_out):
            for colnum, value in enumerate(sublist):
                sheet.write(rownum + rowCount, colnum, value)
    wb.save(filename)
    print('Done!')



def main():
    file_model = list(iter_xml_model_file())
    for k in file_model:
        tree = ET.parse(k)
        root = tree.getroot()
        model = (root.find("MODEL")).attrib['NAME']
        default_sel(tree,root,model)
        rule_picked, rule_pick = update_rule_attached(root,model,tree)
        selected_by_default = default_sel(tree,root,model)
        # print(len(rule_picked),len(rule_pick))
        merge_out = merge_all_output(rule_picked, rule_pick, selected_by_default)
        # print(merge_out)
        my_file = Path("example.xls")
        filename = 'example.xls'
        output_headers = ["MODEL","PATH","ITEM_PICKED","RULE_NAME",
                          "PICKING_PROPERTY","PICKING_SKU"]

        if my_file.is_file():
            ok_write(filename,merge_out)
        else:
            wb = xlwt.Workbook()
            ws = wb.add_sheet('pick_rule_sheet')
            for j, t in enumerate(output_headers):
                ws.write(0, 0 + j, t)
                wb.save(filename)
                ok_write(filename,merge_out)


if __name__ == '__main__':
    main()
