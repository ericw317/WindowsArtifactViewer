from Registry import Registry
from CustomLibs import InputValidation as IV
from CustomLibs import time_conversion
from CustomLibs import list_functions
from CustomLibs.RegistryFunctions import SAM_functions as SAM
from CustomLibs.RegistryFunctions import SYSTEM_functions as SYSTEM
from CustomLibs.RegistryFunctions import SOFTWARE_functions as SOFTWARE
from CustomLibs.RegistryFunctions import amcache_functions as amcache
from CustomLibs.RegistryFunctions import NTUSER_functions as NTUSER
import os
import re
import subprocess
import shutil
import datetime

# global variables
NTUSER_profile_list = []
amcache_mount = False

# Function to recursively display keys and subkeys
def display_keys(key):
    for subkey in key.subkeys():
        print(f"Subkey: {subkey.name()}")

# returns latest shadow copy volume
def get_latest_shadow_copy():
    # run "vssadmin list shadows" command to list all shadow copies
    result = subprocess.run(['vssadmin', 'list', 'shadows'], stdout=subprocess.PIPE, text=True)

    # find all 'Shadow Copy Volume' paths
    shadow_copy_paths = re.findall(r'Shadow Copy Volume: (\\\\\?\\GLOBALROOT\\Device\\HarddiskVolumeShadowCopy\d+)',
                                   result.stdout)

    if shadow_copy_paths:
        latest_shadow_copy = shadow_copy_paths[-1]
        return latest_shadow_copy
    else:
        return None


# copy registry files
def copy_reg(drive, reg_file, specification=None):
    # make a copy of the registry file
    if drive.upper() != "C:\\":  # copying for mounted drives
        if "[root]" in os.listdir(drive):
            begin_source = drive + f"[root]\\"
        else:
            begin_source = drive

        if reg_file == 'sam' or reg_file == 'system' or reg_file == 'software':
            source = begin_source + f"Windows\\System32\\config\\{reg_file}"
            destination = os.path.join(os.getcwd(), f"{reg_file}_temp")
            shutil.copy(source, destination)
        elif reg_file == 'amcache.hve':
            source = begin_source + f"Windows\\appcompat\\Programs\\Amcache.hve"
            destination = os.path.join(os.getcwd(), f"{reg_file}_temp")
            shutil.copy(source, destination)
        elif reg_file == "NTUSER":
            source = begin_source + f"Users\\{specification}\\NTUSER.DAT"
            destination = os.path.join(os.getcwd(), f"{reg_file}_temp")
            shutil.copy(source, destination)
    else:  # copying for C drive
        if reg_file == 'sam' or reg_file == 'system' or reg_file == 'software':
            command = ["reg", "save", f"hklm\\{reg_file}", f"{reg_file}_temp"]
            try:
                result = subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
            except PermissionError as e:
                print("Error: Make sure you're running as administrator.")
        elif reg_file == 'amcache.hve.tmp':
            source = drive + "Windows\\appcompat\\Programs\\Amcache.hve.tmp"
            destination = os.path.join(os.getcwd(), "Amcache.hve.tmp_temp")
            shutil.copy(source, destination)
        elif reg_file == "NTUSER":
            print("C drive analysis still in development")
            '''
            latest_shadow_copy_path = get_latest_shadow_copy()  # get shadow copy path
            print(latest_shadow_copy_path)

            # link shadow copy
            link_shadow_copy = ["mklink", "/d", "CustomLibs\\shadow_copy", latest_shadow_copy_path]
            subprocess.run(link_shadow_copy, shell=True, check=True, stdout=subprocess.DEVNULL)
            '''




# search for registry hives
def list_live_registry_files(drive):
    hives = []  # hold hives found
    possible_hives = ["SYSTEM", "SOFTWARE", "SAM"]  # hives to look for
    if "[root]" in os.listdir(drive):
        path = drive + "[root]\\Windows\\System32\\config"  # path to Windows registry hives
        amchache_path = drive + "[root]\\Windows\\appcompat\\Programs\\Amcache.hve"  # amcache path
        global amcache_mount
        amcache_mount = True
        NTUSER_path = drive + "[root]\\Users"  # NTUSER.dat path
    else:
        path = drive + "Windows\\System32\\config"  # path to Windows registry hives
        amchache_path = drive + "Windows\\appcompat\\Programs\\Amcache.hve.tmp"  # amcache path
        NTUSER_path = drive + "Users"  # NTUSER.dat path

    # loop through path to search for main registry hives
    if os.path.exists(path):
        for file in os.listdir(path):
            if file in possible_hives:
                hives.append(file)

    # check for NTUSER.dat files
    NTUSER_files_exist = False
    exclusion_list = ["All Users", "Default", "Default User", "Public"]
    if os.path.exists(NTUSER_path):
        for username in os.listdir(NTUSER_path):
            full_path = os.path.join(NTUSER_path, username)
            if os.path.isdir(full_path) and username not in exclusion_list:
                full_user_path = os.path.join(full_path, "NTUSER.DAT")
                if os.path.exists(full_user_path):
                    NTUSER_profile_list.append(username)
                    NTUSER_files_exist = True
    if NTUSER_files_exist:
        hives.append("NTUSER.DAT")

    # check for Amcache
    if os.path.exists(amchache_path):
        hives.append("Amcache.hve")

    if hives is not None:
        return hives
    else:
        return None

def parse_registry(drive):
    # display all available registry hives
    hives = list_live_registry_files(drive)
    print("\nSelect a registry hive to analyze:\n------------")
    for index, hive in enumerate(hives):
        print(f"{index + 1}: {hive}")

    # prompt user on hive to analyze
    hive_selection = (IV.int_between_numbers("", 1, len(hives))) - 1

    if hives[hive_selection] == "SAM":
        parse_SAM(drive)
    elif hives[hive_selection] == "SYSTEM":
        parse_SYSTEM(drive)
    elif hives[hive_selection] == "SOFTWARE":
        parse_SOFTWARE(drive)
    elif hives[hive_selection] == "Amcache.hve":
        parse_amcache(drive)
    elif hives[hive_selection] == "NTUSER.DAT":
        parse_NTUSER(drive)


# parses the same file
def parse_SAM(drive):
    # make a copy of the SAM file and load it up
    if not os.path.exists("sam_temp"):
        copy_reg(drive, "sam")
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
                     "Name": SAM.get_name(reg, RID),
                     "Internet Username": SAM.get_internet_username(reg, RID),
                     "Creation Date": key.timestamp()}
        user_data.append(user_dict)

    # output the data
    for users in user_data:
        print(f"Username: {users['Username']}\n"
              f"RID: {users['RID']}\n"
              f"Name: {users['Name']}\n"
              f"Internet Username: {users['Internet Username']}\n"
              f"Creation Date: {users['Creation Date']}\n")
        print("------------------------------\n")

    os.remove("sam_temp")  # remove reg copy

# parse the system registry
def parse_SYSTEM(drive):
    # copy system registry and load it up
    if not os.path.exists("system_temp"):
        copy_reg(drive, "system")
    reg = Registry.Registry("system_temp")

    # get SYSTEM info
    computer_name = SYSTEM.get_computer_name(reg)
    time_zone = SYSTEM.get_time_zone(reg)
    connected_USB_devices = SYSTEM.get_USB_devices(reg)
    connected_USB_storage = SYSTEM.get_USB_storage(reg)

    # print SYSTEM info
    print(f"Computer Name: {computer_name}")
    print(f"Time Zone: {time_zone}")
    print("Connected USB Devices:")
    for device in connected_USB_devices:
        print(f"    {device}")
    print("Connected USB Storage Devices:")
    for device in connected_USB_storage:
        print(f"    {device}")

    os.remove("system_temp")  # remove system copy

# parse the SOFTWARE registry
def parse_SOFTWARE(drive):
    # copy software registry and load it up
    if not os.path.exists("software_temp"):
        copy_reg(drive, "software")
    reg = Registry.Registry("software_temp")

    # get SOFTWARE info
    initial_os = SOFTWARE.get_initial_OS(reg)
    registered_owner = SOFTWARE.get_registered_owner(reg)
    install_time = SOFTWARE.get_install_time(reg)
    network_cards = SOFTWARE.get_network_cards(reg)
    network_history = SOFTWARE.get_networks_connected_to(reg)
    persistent_programs = SOFTWARE.get_persistent_programs(reg)

    # print info
    print(f"Initial OS: {initial_os}")
    print(f"Registered Owner: {registered_owner}")
    if install_time is not None:
        print(f"Install Time: {time_conversion.filetime_convert(install_time)}")
    print(f"\nNetwork Cards: {list_functions.print_list(network_cards)}")
    print(f"\nNetwork List: {list_functions.print_list(network_history)}")
    print(f"\nPersistent Programs: {list_functions.print_list(persistent_programs)}")

    os.remove("software_temp")  # remove software copy

# parse amcache
def parse_amcache(drive):
    # copy amcache hive and load it up
    if not amcache_mount:
        if not os.path.exists("amcache.hve.tmp_temp"):
            copy_reg(drive, "amcache.hve.tmp")
        reg = Registry.Registry("amcache.hve.tmp_temp")
    else:
        if not os.path.exists("amcache.hve_temp"):
            copy_reg(drive, "amcache.hve")
        reg = Registry.Registry("amcache.hve_temp")

    # get amcache info
    recent_installations = amcache.get_recent_installations(reg)

    # catch errors
    if recent_installations is None:
        print("Unable to parse")
        return 0

    # get additional info
    recent_installations_num = IV.int_between_numbers("How many of the most recently installed applications do you want to display?\n",
                                                      1, len(recent_installations))

    # print amcache info
    print(f"{recent_installations_num} Most Recently Installed Applications:")
    for application in recent_installations[:recent_installations_num]:
        print(application)

    if not amcache_mount:
        os.remove("amcache.hve.tmp_temp")  # remove amcache.hve copy
    else:
        os.remove("amcache.hve_temp")  # remove amcache.hve copy

# parse NTUSER.DAT
def parse_NTUSER(drive):
    # prompt user to select NTUSER.DAT file
    print("Select NTUSER.DAT file to analyze:")
    for index, user in enumerate(NTUSER_profile_list):
        print(f"{index + 1}: {user}")

    # prompt user selection
    NTUSER_selection = IV.int_between_numbers("", 1, len(NTUSER_profile_list)) - 1
    NTUSER_selection = NTUSER_profile_list[NTUSER_selection]

    # copy the registry file
    if not os.path.exists("NTUSER_temp"):
        copy_reg(drive, "NTUSER", NTUSER_selection)

    if drive != "C:\\":
        reg = Registry.Registry("NTUSER_temp")

        while True:
            # get info
            recent_docs = NTUSER.get_recent_docs(reg)
            execution_history = NTUSER.get_execution_history(reg)

            # display info
            print(f"\nRecent Documents:\n----------------{list_functions.print_list(recent_docs)}\n")
            print(f"\nProgram Execution History:\n----------------{list_functions.print_list(execution_history)}\n")

            # prompt on continuing or going back
            continuation = IV.int_between_numbers("Continue?\n"
                                                  f"1) Analyze more NTUSER.DAT details for {NTUSER_selection}\n"
                                                  f"2) Go back\n", 1, 2)

            if continuation == 2:
                break

        os.remove("NTUSER_temp")  # remove registry copy
