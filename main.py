from CustomLibs import InputValidation as IV
from CustomLibs import artifact_search as AS
from CustomLibs import registry_parsing as RP
import psutil
import os

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

    # search for registry
    if AS.search_live_registry(drive):
        artifact_list.append("Registry")

    artifact_list.append("Go Back")

    # output found artifacts
    print("\nArtifacts Found:\n----------------")
    for index, artifact in enumerate(artifact_list):
        print(f"{index + 1}: {artifact}")

    return artifact_list

# artifact selection function
def artifact_selection(artifact_list, drive):
    selection = IV.int_between_numbers("Select an artifact: ", 1, len(artifact_list))  # prompt selection
    selected_artifact = artifact_list[selection - 1]  # set selected artifact

    if selected_artifact == "Registry":
        RP.parse_registry(drive)
    elif selected_artifact == "Go Back":
        global artifact_menu
        artifact_menu = False


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
            artifact_selection(artifact_list, drive_selected)  # prompt artifact selection

    return 0


if __name__ == "__main__":
    main()
