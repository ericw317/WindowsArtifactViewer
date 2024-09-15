from datetime import datetime

# validate date format
def validate_date(install_date):
    try:
        datetime.strptime(install_date, "%m/%d/%Y %H:%M:%S")
        return True
    except ValueError:
        return False

def get_recent_installations(reg):
    applications_list = []  # applications_list
    try:
        key = reg.open("Root\\InventoryApplication")
        for subkey in key.subkeys():
            try:
                # store installation date and name
                install_date = subkey.value("InstallDate").value()
                name = subkey.value("Name").value()
                if validate_date(install_date):  # verify date format
                    applications_list.append([install_date, name])  # add values to applications_list
            except:
                pass

        applications_list = sorted(applications_list, key=lambda x: x[0], reverse=True)  # sort the list
        return applications_list
    except:
        return None
