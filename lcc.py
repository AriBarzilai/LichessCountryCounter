#!/usr/bin/env python

from dotenv import load_dotenv
import os
import argparse
import requests
import json
from collections import Counter
import time

load_dotenv()

api_key = os.getenv("OAUTH_2_LICHESS_KEY")
if not api_key:
    raise ValueError("API key not found. Please set OAUTH_2_LICHESS_KEY in your environment variables.")

parser = argparse.ArgumentParser(
                    prog='python lcc.py',
                    description='\'Lichess Country Counter\' counts the number of games played against each country on Lichess.',
                    epilog="Please ensure you've set the OAUTH_2_LICHESS_KEY environment variable in the .env file. See the README for more information.")
parser.add_argument("-v", "--version",
                    action='version',
                    version='v1.01',
                    help="Show the current version of the program.")
parser.add_argument("-q", "--quiet",
                    help="Suppresses all output except for the final execution result.",
                    action='store_true')
parser.add_argument("username",
                    help="The lichess username whose games you'd like to analyse.",
                    type=str)
parser.add_argument("-n", "--number",
                    help="Outputs only the top n most frequent countries. Default shows all.",
                    type=int)
parser.add_argument('-hu', '--hide-unknown',
                    help="Hides the number of games played against users with unknown flags.",
                    action='store_true')
parser.add_argument
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "-m", "--max-games",
    type=int,
    default=50,
    help="Maximum number of games to analyze (default: 50)"
)
group.add_argument(
    "-a", "--all",
    action='store_true',
    help="Analyze all games"
)

class SimpleTimeEstimator:
    def __init__(self, username, max_games, all=False, is_quiet=False):
        self.current_games_analysed = 0
        self.games_to_analyse, self.seconds_estimate = self.estimate_time_to_completion(username, max_games, all, is_quiet)
        self.current_update_benchmark = 0.05
        self.benchmark_increment = 0.05
        self.start_time = time.time()
  
    def estimate_time_to_completion(self, username, max_games: int, all=False, is_quiet=False):
        try:
            base_url = f'https://lichess.org/api/user/{username}'
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            response = requests.get(base_url, headers=headers)
            if response.status_code == 200:
                if all:
                    max_games = response.json()['count']['all']
                seconds = max_games / (10/3)
                return max_games, seconds
            else:
                response.raise_for_status()
        except requests.HTTPError as e:
            if not is_quiet:
                if e.response.status_code == 404:
                    print(f"An error occurred. Please verify that user '{username}' exists.")
                print(e.response.text)
            exit(e.response.status_code)
            
    def update(self, games_analysed, is_quiet=False):
        self.current_games_analysed = games_analysed
        if ((games_analysed / self.games_to_analyse)) >= self.current_update_benchmark:
            if not is_quiet:
                print(f"  {games_analysed / self.games_to_analyse * 100:.0f}% complete ({self.current_games_analysed} games) ", end='\r')
            self.current_update_benchmark += self.benchmark_increment
    
def _extract_games(username: str, count):
    """Extract the latest game of a Lichess user. This function is for testing purposes only.
    
    Args:
        username (str): The Lichess username to extract the latest game from.
        count (int): The number of games to extract."""
    base_url = f'https://lichess.org/api/games/user/{username}'
    headers = {
        'Accept': 'application/x-ndjson',
        'Authorization': f'Bearer {api_key}'
    }
    response = requests.get(base_url, headers=headers, params={'max': count}, stream=True)
    
    if response.status_code == 200:
        games = []
        for raw_game_data in response.iter_lines():
            if raw_game_data:
                game = json.loads(raw_game_data.decode('utf-8'))
                processed_game = process_game(username, game)
                games.append(processed_game)
        return games
    else:
        response.raise_for_status()

def _print_games(games):
    for game in games:
        print(game)
        print()

def process_games(username: str, estimator: SimpleTimeEstimator, return_games=False, is_quiet=False, **params):
    """Download the games of a Lichess user.
    Possible query parameters available at https://lichess.org/api#tag/Games/operation/apiGamesUser
    
    Args:
        username (str): The Lichess username to download games from.
        **params: Additional query parameters"""
    base_url = f'https://lichess.org/api/games/user/{username}'
    headers = {
        'Accept': 'application/x-ndjson',
        'Authorization': f'Bearer {api_key}'
    }
    try:
        response = requests.get(base_url, headers=headers, params=params, stream=True)
        avg_opponent_rating = 0
        results = Counter()
        games = []
        for games_analysed_count, raw_game_data in enumerate(response.iter_lines(), start=1):
            if raw_game_data:
                game = json.loads(raw_game_data.decode('utf-8'))
                game_data = process_game(username, game)
                avg_opponent_rating += ((game_data['opponent_rating'] - avg_opponent_rating) / games_analysed_count)
                flag = game_data['opponent_flag']
                if flag not in results:
                    results[flag] = 1
                else:
                    results[flag] += 1
                if return_games:
                    games.append(game_data)
            estimator.update(games_analysed_count, is_quiet)
        if return_games:
            return games, results, avg_opponent_rating
        else:
            return results, avg_opponent_rating
    except requests.HTTPError as e:
        if not is_quiet:
            print(f"Analysed {estimator.current_games_analysed} games before receiving Error {response.status_code}.")
            print(e.response.text)
        return results, avg_opponent_rating

def process_game(username: str, game):
    """Process a user's game to extract only the relevant information. Returns as a dictionary.
    
    Args:
        username (str): The username of the player whose game is being processed.
        game: a JSON object representing a game."""
    
    color, opponent_color = process_player_colors(game, username)
    opponent_rating = game['players'][opponent_color]['rating']
    opponent_name = game['players'][opponent_color]['user']['name']
    try:
        winner_name = game['players'][game['winner']]['user']['name']
    except KeyError:
        winner_name = 'Unknown'
    return {
        'id': game['id'],
        'perf': game['perf'],
        'opponent': opponent_name,
        'opponent_rating': opponent_rating,
        'opponent_flag': extract_player_flag(opponent_name),
        'winner': winner_name,
        'status': game['status'],
        'color': color,
        'opponent_color': opponent_color,
        'opponent_rating': opponent_rating
    }

def extract_player_flag(username: str, is_quiet=False):
    """Extract the country flag of a Lichess user.
    
    Args:
        username (str): The Lichess username to extract the flag from."""
    base_url = f'https://lichess.org/api/user/{username}'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    try:
        response = requests.get(base_url, headers=headers)
        user_data = response.json()
        try:
            return user_data['profile']['flag']
        except KeyError:
            return 'Unknown'
    except requests.HTTPError as e:
        if not is_quiet:
            print(f'Error: {response.status_code}')
            response.raise_for_status()

def process_player_colors(game, username):
    white_name = game['players']['white']['user']['name']    
    color = ''
    opponent_color = ''
    if white_name == username:
        color = 'white'
        opponent_color = 'black'
    else:
        color = 'black'
        opponent_color = 'white'   
    return color, opponent_color

def process_results(results: Counter, n: int, hide_unknown: bool):
    if n:
        results = results.most_common(n)
    if hide_unknown:
        results = {k: v for k, v in results.items() if k != 'Unknown'}
    return results
def verify_auth():
    url = "https://lichess.org/api/account"
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error. Status code ", response.status_code)
        exit(response.status_code)
        
def execute_workflow():
    args = parser.parse_args()
    verify_auth()
    is_quiet = args.quiet
    estimator = SimpleTimeEstimator(args.username, args.max_games, args.all, is_quiet)
    
    if estimator.seconds_estimate:
        if not is_quiet:
            print (f"Loading... Estimated time to completion: {estimator.seconds_estimate:.0f} seconds.")
        if args.all:
            flag_counts, avg_rating = process_games(username=args.username, estimator=estimator, is_quiet=is_quiet, moves=False)
        else:
            flag_counts, avg_rating = process_games(username=args.username, estimator=estimator, is_quiet=is_quiet, max=args.max_games, moves=False)
        flag_counts = process_results(flag_counts, args.number, args.hide_unknown)
        if not is_quiet:
            print(' ', end='\r')
            print(f"Done! Time: {time.time() - estimator.start_time:.0f} seconds.".ljust(40))
            print(f"Avg. Rating: {avg_rating:.0f}")
        print(flag_counts)           
             
def main():
    execute_workflow()

if __name__ == '__main__':
    main()
