# main.py (na raiz do projeto)
import sys
from chess_game.main import ChessGame

if __name__ == "__main__":
    game = ChessGame()
    game.run()
    sys.exit() # Garante que o programa saia corretamente