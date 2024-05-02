import os
import random
import string
from enum import Enum

import httpx
import numpy as np
# from PyInquirer import prompt
from rich.console import Console
from rich.text import Text
from skopt import gp_minimize


class Character(int, Enum):
    PRESENT = 0
    NOT_PRESENT = 1
    NOT_USED = 2


class Guess(int, Enum):
    CLOSER = 0
    FARTHER = 1


ASCII_ART = Text(
    r"""
                          ____   
 _      ______  _________/ / /__ 
| | /| / / __ \/ ___/ __  / / _ \
| |/ |/ / /_/ / /  / /_/ / /  __/
|__/|__/\____/_/   \__,_/_/\___/ 
""",
    style="bold purple",
)

HELP = "Guess a 5 letter word in 10 tries\n"

console = Console()


def fetch_word() -> str:
    """Fetch a random 5 letter english word that will be guessed by
    the user.

    Returns:
        str: Target word for wordle
    """
    response = httpx.get("https://random-word-api.vercel.app/api?words=1&length=5")
    if response.status_code != 200:
        return generate_random_word()
    data = response.json()
    return data[0]


def generate_random_word() -> str:
    """_summary_

    Returns:
        str: _description_
    """
    chars = [random.choice(string.ascii_lowercase) for _ in range(5)]
    return "".join(chars)


def generate_population(population_size: int) -> list[str]:
    """_summary_

    Args:
        population_size (int): _description_

    Returns:
        list[str]: _description_
    """
    population = [generate_random_word() for _ in range(population_size)]
    return population


def similarity_score(word1: str, word2: str) -> float:
    """_summary_

    Args:
        word1 (str): _description_
        word2 (str): _description_

    Returns:
        float: _description_
    """
    size_x = len(word1) + 1
    size_y = len(word2) + 1
    matrix = np.zeros((size_x, size_y))

    for x in range(size_x):
        matrix[x, 0] = x
    for y in range(size_y):
        matrix[0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if word1[x - 1] == word2[y - 1]:
                substitution_cost = 0
            else:
                substitution_cost = 1
            matrix[x, y] = min(
                matrix[x - 1, y] + 1,
                matrix[x, y - 1] + 1,
                matrix[x - 1, y - 1] + substitution_cost,
            )

    distance = matrix[size_x - 1, size_y - 1]
    max_len = max(len(word1), len(word2))
    return 1.0 - (distance / max_len)


def fitness_score(
    guess: str, target: str, previous_guesses: list[tuple[str, Guess]]
) -> float:
    """_summary_

    Args:
        guess (str): _description_
        target (str): _description_
        previous_guesses (list[tuple[str, Guess]]): _description_

    Returns:
        float: _description_
    """
    semantic_similarity = similarity_score(guess, target)
    correct_chars = sum(
        [1 for expected, actual in zip(target, guess) if expected == actual]
    )
    partial_match_bonus = 0.5 * correct_chars

    feedback_score = 0
    for _, feedback in previous_guesses:
        match feedback:
            case Guess.CLOSER:
                feedback_score += 1
            case Guess.FARTHER:
                feedback_score -= 1

    fitness = (semantic_similarity + partial_match_bonus) * feedback_score
    return fitness


def mutate(word: str, mutation_rate: float) -> str:
    """_summary_

    Args:
        word (str): _description_
        mutation_rate (float): _description_

    Returns:
        str: _description_
    """
    mutated_word = list(word)
    for i in range(5):
        if random.random() < mutation_rate:
            mutated_word[i] = random.choice(string.ascii_lowercase)
    return "".join(mutated_word)


def evolve_population(
    population: list[str],
    target: str,
    guess: str,
    mutation_rate: float,
    present_chars: dict[str, Character],
) -> list[str]:
    """_summary_

    Args:
        population (list[str]): _description_
        target (str): _description_
        guess (str): _description_
        mutation_rate (float): _description_
        present_chars (dict[str, Character]): _description_

    Returns:
        list[str]: _description_
    """
    next_generation = []

    correct_indices = [
        i
        for i, (char_target, char_guess) in enumerate(zip(target, guess))
        if char_target == char_guess
    ]
    chars = present_chars.keys()
    chars = [key for key in chars if present_chars[key] != Character.NOT_PRESENT]

    while len(next_generation) < len(population):
        child = ""
        for i in range(5):
            if i in correct_indices:
                child += guess[i]
            else:
                child += random.choice(chars)
        child = mutate(child, mutation_rate)
        next_generation.append(child)

    return next_generation


def suggest(
    population: list[str], target: str, previous_guesses: list[tuple[str, Guess]]
) -> list[str]:
    """_summary_

    Args:
        population (list[str]): _description_
        target (str): _description_
        previous_guesses (list[tuple[str, Guess]]): _description_

    Returns:
        list[str]: _description_
    """
    suggestions = sorted(
        population,
        key=lambda x: fitness_score(x, target, previous_guesses),
        reverse=True,
    )
    # First 5 distinct suggestions
    suggestions = list(set(suggestions))[:5]
    return suggestions


def optimize_parameters(target: str, present_chars: dict[str, Character]):
    """Optimize population size, maximum number of generations and mutation rate
    using bayesian optimization"""

    def objective(params):
        population_size, mutation_rate = params
        population = generate_population(population_size)
        for _ in range(10):
            population = evolve_population(
                population,
                target,
                "",
                mutation_rate,
                present_chars,
            )
        return -fitness_score(population[0], target, [])

    space = [(50, 200), (0.01, 0.1)]
    result = gp_minimize(objective, space, n_calls=10)
    if not result:
        raise
    return result.x


def get_feedback(target: str, guess: str) -> str:
    """_summary_

    Args:
        target (str): _description_
        guess (str): _description_

    Returns:
        str: _description_
    """
    result = ""
    correct_indices = [
        i
        for i, (char_target, char_guess) in enumerate(zip(target, guess))
        if char_target == char_guess
    ]

    for i, (_, char_guess) in enumerate(zip(target, guess)):
        if i in correct_indices:
            result += f"\033[32m{char_guess}\033[0m"
        elif char_guess in target:
            result += f"\033[33m{char_guess}\033[0m"
        else:
            result += "_"
    return result


def stdout(
    feedbacks: list[list[str]], present_chars: dict[str, bool], score: float
) -> None:
    """Print feedback of the guesses made by the user, along with the similarity
    percentage of target word and user's guess and a list of characters showing
    which of them have been used.

    Args:
        feedbacks (list[list[str]]): _description_
        present_chars (dict[str, bool]): _description_
        score (float): _description_
    """
    os.system("clear")
    console.print(ASCII_ART)

    text = Text()
    for feedback in feedbacks:
        text.append("\t")
        text.append("".join(feedback))
        text.append("\n")
    console.print(text)

    present = "[ "
    for char in present_chars:
        match present_chars[char]:
            case Character.PRESENT:
                present += f"\033[32m{char}\033[0m"
            case Character.NOT_PRESENT:
                present += f"\033[31m{char}\033[0m"
            case Character.NOT_USED:
                present += char
        present += ", "
    present = present[:-2] + " ]"

    console.rule("Guess Statistics")
    print(f"\nPresent Characters: {present}")
    print(f"Similarity Score: {score}\n")


def main():
    present_chars = {}
    for i in range(97, 123):
        present_chars[chr(i)] = Character.NOT_USED

    # target = generate_random_word()
    target = fetch_word()
    population_size, mutation_rate = optimize_parameters(target, present_chars)
    population = generate_population(population_size)

    previous_guesses = []
    feedbacks = [[] for _ in range(10)]

    console.print(ASCII_ART)
    console.print(HELP)
    for i in range(10):
        # question = [
        #     {
        #         "type": "input",
        #         "name": "guess",
        #         "message": "Enter your guess or 's' to use a suggestion",
        #     },
        # ]
        # answer = prompt(question)

        # user_guess = answer["guess"].lower()

        # if user_guess == "s":
        #     suggestions = suggest(population, target, previous_guesses)
        #     question = [
        #         {
        #             "type": "list",
        #             "name": "suggestion",
        #             "message": "Choose a suggestion",
        #             "choices": suggestions,
        #         }
        #     ]
        #     answer = prompt(question)
        #     user_guess = answer["suggestion"]
        
        user_guess = input("Enter your guess or 's' to use a suggestion: ").lower()

        if user_guess == "s":
            suggestions = suggest(population, target, previous_guesses)
            print("Suggestions:")
            for i, suggestion in enumerate(suggestions, start=1):
                print(f"{i}. {suggestion}")
            choice = int(input("Choose a suggestion by entering its number: ")) - 1
            user_guess = suggestions[choice]


        if user_guess == target:
            text = Text()
            text.append("[+]", style="bold green")
            text.append(" Word guessed correctly!")
            console.print(text)
            break

        for char in user_guess:
            if char in target:
                present_chars[char] = Character.PRESENT
            else:
                present_chars[char] = Character.NOT_PRESENT

        feedback = get_feedback(target, user_guess)
        correct_chars = sum(
            [1 for expected, actual in zip(target, user_guess) if expected == actual]
        )
        similarity_percentage = similarity_score(user_guess, target) * 100

        feedbacks[i].extend(feedback)
        stdout(feedbacks, present_chars, similarity_percentage)

        previous_guesses.append(
            (user_guess, Guess.CLOSER if correct_chars > 0 else Guess.FARTHER)
        )
        population = evolve_population(
            population,
            target,
            user_guess,
            mutation_rate,
            present_chars,
        )
    else:
        text = Text()
        text.append("[-]", style="bold red")
        text.append(" Maximum tries reached, word was ")
        text.append(target, style="bold purple")
        console.print(text)


if __name__ == "__main__":
    main()