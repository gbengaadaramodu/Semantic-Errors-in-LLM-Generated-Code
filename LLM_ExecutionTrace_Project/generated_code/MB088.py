def filter_data(student_heights, minimal_height, minimal_weight):
    return {name: height for name, height in student_heights.items() if height >= minimal_height and weight >= minimal_weight}