import datetime
import struct

# convert FILETIME format to readable
def filetime_convert(filetime):
    seconds = filetime / 10**7  # convert FILETIME to seconds
    filetime_epoch = datetime.datetime(1601, 1, 1)  # define epoch
    readable_time = filetime_epoch + datetime.timedelta(seconds=seconds)  # add seconds to epoch
    return readable_time

# convert windows epoch to readable
def convert_windows_epoch(timestamp):
    epoch_start = datetime.datetime(1601, 1, 1)
    timestamp_in_seconds = timestamp / 1_000_000
    readable_time = epoch_start + datetime.timedelta(seconds=timestamp_in_seconds)
    readable_time = readable_time.replace(microsecond=0)
    return readable_time

# convert unix epoch in microseconds
def convert_unix_epoch_microseconds(timestamp):
    epoch_start = datetime.datetime(1970, 1, 1)
    readable_time = epoch_start + datetime.timedelta(microseconds=timestamp)
    readable_time = readable_time.replace(microsecond=0)
    return readable_time
