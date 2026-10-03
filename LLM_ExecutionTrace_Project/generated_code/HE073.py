def numerical_letter_grade(gpas):
    # Create a dictionary to map GPAs to letter grades
    gpa_to_letter_grade = {
        4.0: "A+",
        3.7: "A",
        3.3: "A-",
        3.0: "B+",
        2.7: "B",
        2.3: "B-",
        2.0: "C+",
        1.7: "C",
        1.3: "C-",
        1.0: "D+",
        0.7: "D",
        0.0: "D-",
        0.0: "E"
    }

    # Iterate through the list of GPAs and use the dictionary to map each GPA to a letter grade
    letter_grades = []
    for gpa in gpas:
        letter_grade = gpa_to_letter_grade[gpa]
        letter_grades.append(letter_grade)

    return letter_grades