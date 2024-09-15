import datetime
import struct

# convert FILETIME format to readable
def filetime_convert(filetime):
    seconds = filetime / 10**7  # convert FILETIME to seconds
    filetime_epoch = datetime.datetime(1601, 1, 1)  # define epoch
    readable_time = filetime_epoch + datetime.timedelta(seconds=seconds)  # add seconds to epoch
    return readable_time
