#!/usr/bin/env python

from dotenv import load_dotenv
import os
import argparse
import requests
import json
from collections import Counter

load_dotenv()

api_key = os.getenv("OAUTH_2_LICHESS_KEY")
if not api_key:
    raise ValueError("API key not found. Please set OAUTH_2_LICHESS_KEY in your environment variables.")

parser = argparse.ArgumentParser(
                    prog='python lcc.py',
                    description='\'Lichess Country Counter\' counts the number of games played against each country on Lichess.',
                    epilog="Please ensure you've set the OAUTH_2_LICHESS_KEY environment variable in the .env file. See the README for more information.")
parser.add_argument("username", help="The lichess username whose games you'd like to analyse.", type=str)
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
        print(f'Error: {response.status_code}')
        response.raise_for_status()

def _print_games(games):
    for game in games:
        print(game)
        print()

def process_games(username: str, return_games=False, **params):
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
    
    response = requests.get(base_url, headers=headers, params=params, stream=True)
    
    if response.status_code == 200:
        avg_opponent_rating = 0
        flag_counts = Counter()
        games = []
        for c, raw_game_data in enumerate(response.iter_lines(), start=1):
            if raw_game_data:
                game = json.loads(raw_game_data.decode('utf-8'))
                game_data = process_game(username, game)
                avg_opponent_rating += ((game_data['opponent_rating'] - avg_opponent_rating) / c)
                flag = game_data['opponent_flag']
                if flag not in flag_counts:
                    flag_counts[flag] = 1
                else:
                    flag_counts[flag] += 1
                if return_games:
                    games.append(game_data)
        flag_counts = flag_counts.most_common() # Sort the flags by frequency
        if return_games:
            return games, flag_counts, avg_opponent_rating
        else:
            return flag_counts, avg_opponent_rating
    else:
        print(f'Error: {response.status_code}')
        response.raise_for_status()

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

def extract_player_flag(username: str):
    """Extract the country flag of a Lichess user.
    
    Args:
        username (str): The Lichess username to extract the flag from."""
    base_url = f'https://lichess.org/api/user/{username}'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    response = requests.get(base_url, headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        try:
            return user_data['profile']['flag']
        except KeyError:
            return 'Unknown'
    else:
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

def estimate_time_to_completion(username, max_games: int, all=False):
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
            seconds = max_games / 30
            return seconds
        else:
            print(f'Error: {response.status_code}')
            response.raise_for_status()
    except Exception as e:
        print(f"An error occurred. Please verify that user '{username}' exists.")

             
def main():
    args = parser.parse_args()
    seconds = estimate_time_to_completion(args.username, args.max_games)
    if seconds:
        print (f"Loading... Estimated time to completion: {20*seconds:.1f} seconds.")
        if args.all:
            flag_counts, avg_rating = process_games(args.username, moves=False)
        else:
            flag_counts, avg_rating = process_games(args.username, max=args.max_games, moves=False)
        print(flag_counts)
        print("Avg. Rating:" + str(avg_rating))

if __name__ == '__main__':
    main()
