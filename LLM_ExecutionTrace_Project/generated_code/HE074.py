def file_name_check(file_name):
    if len(file_name) > 3 and "." in file_name:
        prefix, suffix = file_name.split(".")
        if prefix and prefix[0].isalpha() and suffix in ["txt", "exe", "dll"]:
            return "Yes"
    return "No"