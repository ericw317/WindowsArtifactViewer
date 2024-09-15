import os

# search for live registry existence
def search_live_registry(drive):
    hives = []  # hold hives found
    possible_hives = ["SYSTEM", "SOFTWARE", "SAM", "SECURITY", "DEFAULT"]  # hives to look for
    if "[root]" in os.listdir(drive):
        path = drive + "[root]\\Windows\\System32\\config"  # path to Windows registry hives
    else:
        path = drive + "Windows\\System32\\config"  # path to Windows registry hives

    # loop through path to search for registry hives
    if os.path.exists(path):
        for file in os.listdir(path):
            if file in possible_hives:
                return True
    return False
