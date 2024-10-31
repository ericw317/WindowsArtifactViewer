import os
import sys
import shutil
import subprocess
from Registry import Registry
sys.path.append(os.path.abspath("CustomLibs"))  # needed for nested import
from RegistryFunctions import SAM_functions as SAM
from CustomLibs import InputValidation as IV
from CustomLibs import artifact_search as AS
from CustomLibs import time_conversion as TC
import struct
import datetime

# copy SAM hive
def copy_sam(drive):
    # make a copy of the registry file
    if drive.upper() != "C:\\":  # copying for mounted drives
        if "[root]" in os.listdir(drive):
            begin_source = drive + f"[root]\\"
        else:
            begin_source = drive

        source = begin_source + f"Windows\\System32\\config\\sam"
        destination = os.path.join(os.getcwd(), f"sam_temp")
        shutil.copy(source, destination)
    else:  # copying for C drive
        command = ["reg", "save", f"hklm\\sam", f"sam_temp"]
        try:
            result = subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
        except PermissionError as e:
            print("Error: Make sure you're running as administrator.")

# get RIDs
def get_RIDs(drive):
    # make a copy of the SAM file and load it up
    if not os.path.exists("sam_temp"):
        copy_sam(drive)
    reg = Registry.Registry("sam_temp")

    # initialize empty list to hold user data
    user_data = []

    # access a key
    key_path = r"SAM\Domains\Account\Users\Names"
    key = reg.open(key_path)

    # loop through each user and create a dictionary with their data
    for key in key.subkeys():
        RID = SAM.get_RID(reg, key.name())
        user_dict = {"Username": key.name(),
                     "RID": RID,
                     }
        user_data.append(user_dict)

    os.remove("sam_temp")  # remove reg copy
    return user_data

# parse $I files
def parse_i_file(file_path):
    with open(file_path, "rb") as f:
        # read and parse binary data
        header = struct.unpack("<Q", f.read(8))[0]
        file_size = struct.unpack("<Q", f.read(8))[0]
        deletion_timestamp = struct.unpack("<Q", f.read(8))[0]
        original_path_bytes = f.read()

        # convert data
        deletion_timestamp = TC.filetime_convert(deletion_timestamp)
        original_path = original_path_bytes.decode("utf-16le").rstrip("\x00")
        file_name = os.path.basename(original_path)

        metadata = [file_name, file_size, deletion_timestamp, original_path]
        return metadata

# convert file sizes
def convert_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 ** 2:
        size_kb = size_bytes / 1024
        return f"{size_kb:.2f} KB"
    elif size_bytes < 1024 ** 3:
        size_mb = size_bytes / (1024 ** 2)
        return f"{size_mb:.2f} MB"
    else:
        size_gb = size_bytes / (1024 ** 3)
        return f"{size_gb:.2f} GB"

# parse $Recycle.Bin
def parse_recycle_bin(drive):
    recycle_path = AS.set_path("$Recycle.Bin", drive)
    RID_list = get_RIDs(drive)
    recycle_folders = []

    # loop through $Recycle.Bin folders and display them along with the associated user
    print("$Recycle.Bin Folders:\n-------------------------")
    counter = 1
    for file in os.listdir(recycle_path):
        RID = file.split('-')[-1]
        for user in RID_list:
            if int(user['RID']) == int(RID):
                print(f"{counter}) ", end="")
                username = user['Username']
                recycle_folders.append(os.path.join(recycle_path, file))
                print(f"{file} ({user['Username']})")
                counter += 1
                break

    # prompt user to select folder
    selection = IV.int_between_numbers("", 1, len(recycle_folders))
    selection = recycle_folders[selection - 1]

    # spacing data
    size_space = 10
    date_space = 25
    identifier_space = 15

    # calculate file_name space
    name_space = 9
    for file in os.listdir(selection):
        if file.startswith("$I"):
            if len(parse_i_file(os.path.join(selection, file))[0]) > name_space:
                name_space = len(parse_i_file(os.path.join(selection, file))[0])

    horizontal_space = size_space + date_space + identifier_space + name_space + 50

    # display data
    print(f"{'File Name':<{name_space}} | {'Size':<{size_space}} | {'Deletion Date':<{date_space}} | "
          f"{'Identifier':<{identifier_space}} | Original Path")
    print("-" * horizontal_space)
    for file in os.listdir(selection):
        file_path = os.path.join(selection, file)
        if file.startswith("$I"):
            file_name = parse_i_file(file_path)[0]
            file_size = convert_file_size(parse_i_file(file_path)[1])
            deletion_date = parse_i_file(file_path)[2]
            identifier = file
            original_path = parse_i_file(file_path)[3]
            print(f"{file_name:<{name_space}} | {file_size:<{size_space}} | {str(deletion_date):<{date_space}} | "
                  f"{identifier:<{identifier_space}} | {original_path[2:]}")
            print("-" * horizontal_space)

