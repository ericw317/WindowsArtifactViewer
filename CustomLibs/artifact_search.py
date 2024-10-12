import os

def set_path(artifact_path, drive):
    if "root" in os.listdir(drive):
        path = drive + f"[root]\\{artifact_path}"
    else:
        path = drive + artifact_path

    return path

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
