# Lichess Country Counter

A simple python CLI script which calculates the most common countries a lichess user has played against.

## Installation
To get the project to work, copy the file '.env EXAMPLE' over to .env and insert your Lichess API token,
which can be generated [here](https://lichess.org/account/oauth/token/create). No special permissions are necessary.

## Usage

Open a terminal such as CMD and navigate into the folder. Run lcc.py using the ``python lcc.py [username]`` command.

### Optional modifiers:

``-m`` or ``--max``: the maximum number of games to analyse. Default is 50.

``-a`` or ``--all``: analyse all games (warning: this may take some time!).

#### Example:

``python lcc.py -m 25 german11`` will analyze the 25 most recent games playes by user ``german11``.