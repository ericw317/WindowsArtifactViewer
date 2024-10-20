from CustomLibs import list_functions
from CustomLibs import InputValidation as IV
from CustomLibs import time_conversion
from CustomLibs import artifact_search as AS
import sqlite3
import re
import shutil
import os

def extract_username(path, external=False):
    if not external:
        match = re.search(r'C:\\Users\\([^\\]+)\\AppData', path)
    else:
        match = re.search(r'[A-Za-z]:\\[^\\]+\\Users\\([^\\]+)\\AppData', path)

    if match:
        return match.group(1)
    return None

def collect_history(history_path, firefox=False):
    # connect to sqlite3 database
    conn = sqlite3.connect(history_path)
    cursor = conn.cursor()

    # query history data
    if not firefox:
        cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC")
    else:
        cursor.execute("""
            SELECT 
                moz_places.url, 
                moz_places.title, 
                moz_places.visit_count, 
                moz_historyvisits.visit_date 
            FROM 
                moz_places 
            JOIN 
                moz_historyvisits 
            ON 
                moz_places.id = moz_historyvisits.place_id 
            ORDER BY 
                moz_historyvisits.visit_date DESC
        """)
    history = cursor.fetchall()

    # close connection
    conn.close()

    return history

def parse_history(history_files, external=False):
    # collect all users
    user_list = []
    for element in history_files:
        if not external:
            user_name = extract_username(element)
        else:
            user_name = extract_username(element, external=True)
        if user_name is not None and user_name not in user_list:
            user_list.append(user_name)

    # prompt user to select username
    selected_user = IV.int_between_numbers(f"Select a user: {list_functions.print_list_numbered(user_list)}\n",
                                           1, len(user_list))
    selected_user = user_list[selected_user - 1]

    # collect list of all available browsers for selected_user
    browsers = []
    for element in history_files:
        if "Chrome" in element and selected_user in element:
            browsers.append("Chrome")
        elif "Edge" in element and selected_user in element:
            browsers.append("Edge")
        elif "Brave" in element and selected_user in element:
            browsers.append("Brave")
        elif "Firefox" in element and selected_user in element:
            browsers.append("Firefox")

    # prompt user on browser selection
    browser_selection = IV.int_between_numbers(f"\nSelect which browser history to view: {list_functions.print_list_numbered(browsers)}\n",
                                               1, len(browsers))
    browser_selection = browsers[browser_selection - 1]

    # grab browser history path
    history_path = ""
    for element in history_files:
        if browser_selection in element and selected_user in element:
            history_path = element
            break

    # parse history
    if "Firefox" not in history_path:
        if not external:
            history_data = collect_history(history_path)
        else:
            os.mkdir("history_temp_dir")  # create temp dir for processing
            shutil.copy(history_path, "history_temp_dir\\history_temp")  # copy history file to temp dir
            history_data = collect_history("history_temp_dir\\history_temp")  # process history file
            shutil.rmtree("history_temp_dir")
    else:
        if not external:
            history_data = collect_history(history_path, firefox=True)
        else:
            os.mkdir("history_temp_dir")  # create temp dir for processing
            shutil.copy(history_path, "history_temp_dir\\history_temp")  # copy history file to temp dir
            history_data = collect_history("history_temp_dir\\history_temp", firefox=True)  # process history file
            shutil.rmtree("history_temp_dir")

    # prompt user on how many entries to display
    display_selection = IV.int_between_numbers("How many entries would you like to display?\n",
                                               1, len(history_data))

    # get URL lengths for formatting
    longest_URL = 0
    for URL, _, _, _ in history_data[:display_selection]:
        if len(URL) > longest_URL:
            longest_URL = len(URL)

    # set spacing size
    if longest_URL > 30:
        spacing = longest_URL
    else:
        spacing = 30

    # display history entries
    print(f"{'URL':<{spacing}} | {'Title':<{spacing}} | {'Visit Count':<{spacing}} | {'Last Visit':<{spacing}}")
    print("-" * (spacing * 4))
    for entry in history_data[:display_selection]:
        try:
            if "Firefox" not in history_path:
                print(f"{entry[0]:<{spacing}} | {entry[1]:<{spacing}} | {entry[2]:<{spacing}} | "
                      f"{time_conversion.convert_windows_epoch(entry[3])}")
            else:
                print(f"{entry[0]:<{spacing}} | {entry[1]:<{spacing}} | {entry[2]:<{spacing}} | "
                      f"{time_conversion.convert_unix_epoch_microseconds(entry[3])}")
        except Exception as e:
            continue

# search for valid history files
def search_internet_history(drive):
    # function for firefox path
    def get_firefox_path(username):
        firefox_profiles_path = f"{drive}Users\\{username}\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles"
        if os.path.exists(firefox_profiles_path):
            for folder in os.listdir(firefox_profiles_path):
                if folder.endswith(".default-release"):
                    full_path = f"{firefox_profiles_path}\\{folder}\\places.sqlite"
                    return full_path
        return None

    def database_not_empty(file_path, table_name):
        try:
            # connect to SQLite database
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()

            # query to check if there are any records in the table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]

            # close connection
            conn.close()

            return count > 0  # return True if greater than 0 records exist
        except sqlite3.DatabaseError:
            return False

    # initialize user list and history file locations
    user_list = AS.get_user_list(drive)
    history_locations = {
        "chrome": f"{drive}Users\\[user_name]\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History",
        "edge": f"{drive}Users\\[user_name]\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History",
        "brave": f"{drive}Users\\[user_name]\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Default\\History"
    }
    found_paths = []

    # change locations if mounted drive has been selected
    if "[root]" in os.listdir(drive):
        for key in history_locations:
            history_locations[key] = history_locations[key].replace(f"{drive}Users\\", f"{drive}[root]\\Users\\")

    # search Chromium browser locations
    if "[root]" not in os.listdir(drive):
        for user in user_list:
            for browser in history_locations:
                current_location = history_locations[browser].replace("[user_name]", user)
                if os.path.exists(current_location) and database_not_empty(current_location, "urls"):
                    found_paths.append(current_location)
    else:
        os.mkdir("temp_history_directory")  # make temporary directory for history files
        for user in user_list:
            for browser in history_locations:
                current_location = history_locations[browser].replace("[user_name]", user)
                if os.path.exists(current_location):
                    shutil.copy(current_location, "temp_history_directory\\temp_history_file")
                    if os.path.exists(current_location) and database_not_empty("temp_history_directory\\temp_history_file", "urls"):
                        found_paths.append(current_location)
                    os.remove("temp_history_directory\\temp_history_file")
        os.rmdir("temp_history_directory")

    # search firefox
    if "[root]" not in os.listdir(drive):
        for user in user_list:
            firefox_history_path = get_firefox_path(user)
            if firefox_history_path is not None and database_not_empty(firefox_history_path, "moz_places"):
                found_paths.append(firefox_history_path)
    else:
        for user in user_list:
            firefox_history_path = get_firefox_path(user)
            if os.path.exists(str(firefox_history_path)):
                os.mkdir("firefox_temp")
                shutil.copy(firefox_history_path, "firefox_temp\\history_temp")
                if firefox_history_path is not None and database_not_empty("firefox_temp\\history_temp", "moz_places"):
                    found_paths.append(firefox_history_path)
                shutil.rmtree("firefox_temp")

    return found_paths

def main(drive):
    # initialize artifacts and locations
    history_paths = search_internet_history(drive)
    internet_artifacts = []

    # check for history
    if len(history_paths) > 0:
        internet_artifacts.append("History")

    # prompt user on artifact to analyze
    artifact_selection = IV.int_between_numbers(f"\nSelect an internet artifact to analyze: {list_functions.print_list_numbered(internet_artifacts)}\n",
                                                0, len(internet_artifacts))
    artifact_selection = internet_artifacts[artifact_selection - 1]

    if artifact_selection == "History":
        if drive == "C:\\":
            parse_history(history_paths)
        else:
            parse_history(history_paths, external=True)