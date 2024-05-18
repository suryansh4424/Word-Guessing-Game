
# Word-Guessing-Game

Using Genetic Algorithm and Constraint Satisfaction Problems (CSPs)




## Run Locally

Clone the project

```bash
  git clone https://github.com/suryansh4424/Word-Guessing-Game.git
```

Create Virtual Environment

```bash
  python -m venv venv
```

Activate the Virtual Environment

```bash
 venv\Scripts\activate
```

Install Dependencies

```bash
  pip install -r requirements.txt
```
Run Your Script

```bash
  python main.py
```

## Demo

https://github.com/suryansh4424/Word-Guessing-Game/assets/131521058/32ee71a8-27cb-4f7a-9dbb-eb96cf62796e


## Appendix

Game Setup:

- The game is based on the Mastermind game rules.

- Parameters include the number of colors, the length of the secret code (5 in this case), and the number of guesses allowed (10).

Generate Secret Code:

- A random secret code conforming to the specified rules is generated.

- Each code consists of a sequence of colored pegs.

Genetic Algorithm Initialization and Fitness Function:

- A population of candidate solutions (codes) is initialized randomly.

- Parameters like population size, mutation rate, and crossover rate are defined.

- A fitness function evaluates each candidate solution based on its similarity to the secret code.

Constraint Satisfaction Problem (CSP) for Suggestions:
- A suggestion system uses CSP principles to analyze the player's previous guesses and feedback.
- It provides optimal suggestions for the next guess based on constraints provided by the feedback.

Genetic Algorithm Loop:
- Generations of candidate solutions are iterated until a satisfactory solution is found or a maximum number of generations is reached.
- Fitness of each candidate solution is evaluated using the fitness function.
- Genetic operators like mutation and crossover are applied to create offspring from selected parents.

Game Interaction:
- The player makes guesses, and the game provides feedback on each guess.
- Feedback indicates the number of correct colors and positions and the number of correct colors but in the wrong positions.

Win/Loss Condition:
- The game determines if the player has correctly guessed the secret code within the allowed number of guesses.
- If the player guesses correctly, they win; otherwise, they lose.