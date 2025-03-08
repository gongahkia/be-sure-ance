import glob
import os
import re
import json
import difflib
import hashlib
import requests
from lxml import etree
import networkx as nx
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xmldiff import main, formatting
from datetime import datetime, timedelta
from xml.parsers.expat import ExpatError
from xml.dom.minidom import parse, parseString

def delete_directory_files(target_directory):
    current_date = datetime.now().strftime("%d_%m_%Y")
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%d_%m_%Y")
    try:
        for filename in os.listdir(target_directory):
            file_path = os.path.join(target_directory, filename)
            if os.path.isfile(file_path):
                if (
                    current_date not in file_path
                    and yesterday_date not in file_path
                ):
                    os.remove(file_path)
                    pretty_print_green(f"Deleted file at the filepath: {file_path}")
                else:
                    pass
    except Exception as e:
        pretty_print_red(f"Error encountered: {e}")

def delete_files(target_filepath_array):
    files_to_delete_array = glob.glob(target_filepath_array)
    if files_to_delete_array:
        for filepath in files_to_delete_array:
            try:
                os.remove(filepath)
                pretty_print_green(f"Deleted file at filepath: {filepath}")
            except OSError as e:
                pretty_print_red(
                    f"Error deleting file at filepath: {filepath} due to {e}"
                )
    else:
        pretty_print_red(f"No files at filepath: {target_filepath} were found")

def fetch_raw_html(url):
    response = requests.get(url)
    response.raise_for_status()
    html_content = response.content.decode("utf-8")
    html_content = re.sub(r"<\?xml .*?\?>", "", html_content)
    html_content = re.sub(
        r'<use\s+xlink:href="[^"]*".*?>', "", html_content, flags=re.IGNORECASE
    )
    html_as_soup = BeautifulSoup(html_content, "html.parser")
    for script_or_style in html_as_soup(["style", "script"]):
        script_or_style.decompose()
    body_content = html_as_soup.find("body")
    return str(body_content) if body_content else ""

def generate_xml_hash(xml_content):
    hash_object = hashlib.sha256(xml_content.encode("utf-8"))
    return hash_object.hexdigest()

def normalize_xml(xml_content):

    root = ET.fromstring(xml_content)

    def strip_namespace(tag):
        return tag.split("}", 1)[-1] if "}" in tag else tag

    def traverse_and_build_structure(element):
        structure = f"<{strip_namespace(element.tag)}>"
        for child in element:
            structure += traverse_and_build_structure(child)
        structure += f"</{strip_namespace(element.tag)}>"
        return structure

    structure_only_xml = traverse_and_build_structure(root)
    return structure_only_xml

def compare_structural_similarity(xml1, xml2):

    def get_node_paths(element, parent_path=""):
        paths = []
        for child in element:
            path = f"{parent_path}/{child.tag}"
            paths.append(path)
            paths.extend(get_node_paths(child, path))
        return paths

    if xml1:
        try:
            root1 = ET.fromstring(xml1)
        except ET.ParseError as e:
            pretty_print_red(f"XML Parse Error: {e}")
            print(
                "Human validation required for the compare_structural_similarity() check!"
            )
            root1 = None

    if xml2:
        try:
            root2 = ET.fromstring(xml2)
        except ET.ParseError as e:
            pretty_print_red(f"XML Parse Error: {e}")
            print(
                "Human validation required for the compare_structural_similarity() check!"
            )
            root2 = None

    if root1 and root2:
        paths1, paths2 = get_node_paths(root1), get_node_paths(root2)
        unique_in_1 = set(paths1) - set(paths2)
        unique_in_2 = set(paths2) - set(paths1)
        return {
            "unique_in_xml1": unique_in_1,
            "unique_in_xml2": unique_in_2,
            "common_paths": set(paths1).intersection(paths2),
        }
    else:
        return {
            "unique_in_xml1": "Error",
            "unique_in_xml2": "Error",
            "common_paths": "Error",
        }

def validate_xml_with_schema(xml_file, schema_file):

    xml_doc = etree.parse(xml_file)
    with open(schema_file, "r") as schema_file_obj:
        schema_doc = etree.XML(schema_file_obj.read())
    schema = etree.XMLSchema(schema_doc)
    if schema.validate(xml_doc):
        return "XML is valid against the specified schema"
    else:
        return f"XML is not valid against the specified schema. Errors: {str(schema.error_log)}"

def calculate_levenshtein_distance(xml1, xml2):

    def get_tag_sequence(element):
        seq = [element.tag]
        for child in element:
            seq.extend(get_tag_sequence(child))
        return seq

    def levenshtein_distance(seq1, seq2):
        matcher = difflib.SequenceMatcher(None, seq1, seq2)
        return 1 - matcher.ratio()

    if xml1:
        try:
            tree1 = ET.fromstring(xml1)
        except ET.ParseError as e:
            pretty_print_red(f"XML Parse Error: {e}")
            print("Human validation required for the calculate_levenshtein_distance!")
            tree1 = None

    if xml2:
        try:
            tree2 = ET.fromstring(xml2)
        except ET.ParseError as e:
            pretty_print_red(f"XML Parse Error: {e}")
            print("Human validation required for the calculate_levenshtein_distance!")
            tree2 = None

    if tree1 and tree2:
        seq1 = get_tag_sequence(tree1)
        seq2 = get_tag_sequence(tree2)
        distance = levenshtein_distance(seq1, seq2)
        return distance
    else:
        return 0.0

def compare_dom(xml1, xml2):

    def compare_dom_elements(elem1, elem2):
        if elem1.tagName != elem2.tagName:
            return False
        if elem1.namespaceURI != elem2.namespaceURI:
            return False
        if elem1.attributes.keys() != elem2.attributes.keys():
            return False
        for key in elem1.attributes.keys():
            if elem1.attributes[key].value != elem2.attributes[key].value:
                return False
        elem1_children = [
            child for child in elem1.childNodes if child.nodeType == child.ELEMENT_NODE
        ]
        elem2_children = [
            child for child in elem2.childNodes if child.nodeType == child.ELEMENT_NODE
        ]
        if len(elem1_children) != len(elem2_children):
            return False
        for child1, child2 in zip(elem1_children, elem2_children):
            if not compare_dom_elements(child1, child2):
                return False
        return True

    if xml1:
        try:
            dom1 = parseString(xml1)
        except ExpatError as e:
            pretty_print_red(f"XML Parse Error: {e}")
            print("Human validation required for the compare_dom() check!")
            return None

    if xml2:
        try:
            dom2 = parseString(xml2)
        except ExpatError as e:
            pretty_print_red(f"XML Parse Error: {e}")
            print("Human validation required for the compare_dom() check!")
            return None

    if xml1 and xml1:
        root1 = dom1.documentElement
        root2 = dom2.documentElement
        return compare_dom_elements(root1, root2)
    else:
        return False