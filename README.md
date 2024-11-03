# Lichess Country Counter

A simple python CLI script which calculates the most common countries a lichess user has played against.

## Installation
To get the project to work, copy the file '.env EXAMPLE' over to .env and insert your Lichess API token,
which can be generated [here](https://lichess.org/account/oauth/token/create). No special permissions are necessary.

## Usage

Open a terminal such as CMD and navigate into the folder. Run lcc.py using the ``python lcc.py [username]`` command.


### Positional Arguments

- `username`: The Lichess username whose games you'd like to analyze.

### Options

- `-h`, `--help`: Show this help message and exit.
- `-v`, `--version`: Show the current version of the program.
- `-q`, `--quiet`: Suppress all output except for the final execution result.
- `-n NUMBER`, `--number NUMBER`: Output only the top `n` most frequent countries (default shows all).
- `-hu`, `--hide-unknown`: Hide the number of games played against users with unknown flags.
- `-m MAX_GAMES`, `--max-games MAX_GAMES`: Maximum number of games to analyze (default: 50).
- `-a`, `--all`: Analyze all games.

#### Example:

``python lcc.py -m 25 german11`` will analyze the 25 most recent games playes by user ``german11``.