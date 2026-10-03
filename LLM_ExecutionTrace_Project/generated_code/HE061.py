def Strongest_Extension(class_name, extensions):
    strongest = None
    strength = float('-inf')
    for extension in extensions:
        cap = sum(1 for c in extension if c.isupper())
        sm = sum(1 for c in extension if c.islower())
        current_strength = cap - sm
        if current_strength > strength:
            strongest = extension
            strength = current_strength
    return f"{class_name}.{strongest}"