def common_in_nested_lists(nested_lists):
    common_elements = set()
    for nested_list in nested_lists:
        common_elements.update(set(nested_list))
    return list(common_elements)