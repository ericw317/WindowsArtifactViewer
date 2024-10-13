from CustomLibs import list_functions
from CustomLibs import InputValidation as IV
from CustomLibs import artifact_search as AS
import os
import time
import shutil
from tempfile import mkdtemp

def get_metadata(file_path):
    creation_time = time.ctime(os.path.getctime(file_path))
    mod_time = time.ctime(os.path.getmtime(file_path))
    return [creation_time, mod_time]

def parse_recent(user_list, drive):
    # prompt user selection
    print(f"\nSelect a user account:{list_functions.print_list_numbered(user_list)}")
    selection_num = IV.int_between_numbers("", 1, len(user_list))
    selected_user = user_list[selection_num - 1]

    # set path to recent items and get number of files
    recent_items_path = AS.set_path(f"Users\\{selected_user}\\AppData\\Roaming\\Microsoft\\Windows\\Recent", drive)
    item_number = len(os.listdir(recent_items_path))

    # put link files in a list and sort it by modification date
    lnk_list = []
    for file in os.listdir(recent_items_path):
        file_path = os.path.join(recent_items_path, file)
        lnk_list.append(file_path)
    lnk_list = list_functions.sort_files_by_modification(lnk_list)
    lnk_list.reverse()

    # prompt user on how many recent files to display
    item_number_selection = IV.int_between_numbers("Select number of recent items to display: ", 1, item_number)

    # create file name list for formatting
    file_name_list = []
    for file in lnk_list[:item_number_selection]:
        file_name_list.append(os.path.basename(file))

    # set spacing size for formatting
    longest_file_name = max(file_name_list, key=len)
    longest_length = len(longest_file_name)

    # set spacing size
    if longest_length <= 30:
        spacing = 30
    else:
        spacing = longest_length

    # print data
    print(f"{'File Name':<{spacing}} | {'Modification Date':<{spacing}} | {'Creation Date':<{spacing}}")
    print("-" * (spacing * 3))
    for file in lnk_list[:item_number_selection]:
        print(f"{os.path.basename(file):<{spacing}} | {get_metadata(file)[1]:<{spacing}} | {get_metadata(file)[0]:<{spacing}}")

def parse_recent_external(user_list, drive):
    # prompt user selection
    print(f"\nSelect a user account:{list_functions.print_list_numbered(user_list)}")
    selection_num = IV.int_between_numbers("", 1, len(user_list))
    selected_user = user_list[selection_num - 1]

    # set path to recent items and get number of files
    recent_items_path = AS.set_path(f"Users\\{selected_user}\\AppData\\Roaming\\Microsoft\\Windows\\Recent", drive)
    item_number = len(os.listdir(recent_items_path))

    # make temp directory for analysis
    current_directory = os.getcwd()
    temp_dir = mkdtemp(dir=current_directory)
    try:
        for file_name in os.listdir(recent_items_path):
            if file_name.endswith(".lnk"):
                full_file_name = os.path.join(recent_items_path, file_name)

                # Only copy if it's a file (skip directories or anything else)
                if os.path.isfile(full_file_name):
                    shutil.copy2(full_file_name, temp_dir)  # copy2 preserves metadata (modification times, etc.)
    except Exception as e:
        print(f"Error copying files: {e}")

    # put link files in a list and sort it by modification date
    lnk_list = []
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        lnk_list.append(file_path)
    lnk_list = list_functions.sort_files_by_modification(lnk_list)
    lnk_list.reverse()

    # prompt user on how many recent files to display
    item_number_selection = IV.int_between_numbers("Select number of recent items to display: ", 1, item_number)

    # create file name list for formatting
    file_name_list = []
    for file in lnk_list[:item_number_selection]:
        file_name_list.append(os.path.basename(file))

    # set spacing size for formatting
    longest_file_name = max(file_name_list, key=len)
    longest_length = len(longest_file_name)

    # set spacing size
    if longest_length <= 30:
        spacing = 30
    else:
        spacing = longest_length

    # print data
    print(f"{'File Name':<{spacing}} | {'Modification Date':<{spacing}} | {'Creation Date':<{spacing}}")
    print("-" * (spacing * 3))
    for file in lnk_list[:item_number_selection]:
        print(f"{os.path.basename(file):<{spacing}} | {get_metadata(file)[1]:<{spacing}} | {get_metadata(file)[0]:<{spacing}}")

    shutil.rmtree(temp_dir)
