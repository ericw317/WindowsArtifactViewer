from Registry import Registry
from CustomLibs import time_conversion as TC

def display_keys(key):
    for subkey in key.subkeys():
        print(f"Subkey: {subkey.name()}")

# get initial OS
def get_initial_OS(reg):
    key = reg.open("Microsoft\\Windows NT\\CurrentVersion")
    return key.value("ProductName").value()

# get registered owner
def get_registered_owner(reg):
    key = reg.open("Microsoft\\Windows NT\\CurrentVersion")
    return key.value("RegisteredOwner").value()

# get installation time
def get_install_time(reg):
    key = reg.open("Microsoft\\Windows NT\\CurrentVersion")
    try:
        return key.value("InstallTime").value()
    except:
        return None

# get network cards
def get_network_cards(reg):
    network_cards = []  # initialize network cards list
    key = reg.open("Microsoft\\Windows NT\\CurrentVersion\\NetworkCards")
    # loop through network cards adding name of each to list
    for subkey in key.subkeys():
        network_cards.append(subkey.value("Description").value())

    return network_cards

# get networks connected to
def get_networks_connected_to(reg):
    network_connections = []  # initialize network connections list
    key = reg.open("Microsoft\\Windows NT\\CurrentVersion\\NetworkList\\Profiles")

    # loop through each network adding relevant details to list
    for subkey in key.subkeys():
        network_name = subkey.value("ProfileName").value()
        network_connections.append(network_name)

    return network_connections

# get persistence programs
def get_persistent_programs(reg):
    persistent_programs = []  # initialize persistent programs list
    key = reg.open("Microsoft\\Windows\\CurrentVersion\\Run")

    # loop through each persistent program, adding each to list
    for value in key.values():
        persistent_programs.append(f"{value.name()}: {value.value()}")

    return persistent_programs