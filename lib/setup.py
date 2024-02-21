import srcomapi
import srcomapi.datatypes as sdt
from sys import stdout, exit
import shelve

game_name = None
game_choice = None
make_FG = None
orientation_FG = None
defaults_FG = None
make_IL = None
orientation_IL = None
defaults_IL = None
make_ranking = None
update_channel = None
channel_id = None

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")

game_name = input("Enter game name: ")

api = srcomapi.SpeedrunCom()
game_options = api.search(sdt.Game, {'name': game_name})
orientations = ['vertical', 'horizontal']

if game_options == []:  # abort if the game is not on speedrun.com
    print("Sorry, but no game with that name could be found.")
    exit()
else:   # list possible games from given title
    print("Select your game from the following options.")
    for x,k in enumerate(game_options):
        print("{}: {}".format(x,k.name))
    game_choice = int(input("Your game: "))
    # game = game_options[game_choice]

make_FG = query_yes_no('Do you wish to create a leaderboard of Full Game runs?')

if make_FG:
    print("Should the categories be oriented vertically or horizontally in your Full Game leaderboard?")
    for x,k in enumerate(orientations):
            print("{}: {}".format(x,k))
    orientation_FG = orientations[int(input("Your choice: "))]
    
    defaults_FG = query_yes_no('Only consider Full Game runs with default variables?')

make_IL = query_yes_no('Do you wish to create a leaderboard of Individual Level runs?')

if make_IL:
    print("Should the categories be oriented vertically or horizontally in your Individual Levels leaderboard?")
    for x,k in enumerate(orientations):
            print("{}: {}".format(x,k))
    orientation_IL = orientations[int(input("Your choice: "))]

    defaults_IL = query_yes_no('Only consider Individual Level runs with default variables? \n IMPORTANT: If your game has more than 20 levels, then select "no" here.')

make_ranking = query_yes_no('Do you wish to create a ranking leaderboard of runners based on total number of world records?')

update_channel = query_yes_no('Do you wish to automatically post updated leaderboards to a channel in your server?')

if update_channel:
    channel_id = int(input("Enter the ID of the text channel you wish to use: "))


with shelve.open('./data/config') as db:
    db['game_name'] = game_name
    db['game_choice'] = game_choice
    db['make_FG'] = make_FG
    db['orientation_FG'] = orientation_FG
    db['defaults_FG'] = defaults_FG
    db['make_IL'] = make_IL
    db['orientation_IL'] = orientation_IL
    db['defaults_IL'] = defaults_IL
    db['make_ranking'] = make_ranking
    db['update_channel'] = update_channel
    db['channel_id'] = channel_id
