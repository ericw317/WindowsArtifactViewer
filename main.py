from CustomLibs import InputValidation as IV
from CustomLibs import artifact_search as AS
from CustomLibs import registry_parsing as RP
from CustomLibs import recent_items_parsing as RI
from CustomLibs import prefetch_parsing
from CustomLibs import internet_parsing
import psutil
import os

# global variables
recent_items_user_list = []

# list connected devices
def list_drives():
    counter = 1
    partitions = psutil.disk_partitions()
    drives = {}

    # add each drive to a dictionary and enumerate each entry
    for partition in partitions:
        drives[counter] = partition.device
        counter += 1

    return drives

# search for artifacts
def artifact_search_device(drive):
    # initialize artifact list
    artifact_list = []

    # search recent items
    global recent_items_user_list
    recent_items_user_list = AS.search_recent_items(drive)

    # search for registry
    if AS.search_live_registry(drive):
        artifact_list.append("Registry")

    # check recent items list
    if "No***Users***Found" in recent_items_user_list:
        recent_items_user_list = []
    if len(recent_items_user_list) != 0:
        artifact_list.append("Recent Items (LNK Files)")

    # search for prefetch files
    if AS.search_prefetch(drive):
        artifact_list.append("Prefetch")

    # search internet artifact
    if AS.search_internet(drive):
        artifact_list.append("Internet Artifacts")

    # output found artifacts
    print("\nArtifacts Found:\n----------------")
    for index, artifact in enumerate(artifact_list):
        print(f"{index + 1}: {artifact}")

    return artifact_list

# artifact selection function
def artifact_selection(artifact_list, drive):
    selection = IV.int_between_numbers("Select an artifact: ", 0, len(artifact_list))  # prompt selection
    selected_artifact = artifact_list[selection - 1]  # set selected artifact

    if selection == 0:
        global artifact_menu
        artifact_menu = False
        return

    if selected_artifact == "Registry":
        RP.parse_registry(drive)
    elif selected_artifact == "Recent Items (LNK Files)":
        if drive == "C:\\":
            RI.parse_recent(recent_items_user_list, drive)
        else:
            RI.parse_recent_external(recent_items_user_list, drive)
    elif selected_artifact == "Prefetch":
        if drive == "C:\\":
            prefetch_parsing.parse_prefetch(drive)
        else:
            prefetch_parsing.parse_prefetch_external(drive)
    elif selected_artifact == "Internet Artifacts":
        if drive == "C:\\":
            internet_parsing.main(drive)
        else:
            internet_parsing.main(drive)


artifact_menu = True

def main():
    drives = list_drives()  # load drives
    while True:
        global artifact_menu
        artifact_menu = True
        print("Enter the number of the device you want to analyze: ")
        for number, drive in drives.items():  # print all connected devices
            print(f"{number}: {drive}")
        print("0: Exit Program")
        drive_selected = IV.int_between_numbers("", 0, len(drives))  # get input on which drive to analyze
        if drive_selected == 0:
            break
        drive_selected = drives[drive_selected]  # map input to drive

        while artifact_menu:
            artifact_list = artifact_search_device(drive_selected)  # display found artifacts and set in list
            print("O: Go Back")  # print go back option
            artifact_selection(artifact_list, drive_selected)  # prompt artifact selection

    return 0


if __name__ == "__main__":
    main()
