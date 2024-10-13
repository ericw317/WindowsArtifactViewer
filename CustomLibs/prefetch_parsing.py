from CustomLibs import artifact_search as AS
from CustomLibs import InputValidation as IV
from CustomLibs import list_functions
import windowsprefetch
import os
import shutil
from tempfile import mkdtemp

def parse_prefetch(drive):
    prefetch_path = AS.set_path("Windows\\Prefetch", drive)  # set prefetch path
    prefetch_list = []

    # load prefetch files and sort them
    for file in os.listdir(prefetch_path):
        prefetch_list.append(os.path.join(prefetch_path, file))
    prefetch_list = list_functions.sort_files_by_modification(prefetch_list)
    prefetch_list.reverse()

    # prompt user for number of prefetch files to parse
    display_num = IV.int_between_numbers("\nEnter the number of most recent prefetch files to view: ",
                                         1, len(prefetch_list))

    # prompt user for number of runtimes to display
    runtime_num = IV.int_between_numbers("How many last runtimes do you want displayed for each: ",
                                         1, 8)

    # get file name lengths for formatting
    file_name_list = []
    for file in prefetch_list:
        file_name_list.append(os.path.basename(file))

    # set spacing size for formatting
    longest_file_name = max(file_name_list, key=len)
    longest_length = len(longest_file_name)

    # set spacing size
    if longest_length <= 30:
        spacing = 30
    else:
        spacing = longest_length

    # display files
    print(f"{'File Name':<{spacing}} | {'Executable Name':<{spacing}} | {'Run Count':<{spacing}} |"
          f"{'Last Runtimes':<{spacing}}")
    print("-" * (spacing * 4))
    for file in prefetch_list[:display_num]:
        # load prefetch file and data
        pf = windowsprefetch.Prefetch(file)
        exe_name = pf.executableName
        run_count = pf.runCount
        last_runtimes = get_last_runtimes(pf, runtime_num)

        print(f"{os.path.basename(file):<{spacing}} | {exe_name:<{spacing}} | {run_count:<{spacing}} | ", end="")

        for x, runtime in enumerate(last_runtimes[:runtime_num]):
            try:
                if x == 0:
                    print(f"{runtime:<{spacing}}")
                else:
                    print(f"{' ' * ((spacing * 3) + 9)}{runtime}")
            except IndexError:
                continue

        print("-" * (spacing * 4))

def parse_prefetch_external(drive):
    prefetch_path = AS.set_path("Windows\\Prefetch", drive)  # set prefetch path
    prefetch_list = []

    # make temp directory for analysis
    current_directory = os.getcwd()
    temp_dir = mkdtemp(dir=current_directory)
    try:
        for file_name in os.listdir(prefetch_path):
            if file_name.endswith(".pf"):
                full_file_name = os.path.join(prefetch_path, file_name)

                # Only copy if it's a file (skip directories or anything else)
                if os.path.isfile(full_file_name):
                    shutil.copy2(full_file_name, temp_dir)  # copy2 preserves metadata (modification times, etc.)
    except Exception as e:
        print(f"Error copying files: {e}")

    # load prefetch files and sort them
    for file in os.listdir(temp_dir):
        prefetch_list.append(os.path.join(temp_dir, file))
    prefetch_list = list_functions.sort_files_by_modification(prefetch_list)
    prefetch_list.reverse()

    # prompt user for number of prefetch files to parse
    display_num = IV.int_between_numbers("\nEnter the number of most recent prefetch files to view: ",
                                         1, len(prefetch_list))

    # prompt user for number of runtimes to display
    runtime_num = IV.int_between_numbers("How many last runtimes do you want displayed for each: ",
                                         1, 8)

    # get file name lengths for formatting
    file_name_list = []
    for file in prefetch_list:
        file_name_list.append(os.path.basename(file))

    # set spacing size for formatting
    longest_file_name = max(file_name_list, key=len)
    longest_length = len(longest_file_name)

    # set spacing size
    if longest_length <= 30:
        spacing = 30
    else:
        spacing = longest_length

    # display files
    print(f"{'File Name':<{spacing}} | {'Executable Name':<{spacing}} | {'Run Count':<{spacing}} |"
          f"{'Last Runtimes':<{spacing}}")
    print("-" * (spacing * 4))
    for file in prefetch_list[:display_num]:
        # load prefetch file and data
        pf = windowsprefetch.Prefetch(file)
        exe_name = pf.executableName
        run_count = pf.runCount
        last_runtimes = get_last_runtimes(pf, runtime_num)

        print(f"{os.path.basename(file):<{spacing}} | {exe_name:<{spacing}} | {run_count:<{spacing}} | ", end="")

        for x, runtime in enumerate(last_runtimes[:runtime_num]):
            try:
                if x == 0:
                    print(f"{runtime:<{spacing}}")
                else:
                    print(f"{' ' * ((spacing * 3) + 9)}{runtime}")
            except IndexError:
                continue

        print("-" * (spacing * 4))

    shutil.rmtree(temp_dir)

def get_last_runtimes(pf_file, num):
    runtime_list = []
    try:
        for x in range(num):
            runtime_list.append(f"{(pf_file.timestamps[x])[:-7]} UTC")
    except IndexError:
        pass
    return runtime_list
