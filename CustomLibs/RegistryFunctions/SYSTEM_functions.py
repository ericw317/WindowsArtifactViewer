from Registry import Registry

def display_keys(key):
    for subkey in key.subkeys():
        print(f"Subkey: {subkey.name()}")

# get computer name
def get_computer_name(reg):
    key = reg.open("ControlSet001\\Control\\ComputerName\\ComputerName")
    return key.value("ComputerName").value()

# get time zone information
def get_time_zone(reg):
    key = reg.open("ControlSet001\\Control\\TimeZoneInformation")
    return key.value("TimeZoneKeyName").value()

# get USB information
def get_USB_devices(reg):
    USB_name_list = []
    key = reg.open("ControlSet001\\Enum\\USB")

    def recurse_subkeys(key):
        for subkey in key.subkeys():
            # Check for the "FriendlyName" value
            try:
                friendly_name_value = subkey.value("FriendlyName").value()
                if friendly_name_value not in USB_name_list:
                    USB_name_list.append(friendly_name_value)
            except Registry.RegistryValueNotFoundException:
                pass  # "FriendlyName" not found, continue

            # Recurse into the subkey
            recurse_subkeys(subkey)

    recurse_subkeys(key)
    return USB_name_list

# get USB storage
def get_USB_storage(reg):
    USB_storage_list = []
    key = reg.open("ControlSet001\\Enum\\USBSTOR")

    def recurse_subkeys(key):
        for subkey in key.subkeys():
            # Check for the "FriendlyName" value
            try:
                friendly_name_value = subkey.value("FriendlyName").value()
                if friendly_name_value not in USB_storage_list:
                    USB_storage_list.append(friendly_name_value)
            except Registry.RegistryValueNotFoundException:
                pass  # "FriendlyName" not found, continue

            # Recurse into the subkey
            recurse_subkeys(subkey)

    recurse_subkeys(key)
    return USB_storage_list
