import os
import sqlite3
import shutil

def set_path(artifact_path, drive):
    if "[root]" in os.listdir(drive):
        path = drive + f"[root]\\{artifact_path}"
    else:
        path = drive + artifact_path

    return path

# return list of all user profiles
def get_user_list(drive):
    exclusion_list = ["All Users", "Default", "Default User", "Public"]
    user_list = []
    users_path = set_path("Users", drive)

    for user in os.listdir(users_path):
        if os.path.isdir(os.path.join(users_path, user)) and user not in exclusion_list:
            user_list.append(user)

    return user_list


# search for live registry existence
def search_live_registry(drive):
    hives = []  # hold hives found
    possible_hives = ["SYSTEM", "SOFTWARE", "SAM", "SECURITY", "DEFAULT"]  # hives to look for
    path = set_path("Windows\\System32\\config", drive)

    # loop through path to search for registry hives
    if os.path.exists(path):
        for file in os.listdir(path):
            if file in possible_hives:
                return True
    return False

# search Recent Items
def search_recent_items(drive):
    user_list = []  # initialize user list
    user_list_output = []  # initialize output user list
    exclusion_list = ["All Users", "Default", "Default User", "Public"]
    user_path = set_path("Users", drive)
    files_found = False

    if os.path.exists(user_path):
        # add users to user list
        for user in os.listdir(user_path):
            if os.path.isdir(os.path.join(user_path, user)) and user not in exclusion_list:
                user_list.append(user)

        # check user paths for files in Recent folder
        for user in user_list:
            try:
                user_path = set_path(f"Users\\{user}\\AppData\\Roaming\\Microsoft\\Windows\\Recent", drive)
                if bool(os.listdir(user_path)):
                    user_list_output.append(user)
            except Exception:
                pass

        return user_list_output

    else:
        return "No***Users***Found"

# search for prefetch files
def search_prefetch(drive):
    prefetch_path = set_path("Windows\\Prefetch", drive)  # set path to prefetch files
    return os.path.exists(prefetch_path) and bool(os.listdir(prefetch_path))  # check if path and files exist

def search_internet(drive):
    # initialize user list and internet locations
    user_list = get_user_list(drive)
    internet_locations = {
        "chrome": f"{drive}Users\\[user_name]\\AppData\\Local\\Google\\Chrome",
        "edge": f"{drive}Users\\[user_name]\\AppData\\Local\\Microsoft\\Edge",
        "brave": f"{drive}Users\\[user_name]\\AppData\\Local\\BraveSoftware\\Brave-Browser",
        "firefox": f"{drive}Users\\[user_name]\\AppData\\Roaming\\Mozilla\\Firefox"
    }

    # change locations if mounted drive has been selected
    if "[root]" in os.listdir(drive):
        for key in internet_locations:
            internet_locations[key] = internet_locations[key].replace(f"{drive}Users\\", f"{drive}[root]\\Users\\")

    for user in user_list:
        for location in internet_locations:
            current_location = internet_locations[location].replace("[user_name]", user)
            if os.path.exists(current_location):
                return True

    return False
