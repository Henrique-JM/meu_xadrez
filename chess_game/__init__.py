# chess_game/main.py (modificado)
import pygame
import chess
import os
import time  # Adicionar para simular "pensamento" da IA
from chess_game.engine import ChessEngine  # Importar o motor da IA

# --- Configurações da Janela ---
WIDTH, HEIGHT = 800, 800
FPS = 60
BOARD_SIZE = 8
SQUARE_SIZE = WIDTH // BOARD_SIZE

# --- Cores ---
LIGHT_SQUARE_COLOR = (240, 217, 181)  # Bege claro
DARK_SQUARE_COLOR = (181, 136, 99)  # Marrom escuro
SELECTED_SQUARE_COLOR = (150, 200, 255)  # Azul claro para seleção
VALID_MOVE_COLOR = (120, 180, 100)  # Verde para movimentos válidos
CHECK_SQUARE_COLOR = (255, 0, 0)  # Vermelho para o rei em xeque

# --- Carregamento de Imagens das Peças ---
PIECE_IMAGES = {}


def load_piece_images():
    pieces = ['bR', 'bN', 'bB', 'bQ', 'bK', 'bP',
              'wR', 'wN', 'wB', 'wQ', 'wK', 'wP']
    for piece in pieces:
        path = os.path.join('assets', 'images', f'{piece}.png')
        try:
            image = pygame.image.load(path).convert_alpha()
            PIECE_IMAGES[piece] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
        except pygame.error as e:
            print(f"Erro ao carregar imagem {path}: {e}")
            print("Certifique-se de que as imagens estão na pasta 'assets/images'.")
            pygame.quit()
            exit()


class ChessGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Meu Jogo de Xadrez")
        self.clock = pygame.time.Clock()

        self.board = chess.Board()
        self.selected_square = None
        self.dragging_piece = False
        self.drag_offset = (0, 0)
        self.game_over = False  # Novo estado para o fim do jogo

        # --- Configuração da IA ---
        self.player_is_white = True  # Jogador humano joga com as brancas
        self.ai_engine = ChessEngine(depth=2)  # Profundidade inicial da IA (Elo baixo)
        # Profundidade 1-2 é bem fraca. 3-4 já é um desafio.
        # Aumentar muito a profundidade pode deixar a IA lenta.

        load_piece_images()

    def _get_square_coords(self, row, col):
        return col * SQUARE_SIZE, row * SQUARE_SIZE

    def _get_square_from_coords(self, x, y):
        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE
        return row, col

    def draw_board(self):
        self.screen.fill((0, 0, 0))
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = LIGHT_SQUARE_COLOR if (row + col) % 2 == 0 else DARK_SQUARE_COLOR
                pygame.draw.rect(self.screen, color,
                                 (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        if self.selected_square:
            row, col = self.selected_square
            pygame.draw.rect(self.screen, SELECTED_SQUARE_COLOR,
                             (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

            legal_moves = [move.to_square for move in self.board.legal_moves if
                           move.from_square == chess.square(col, 7 - row)]
            for move_square in legal_moves:
                move_col = chess.square_file(move_square)
                move_row = 7 - chess.square_rank(move_square)
                pygame.draw.circle(self.screen, VALID_MOVE_COLOR,
                                   (move_col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                    move_row * SQUARE_SIZE + SQUARE_SIZE // 2),
                                   SQUARE_SIZE // 4)

        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            if king_square is not None:
                king_col = chess.square_file(king_square)
                king_row = 7 - chess.square_rank(king_square)
                pygame.draw.rect(self.screen, CHECK_SQUARE_COLOR,
                                 (king_col * SQUARE_SIZE, king_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

    def draw_pieces(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                if piece:
                    piece_symbol = piece.symbol()
                    piece_key = (f'b{piece_symbol.upper()}' if piece_symbol.islower()
                                 else f'w{piece_symbol.upper()}')

                    if PIECE_IMAGES.get(piece_key):
                        if not (self.dragging_piece and
                                (row, col) == self.selected_square_on_board):
                            self.screen.blit(PIECE_IMAGES[piece_key], (col * SQUARE_SIZE, row * SQUARE_SIZE))

        if self.dragging_piece and self.selected_piece_image:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.screen.blit(self.selected_piece_image,
                             (mouse_x - self.drag_offset[0], mouse_y - self.drag_offset[1]))

    def handle_mouse_down(self, event):
        if self.game_over: return  # Não permite movimentos se o jogo acabou
        if (self.board.turn == chess.WHITE and not self.player_is_white) or \
                (self.board.turn == chess.BLACK and self.player_is_white):
            return  # Não permite clique se não for a vez do jogador humano

        x, y = event.pos
        row, col = self._get_square_from_coords(x, y)
        self.selected_square = (row, col)

        from_square = chess.square(col, 7 - row)
        piece = self.board.piece_at(from_square)

        # Apenas seleciona a peça se for da cor do jogador humano
        if piece and ((piece.color == chess.WHITE and self.player_is_white) or \
                      (piece.color == chess.BLACK and not self.player_is_white)):
            piece_symbol = piece.symbol()
            piece_key = (f'b{piece_symbol.upper()}' if piece_symbol.islower()
                         else f'w{piece_symbol.upper()}')

            self.selected_piece_image = PIECE_IMAGES.get(piece_key)
            if self.selected_piece_image:
                self.dragging_piece = True
                self.selected_square_on_board = (row, col)
                self.drag_offset = (x - col * SQUARE_SIZE, y - row * SQUARE_SIZE)
        else:
            self.selected_square = None

    def handle_mouse_up(self, event):
        if self.game_over: return  # Não permite movimentos se o jogo acabou
        if not self.dragging_piece: return  # Não faz nada se não estava arrastando

        x, y = event.pos
        target_row, target_col = self._get_square_from_coords(x, y)

        from_row, from_col = self.selected_square

        from_square = chess.square(from_col, 7 - from_row)
        to_square = chess.square(target_col, 7 - target_row)

        move = chess.Move(from_square, to_square)

        # Lidar com promoção de peão (simplificado: sempre Rainha)
        if self.board.piece_at(from_square) == chess.Piece(chess.PAWN, self.board.turn) and \
                (chess.square_rank(to_square) == 7 or chess.square_rank(to_square) == 0):
            move = chess.Move(from_square, to_square, promotion=chess.QUEEN)

        if move in self.board.legal_moves:
            self.board.push(move)
            print(f"Movimento do Jogador: {move.uci()}")
            self.check_game_status()  # Verifica o status do jogo após o movimento humano

        self.selected_square = None
        self.dragging_piece = False
        self.selected_piece_image = None
        self.selected_square_on_board = None

    def check_game_status(self):
        """Verifica se o jogo terminou e imprime o resultado."""
        if self.board.is_checkmate():
            print(f"Checkmate! {'Brancas' if self.board.turn == chess.BLACK else 'Pretas'} venceram!")
            self.game_over = True
        elif self.board.is_stalemate():
            print("Afogamento! Jogo empatado.")
            self.game_over = True
        elif self.board.is_insufficient_material():
            print("Material Insuficiente! Jogo empatado.")
            self.game_over = True
        elif self.board.is_seventyfive_moves():
            print("Regra dos 75 movimentos! Jogo empatado.")
            self.game_over = True
        elif self.board.is_fivefold_repetition():
            print("Repetição de 5 posições! Jogo empatado.")
            self.game_over = True
        elif self.board.is_fifty_moves():  # Regra dos 50 movimentos
            print("Regra dos 50 movimentos! Jogo empatado.")
            self.game_over = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_mouse_down(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.handle_mouse_up(event)
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_piece:
                    pass

        # Lógica para a jogada da IA
        if not self.game_over and \
                ((self.board.turn == chess.BLACK and self.player_is_white) or \
                 (self.board.turn == chess.WHITE and not self.player_is_white)):

            # Pequeno atraso para simular "pensamento" da IA e evitar que seja instantâneo
            # time.sleep(0.1) # Removido para evitar congelamento da UI em buscas profundas

            ai_move = self.ai_engine.find_best_move(self.board)
            if ai_move:
                self.board.push(ai_move)
                print(f"Movimento da IA: {ai_move.uci()}")
                self.check_game_status()  # Verifica o status do jogo após o movimento da IA

        return True

    def run(self):
        running = True
        while running:
            running = self.handle_events()

            self.draw_board()
            self.draw_pieces()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()