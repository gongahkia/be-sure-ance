import os

def delete_json(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        pretty_print_green(f"JSON file has been deleted at filepath: {file_path}")
    else:
        pretty_print_red(f"No JSON file was found at filepath: {file_path}")
    return

def all_JSON_fields(json_object):
    fin = []
    for field_name in json_object:
        fin.append(field_name)
    return fin

def unique_JSON_fields(file_path):
    attributes_list = []
    all_attributes = set()
    with open(file_path, "r") as fhand:
        for line in fhand:
            entry = json.loads(line)
            attributes = set(entry.keys())
            all_attributes.update(attributes)
            attributes_list.append(attributes)
    return attributes_list
