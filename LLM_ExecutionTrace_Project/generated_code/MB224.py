def find_adverb_position(sentence):
    adverb = ""
    start_index = 0
    end_index = 0
    
    for word in sentence.split():
        if word[-1] == 'ly':
            adverb = word
            break
            
    for i, word in enumerate(sentence.split()):
        if word == adverb:
            start_index = i
            break
            
    for i, word in enumerate(sentence.split()[::-1]):
        if word == adverb:
            end_index = len(sentence.split()) - i
            break
            
    return (start_index, end_index, adverb)