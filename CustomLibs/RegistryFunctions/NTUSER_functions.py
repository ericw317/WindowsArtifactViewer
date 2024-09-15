from CustomLibs import InputValidation as IV
import re

def display_keys(key):
    for subkey in key.subkeys():
        print(f"Subkey: {subkey.name()}")

def is_int_string(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def get_recent_docs(reg):
    recent_docs = []
    file_type_list = []
    key = reg.open("Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs")

    # display file types found
    print("File Types Found:\n----------")
    for subkey in key.subkeys():
        print(subkey.name())
        file_type_list.append(subkey.name())

    # prompt user on which type to analyze
    file_type = IV.string_match("\nEnter the file type to analyze recent docs: ", file_type_list)
    key = reg.open(f"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs\\{file_type}")

    for value in key.values():
        if is_int_string(value.name()):
            file_data = value.raw_data().decode('utf-16le', errors='ignore').rstrip('\x00')  # decode value
            file_name = file_data.split('\x00')[0]  # parse relevant data
            recent_docs.append(file_name)

    return recent_docs

# get execution history
def get_execution_history(reg):
    guid_pattern = r'\{[0-9A-Fa-f\-]{36}\}'
    execution_list = []
    key = reg.open("Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist")

    for subkey_x in key.subkeys():
        for subkey_y in subkey_x.subkeys():
            for value in subkey_y.values():
                program_data = value.raw_data().decode('utf-16le', errors='ignore').rstrip('\x00')  # decode value
                filtered_data = re.sub(guid_pattern, '', program_data)  # filter guid pattern
                filtered_data = re.sub(r'[^\x20-\x7E]+', '', filtered_data)  # filter unreadable characters
                if filtered_data != "":
                    execution_list.append(filtered_data)

    return execution_list