from ai import main_ai
from player import main_player
import sys


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "ai":
            print("Running AI mode...")
            main_ai()
        elif arg == "player":
            print("Running Player mode...")
            main_player()
        else:
            print("Invalid argument. Use 'ai' or 'player'.")
    else:
        print("Usage: python main.py [ai|player]")