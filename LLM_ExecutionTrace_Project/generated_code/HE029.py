def compare(game_scores, guesses):
    result = []
    for i in range(len(game_scores)):
        if game_scores[i] == guesses[i]:
            result.append(0)
        else:
            result.append(abs(game_scores[i] - guesses[i]))
    return result