def change_date_format(date_string):
    date = date_string.split('-')
    return f"{date[2]}-{date[1]}-{date[0]}"