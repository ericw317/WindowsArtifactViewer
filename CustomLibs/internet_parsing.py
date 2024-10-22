from CustomLibs import list_functions
from CustomLibs import InputValidation as IV
from CustomLibs import time_conversion
from CustomLibs import artifact_search as AS
import sqlite3
import re
import shutil
import os

##### GENERAL FUNCTIONS #####

# extract username from path
def extract_username(path, external=False):
    if not external:
        match = re.search(r'C:\\Users\\([^\\]+)\\AppData', path)
    else:
        match = re.search(r'[A-Za-z]:\\[^\\]+\\Users\\([^\\]+)\\AppData', path)

    if match:
        return match.group(1)
    return None


def database_not_empty(file_path, table_name):
    try:
        # connect to SQLite database
        conn = sqlite3.connect(file_path, timeout=0.1)
        cursor = conn.cursor()

        # query to check if there are any records in the table
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]

        # close connection
        conn.close()

        return count > 0  # return True if greater than 0 records exist
    except sqlite3.DatabaseError:
        return False

# initialize history paths
def initialize_artifact_paths(drive, artifact, firefox=False, username=""):
    if not firefox:
        history_locations = {
            "chrome": f"{drive}Users\\[user_name]\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\{artifact}",
            "edge": f"{drive}Users\\[user_name]\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\{artifact}",
            "brave": f"{drive}Users\\[user_name]\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Default\\{artifact}"
        }
        return history_locations
    else:
        firefox_profiles_path = f"{drive}Users\\{username}\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles"
        if os.path.exists(firefox_profiles_path):
            for folder in os.listdir(firefox_profiles_path):
                if folder.endswith(".default-release"):
                    full_firefox_path = f"{firefox_profiles_path}\\{folder}\\{artifact}"
                    return full_firefox_path
        return None

# set spacing
def set_spacing(artifact_data, display_selection, index, extra=False):
    longest_element = 0
    if not extra:
        for element in artifact_data[:display_selection]:
            if len(str(element[index])) > longest_element:
                longest_element = len(str(element[index]))
    else:
        for element in artifact_data[:display_selection]:
            if len(str(os.path.basename(element[index]))) > longest_element:
                longest_element = len(str(os.path.basename(element[index])))

    return longest_element

##### SEARCH FUNCTIONS #####

# search internet SQLite files
def search_internet_SQL(drive, chromium_artifact, chromium_table, firefox_artifact, firefox_table):
    # initialize user list and history file locations
    user_list = AS.get_user_list(drive)
    history_locations = initialize_artifact_paths(drive, chromium_artifact)
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
                if os.path.exists(current_location) and database_not_empty(current_location, chromium_table):
                    found_paths.append(current_location)
    else:
        os.mkdir("temp_history_directory")  # make temporary directory for history files
        for user in user_list:
            for browser in history_locations:
                current_location = history_locations[browser].replace("[user_name]", user)
                if os.path.exists(current_location):
                    shutil.copy(current_location, "temp_history_directory\\temp_history_file")
                    if os.path.exists(current_location) and database_not_empty("temp_history_directory\\temp_history_file", chromium_table):
                        found_paths.append(current_location)
                    os.remove("temp_history_directory\\temp_history_file")
        os.rmdir("temp_history_directory")

    # search firefox
    if "[root]" not in os.listdir(drive):
        for user in user_list:
            firefox_history_path = initialize_artifact_paths(drive, firefox_artifact, firefox=True, username=user)
            if firefox_history_path is not None and database_not_empty(firefox_history_path, firefox_table):
                found_paths.append(firefox_history_path)
    else:
        for user in user_list:
            firefox_history_path = initialize_artifact_paths(drive, firefox_artifact, firefox=True, username=user)
            if os.path.exists(str(firefox_history_path)):
                os.mkdir("firefox_temp")
                shutil.copy(firefox_history_path, "firefox_temp\\history_temp")
                if firefox_history_path is not None and database_not_empty("firefox_temp\\history_temp", firefox_table):
                    found_paths.append(firefox_history_path)
                shutil.rmtree("firefox_temp")

    return found_paths

##### PARSING FUNCTIONS #####

# collect internet history
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

# collect download history
def collect_downloads(downloads_path, firefox=False):
    # connect to sqlite3 database
    conn = sqlite3.connect(downloads_path)
    cursor = conn.cursor()

    # query downloads data
    if not firefox:
        cursor.execute("SELECT target_path, end_time, tab_url FROM downloads ORDER BY end_time DESC")
    else:
        cursor.execute("SELECT content, dateAdded FROM moz_annos WHERE content LIKE 'file://%' ORDER BY dateAdded DESC")

    downloads = cursor.fetchall()

    return downloads

# display history data
def display_history(artifact_data, display_selection, history_path):
    URL_spacing = set_spacing(artifact_data, display_selection, 0)
    title_spacing = set_spacing(artifact_data, display_selection, 1)
    visit_count_spacing = 11
    last_visit_spacing = 25
    horizontal_spacing = URL_spacing + title_spacing + (last_visit_spacing * 2)

    # display history entries
    print(f"{'Title':<{title_spacing}} | {'Last Visit':<{last_visit_spacing}} | {'Visit Count':<{visit_count_spacing}} | {'URL':<{URL_spacing}}")
    print("-" * horizontal_spacing)
    for entry in artifact_data[:display_selection]:
        title = entry[1]
        visit_count = entry[2]
        URL = entry[0]
        try:
            if "Firefox" not in history_path:
                last_visit_time = str(time_conversion.convert_windows_epoch(entry[3]))
                print(f"{title:<{title_spacing}} | {last_visit_time:<{last_visit_spacing}} | {visit_count:<{visit_count_spacing}}"
                      f" | {URL:<{URL_spacing}}")
            else:
                last_visit_time = str(time_conversion.convert_unix_epoch_microseconds(entry[3]))
                print(
                    f"{title:<{title_spacing}} | {last_visit_time:<{last_visit_spacing}} | {visit_count:<{visit_count_spacing}}"
                    f" | {URL:<{URL_spacing}}")
        except Exception as e:
            continue

# display downloads
def display_downloads(artifact_data, display_selection, downloads_path):
    file_name_space = set_spacing(artifact_data, display_selection, 0, extra=True)
    download_path_space = set_spacing(artifact_data, display_selection, 0)
    download_time_space = 25
    if "Firefox" not in downloads_path:
        download_url_space = set_spacing(artifact_data, display_selection, 2)
        horizontal_space = file_name_space + download_path_space + download_time_space + download_url_space
    else:
        horizontal_space = file_name_space + download_path_space + download_time_space

    # display downloads
    print(f"{'File Name':<{file_name_space}} | {'Download Path':<{download_path_space}} | {'Download Time':<{download_time_space}} | {'Download URL'}")
    print("-" * (horizontal_space * 4))
    if "Firefox" not in downloads_path:
        for entry in artifact_data[:display_selection]:
            try:
                file_name = os.path.basename(entry[0])
                target_path = entry[0]
                download_time = str(time_conversion.convert_windows_epoch(entry[1]))
                download_url = entry[2]

                print(f"{file_name:<{file_name_space}} | {target_path:<{download_path_space}} | {download_time:<{download_time_space}} | {download_url}")

            except Exception as e:
                continue
    else:
        for entry in artifact_data[:display_selection]:
            try:
                file_name = os.path.basename(entry[0])
                target_path = entry[0]
                download_time = str(time_conversion.convert_unix_epoch_microseconds(entry[1]))

                print(f"{file_name:<{file_name_space}} | {target_path:<{download_path_space}} | {download_time:<{download_time_space}} | ")

            except Exception as e:
                print(f"Error: {e}")
                continue

# artifact parsing
def parse_artifact(artifact_files, collection_func, artifact_type, external=False):
    # collect all users
    user_list = []
    for element in artifact_files:
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
    for element in artifact_files:
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
    artifact_path = ""
    for element in artifact_files:
        if browser_selection in element and selected_user in element:
            artifact_path = element
            break

    # parse history
    if "Firefox" not in artifact_path:
        if not external:
            artifact_data = collection_func(artifact_path)
        else:
            os.mkdir("temp_dir")  # create temp dir for processing
            shutil.copy(artifact_path, "temp_dir\\temp_file")  # copy history file to temp dir
            artifact_data = collection_func("temp_dir\\temp_file")  # process history file
            shutil.rmtree("temp_dir")
    else:
        if not external:
            artifact_data = collection_func(artifact_path, firefox=True)
        else:
            os.mkdir("temp_dir")  # create temp dir for processing
            shutil.copy(artifact_path, "temp_dir\\temp_file")  # copy history file to temp dir
            artifact_data = collection_func("temp_dir\\temp_file", firefox=True)  # process history file
            shutil.rmtree("temp_dir")

    # prompt user on how many entries to display
    display_selection = IV.int_between_numbers("How many entries would you like to display?\n",
                                               1, len(artifact_data))

    if artifact_type == "history":
        display_history(artifact_data, display_selection, artifact_path)
    elif artifact_type == "downloads":
        display_downloads(artifact_data, display_selection, artifact_path)

# main function
def main(drive):
    # initialize artifacts and locations
    history_paths = search_internet_SQL(drive, "History", "urls", "places.sqlite", "moz_places")
    downloads_paths = search_internet_SQL(drive, "History", "downloads", "places.sqlite", "moz_annos")
    internet_artifacts = []

    # check for history
    if len(history_paths) > 0:
        internet_artifacts.append("History")
    if len(downloads_paths) > 0:
        internet_artifacts.append("Downloads")

    # prompt user on artifact to analyze
    artifact_selection = IV.int_between_numbers(f"\nSelect an internet artifact to analyze: {list_functions.print_list_numbered(internet_artifacts)}\n",
                                                0, len(internet_artifacts))
    artifact_selection = internet_artifacts[artifact_selection - 1]

    if artifact_selection == "History":
        if drive == "C:\\":
            parse_artifact(history_paths, collect_history, "history")
        else:
            parse_artifact(history_paths, collect_history, "history", external=True)
    elif artifact_selection == "Downloads":
        if drive == "C:\\":
            parse_artifact(downloads_paths, collect_downloads, "downloads")
        else:
            parse_artifact(downloads_paths, collect_downloads, "downloads", external=True)