from CustomLibs import list_functions
from CustomLibs import InputValidation as IV
from CustomLibs import time_conversion
from CustomLibs import artifact_search as AS
import sqlite3
import re
import shutil
import os
import json
import FireFoxDecrypt

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

# check if database is empty
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

# check if JSON file is empty
def json_not_empty(json_file):
    with open(json_file, 'r') as file:
        try:
            data = json.load(file)  # load json data

            # check if JSON object is empty
            if not data:
                return False
            else:
                return True
        except json.JSONDecodeError:
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
    if display_selection != 0:
        if not extra:
            for element in artifact_data[:display_selection]:
                if len(str(element[index])) > longest_element:
                    longest_element = len(str(element[index]))
        else:
            for element in artifact_data[:display_selection]:
                if len(str(os.path.basename(element[index]))) > longest_element:
                    longest_element = len(str(os.path.basename(element[index])))
    else:
        for element in artifact_data:
            if len(str(element[index])) > longest_element:
                longest_element = len(str(element[index]))

    return longest_element

##### SEARCH FUNCTIONS #####

# search internet SQLite files
# history_paths = search_internet_SQL(drive, "History", "urls", "places.sqlite", "moz_places")
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

# search login data
def search_logins(drive):
    # initialize user list and login data file locations
    user_list = AS.get_user_list(drive)
    logins_chromium_paths = initialize_artifact_paths(drive, "Login Data")
    found_paths = []

    # change locations if mounted drive has been selected
    if "[root]" in os.listdir(drive):
        for key in logins_chromium_paths:
            logins_chromium_paths[key] = logins_chromium_paths[key].replace(f"{drive}Users\\", f"{drive}[root]\\Users\\")

    # search Chromium browser locations
    if "[root]" not in os.listdir(drive):
        for user in user_list:
            for browser in logins_chromium_paths:
                current_location = logins_chromium_paths[browser].replace("[user_name]", user)
                if os.path.exists(current_location) and database_not_empty(current_location, "logins"):
                    found_paths.append(current_location)
    else:
        os.mkdir("temp_history_directory")  # make temporary directory for history files
        for user in user_list:
            for browser in logins_chromium_paths:
                current_location = logins_chromium_paths[browser].replace("[user_name]", user)
                if os.path.exists(current_location):
                    shutil.copy(current_location, "temp_history_directory\\temp_history_file")
                    if os.path.exists(current_location) and database_not_empty(
                            "temp_history_directory\\temp_history_file", "logins"):
                        found_paths.append(current_location)
                    os.remove("temp_history_directory\\temp_history_file")
        os.rmdir("temp_history_directory")

    # search firefox
    if "[root]" not in os.listdir(drive):
        for user in user_list:
            firefox_logins_path = initialize_artifact_paths(drive, "logins.json", firefox=True, username=user)
            if firefox_logins_path is not None and json_not_empty(firefox_logins_path):
                found_paths.append(firefox_logins_path)
    else:
        for user in user_list:
            firefox_logins_path = initialize_artifact_paths(drive, "logins.json", firefox=True, username=user)
            if os.path.exists(str(firefox_logins_path)):
                os.mkdir("firefox_temp")
                shutil.copy(firefox_logins_path, "firefox_temp\\history_temp")
                if firefox_logins_path is not None and json_not_empty("firefox_temp\\history_temp"):
                    found_paths.append(firefox_logins_path)
                shutil.rmtree("firefox_temp")

    return found_paths

# search bookmarks
def search_bookmarks(drive):
    # initialize user list and login data file locations
    user_list = AS.get_user_list(drive)
    bookmarks_chromium_paths = initialize_artifact_paths(drive, "Bookmarks")
    found_paths = []

    # change locations if mounted drive has been selected
    if "[root]" in os.listdir(drive):
        for key in bookmarks_chromium_paths:
            bookmarks_chromium_paths[key] = bookmarks_chromium_paths[key].replace(f"{drive}Users\\",
                                                                                  f"{drive}[root]\\Users\\")

    # search Chromium browser locations
    if "[root]" not in os.listdir(drive):
        for user in user_list:
            for browser in bookmarks_chromium_paths:
                current_location = bookmarks_chromium_paths[browser].replace("[user_name]", user)
                if os.path.exists(current_location) and json_not_empty(current_location):
                    found_paths.append(current_location)
    else:
        os.mkdir("temp_history_directory")  # make temporary directory for history files
        for user in user_list:
            for browser in bookmarks_chromium_paths:
                current_location = bookmarks_chromium_paths[browser].replace("[user_name]", user)
                if os.path.exists(current_location):
                    shutil.copy(current_location, "temp_history_directory\\temp_history_file")
                    if os.path.exists(current_location) and json_not_empty(current_location):
                        found_paths.append(current_location)
                    os.remove("temp_history_directory\\temp_history_file")
        os.rmdir("temp_history_directory")

    # search firefox
    if "[root]" not in os.listdir(drive):
        for user in user_list:
            firefox_logins_path = initialize_artifact_paths(drive, "places.sqlite", firefox=True, username=user)
            if firefox_logins_path is not None and database_not_empty(firefox_logins_path, "moz_bookmarks"):
                found_paths.append(firefox_logins_path)
    else:
        for user in user_list:
            firefox_logins_path = initialize_artifact_paths(drive, "places.sqlite", firefox=True, username=user)
            if os.path.exists(str(firefox_logins_path)):
                os.mkdir("firefox_temp")
                shutil.copy(firefox_logins_path, "firefox_temp\\history_temp")
                if firefox_logins_path is not None and database_not_empty("firefox_temp\\history_temp", "moz_bookmarks"):
                    found_paths.append(firefox_logins_path)
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

# collect login data
def collect_logins(logins_path, firefox=False):
    if not firefox:
        # connect to sqlite3 database
        conn = sqlite3.connect(logins_path)
        cursor = conn.cursor()

        # query login data
        cursor.execute("SELECT origin_url, username_value FROM logins")

        chromium_logins = cursor.fetchall()

        return chromium_logins

# collect bookmark data
def collect_bookmarks(bookmarks_path, firefox=False):
    if not firefox:
        with open(bookmarks_path, 'r') as json_file:
            data = json.load(json_file)

        roots = data['roots']
        other_bookmarks = roots['other']['children']
        bookmarks_data = []

        for bookmark in other_bookmarks:
            bookmarks_data.append([bookmark['name'], int(bookmark['date_added']), bookmark['url']])

        return bookmarks_data
    else:
        # connect to sqlite3 database
        conn = sqlite3.connect(bookmarks_path)
        cursor = conn.cursor()

        # query bookmarks data
        cursor.execute("SELECT title, dateAdded FROM moz_bookmarks")

        firefox_bookmarks = cursor.fetchall()

        return firefox_bookmarks


# display history data
def display_history(artifact_data, display_selection, history_path):
    URL_spacing = set_spacing(artifact_data, display_selection, 0)
    title_spacing = set_spacing(artifact_data, display_selection, 1)
    visit_count_spacing = 11
    last_visit_spacing = 25
    horizontal_spacing = URL_spacing + title_spacing + (last_visit_spacing * 2)
    if horizontal_spacing > 150:
        horizontal_spacing = 150

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
                print("-" * horizontal_spacing)
            else:
                last_visit_time = str(time_conversion.convert_unix_epoch_microseconds(entry[3]))
                print(
                    f"{title:<{title_spacing}} | {last_visit_time:<{last_visit_spacing}} | {visit_count:<{visit_count_spacing}}"
                    f" | {URL:<{URL_spacing}}")
                print("-" * horizontal_spacing)
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
        if horizontal_space > 150:
            horizontal_space = 150
    else:
        horizontal_space = file_name_space + download_path_space + download_time_space

    # display downloads
    print(f"{'File Name':<{file_name_space}} | {'Download Path':<{download_path_space}} | {'Download Time':<{download_time_space}} | {'Download URL'}")
    print("-" * horizontal_space)
    if "Firefox" not in downloads_path:
        for entry in artifact_data[:display_selection]:
            try:
                file_name = os.path.basename(entry[0])
                target_path = entry[0]
                download_time = str(time_conversion.convert_windows_epoch(entry[1]))
                download_url = entry[2]

                print(f"{file_name:<{file_name_space}} | {target_path:<{download_path_space}} | {download_time:<{download_time_space}} | {download_url}")
                print("-" * horizontal_space)
            except Exception as e:
                continue
    else:
        for entry in artifact_data[:display_selection]:
            try:
                file_name = os.path.basename(entry[0])
                target_path = entry[0]
                download_time = str(time_conversion.convert_unix_epoch_microseconds(entry[1]))

                print(f"{file_name:<{file_name_space}} | {target_path:<{download_path_space}} | {download_time:<{download_time_space}} | ")
                print("-" * horizontal_space)
            except Exception as e:
                print(f"Error: {e}")
                continue

# display login data
def display_logins(artifact_data, display_selection, logins_path):
    if "Firefox" not in logins_path:
        url_space = set_spacing(artifact_data, display_selection, 0)
        username_space = 8
        horizontal_space = url_space + username_space

        # display downloads
        print(f"{'URL':<{url_space}} | {'Username':<{username_space}}")
        print("-" * horizontal_space)

        for entry in artifact_data:
            try:
                url = entry[0]
                username = entry[1]

                print(f"{url:<{url_space}} | {username:<{username_space}}")
                print("-" * horizontal_space)
            except Exception as e:
                continue

# display firefox logins
def display_firefox_logins(firefox_logins_path):
    # decrypt firefox login data
    login_file = firefox_logins_path
    key_file = login_file.replace("logins.json", "key4.db")
    login_data = FireFoxDecrypt.DecryptLogins(login_file, key_file)

    # set spacing
    url_space = set_spacing(login_data, 0, "hostname")
    username_space = set_spacing(login_data, 0, "username")
    if username_space < 8:
        username_space = 8
    password_space = 16
    horizontal_space = url_space + username_space + password_space

    # display login data
    print(f"{'URL':<{url_space}} | {'Username':<{username_space}} | {'Password':<{password_space}}")
    print("-" * horizontal_space)
    for entry in login_data:
        print(f"{entry['hostname']:<{url_space}} | {entry['username']:<{username_space}} | {entry['password']:<{password_space}}")
        print("-" * horizontal_space)

# display bookmarks
def display_bookmarks(artifact_data, display_selection, bookmarks_path):
    if "Firefox" not in bookmarks_path:
        # set spacing
        name_space = set_spacing(artifact_data, display_selection, 0)
        date_space = 25
        url_space = set_spacing(artifact_data, display_selection, 2)
        horizontal_space = name_space + date_space + url_space

        # display bookmarks
        print(f"{'Bookmark':<{name_space}} | {'Date Added':<{date_space}} | {'URL':<{url_space}}")
        print("-" * horizontal_space)
        for bookmark in artifact_data:
            name = bookmark[0]
            date = str(time_conversion.convert_windows_epoch(bookmark[1]))
            url = bookmark[2]
            print(f"{name:<{name_space}} | {date:<{date_space}} | {url:<{url_space}}")
            print("-" * horizontal_space)
    else:
        # set spacing
        name_space = set_spacing(artifact_data, display_selection, 0)
        date_space = 25
        horizontal_space = name_space + date_space

        # display bookmarks
        print(f"{'Bookmark':<{name_space}} | {'Date Added':<{date_space}}")
        print("-" * horizontal_space)
        for bookmark in artifact_data:
            name = bookmark[0]
            date = str(time_conversion.convert_unix_epoch_microseconds(bookmark[1]))
            print(f"{name:<{name_space}} | {date:<{date_space}}")
            print("-" * horizontal_space)


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

    # switch to login parsing in the case of firefox login data
    if "Firefox" in artifact_path and artifact_type == "logins":
        try:
            display_firefox_logins(artifact_path)
        except Exception as e:
            print(f"Couldn't decrypt Firefox logins: {e}")
        return 0

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
    if artifact_type != "logins" and artifact_type != "bookmarks":
        display_selection = IV.int_between_numbers("How many entries would you like to display?\n",
                                                   1, len(artifact_data))

    if artifact_type == "history":
        display_history(artifact_data, display_selection, artifact_path)
    elif artifact_type == "downloads":
        display_downloads(artifact_data, display_selection, artifact_path)
    elif artifact_type == "logins":
        display_logins(artifact_data, 0, artifact_path)
    elif artifact_type == "bookmarks":
        display_bookmarks(artifact_data, 0, artifact_path)

# main function
def main(drive):
    # initialize artifacts and locations
    history_paths = search_internet_SQL(drive, "History", "urls", "places.sqlite", "moz_places")
    downloads_paths = search_internet_SQL(drive, "History", "downloads", "places.sqlite", "moz_annos")
    logins_paths = search_logins(drive)
    bookmarks_paths = search_bookmarks(drive)
    internet_artifacts = []

    # check for history
    if len(history_paths) > 0:
        internet_artifacts.append("History")
    if len(downloads_paths) > 0:
        internet_artifacts.append("Downloads")
    if len(bookmarks_paths) > 0:
        internet_artifacts.append("Bookmarks")
    if len(logins_paths) > 0:
        internet_artifacts.append("Logins")

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
    elif artifact_selection == "Bookmarks":
        if drive == "C:\\":
            parse_artifact(bookmarks_paths, collect_bookmarks, "bookmarks")
        else:
            parse_artifact(bookmarks_paths, collect_bookmarks, "bookmarks", external=True)
    elif artifact_selection == "Logins":
        if drive == "C:\\":
            parse_artifact(logins_paths, collect_logins, "logins")
        else:
            parse_artifact(logins_paths, collect_logins, "logins", external=True)
