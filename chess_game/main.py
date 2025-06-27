# meu_xadrez/chess_game/main.py (VERSÃO FINAL E COMPLETA)
import pygame
import chess
import os
import time
from chess_game.engine import ChessEngine

# --- Constantes de Cores e Tamanhos ---
BOARD_WIDTH, PANEL_WIDTH = 800, 400
WIDTH, HEIGHT = BOARD_WIDTH + PANEL_WIDTH, 800
BOARD_SIZE, SQUARE_SIZE, FPS = 8, BOARD_WIDTH // 8, 60

# --- Cores ---
LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR = (238, 238, 210), (118, 150, 86)
SELECTED_SQUARE_COLOR = (186, 202, 68, 150)
VALID_MOVE_COLOR = (40, 40, 40, 100)
CHECK_SQUARE_COLOR = (255, 70, 70)
PANEL_COLOR, BUTTON_COLOR, TEXT_COLOR = (45, 45, 45), (80, 80, 80), (240, 240, 240)
HIGHLIGHT_COLOR, DISABLED_COLOR = (110, 110, 110), (60, 60, 60)
BLUNDER_COLOR, MISTAKE_COLOR, INACCURACY_COLOR = (255, 80, 80), (255, 160, 50), (255, 255, 80)
GOOD_MOVE_COLOR, BEST_MOVE_COLOR, SUGGESTION_ARROW_COLOR = (120, 220, 120), (100, 180, 255), (0, 100, 255, 200)
PROMOTION_BG_COLOR = (80, 80, 80, 200)

PIECE_IMAGES = {}


def load_piece_images():
    script_dir = os.path.dirname(__file__)
    pieces = ['bR', 'bN', 'bB', 'bQ', 'bK', 'bP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'wP']
    for piece in pieces:
        path = os.path.join(script_dir, '..', 'assets', 'images', f'{piece}.png')
        try:
            image = pygame.image.load(path).convert_alpha()
            PIECE_IMAGES[piece] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
        except pygame.error as e:
            print(f"Erro ao carregar imagem: {path} - {e}")
            pygame.quit()
            exit()


class ChessGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Xadrez com Análise")
        self.clock = pygame.time.Clock()
        load_piece_images()
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 48)
        self.small_font = pygame.font.SysFont('Arial', 18)
        self.history_font = pygame.font.SysFont('Consolas', 20)
        self.reset_game_variables()

    def reset_game_variables(self):
        self.board = None
        self.ai_engine = ChessEngine()
        self.player_is_white = True
        self.game_over = False
        self.selected_square = None
        self.dragging_piece = False
        self.drag_offset = (0, 0)
        self.selected_piece_image = None
        self.selected_square_on_board = None
        self.analysis_message = ""
        self.analysis_message_color = TEXT_COLOR
        self.best_move_arrow = None
        self.history_scroll_y = 0
        self.promotion_move_candidate = None
        self.promotion_target_square = None
        self.previous_game_state = None
        self.game_state = "MENU"
        self.selected_elo = 400
        self.elo_options = [100, 400, 800, 1200, 1600]

    def _get_square_from_coords(self, x, y):
        if x >= BOARD_WIDTH:
            return None, None
        return y // SQUARE_SIZE, x // SQUARE_SIZE

    def draw_board(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color = LIGHT_SQUARE_COLOR if (r + c) % 2 == 0 else DARK_SQUARE_COLOR
                pygame.draw.rect(self.screen, color, (c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        if self.selected_square and self.selected_square[0] is not None:
            r, c = self.selected_square
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(SELECTED_SQUARE_COLOR)
            self.screen.blit(s, (c * SQUARE_SIZE, r * SQUARE_SIZE))

    def draw_move_hints(self):
        if not self.selected_square or self.selected_square[0] is None or not self.board:
            return

        r, c = self.selected_square
        from_sq = chess.square(c, 7 - r)
        piece = self.board.piece_at(from_sq)

        is_human_turn = (self.game_state == "PLAYING_VS_PLAYER") or \
                        (self.board and ((self.board.turn and self.player_is_white) or (
                                    not self.board.turn and not self.player_is_white)))

        can_show_hints = is_human_turn and piece and piece.color == self.board.turn

        if can_show_hints:
            for move in self.board.legal_moves:
                if move.from_square == from_sq:
                    mr, mc = 7 - chess.square_rank(move.to_square), chess.square_file(move.to_square)
                    center = (mc * SQUARE_SIZE + SQUARE_SIZE // 2, mr * SQUARE_SIZE + SQUARE_SIZE // 2)
                    if self.board.is_capture(move):
                        pygame.draw.circle(self.screen, VALID_MOVE_COLOR, center, SQUARE_SIZE // 2, 6)
                    else:
                        pygame.draw.circle(self.screen, VALID_MOVE_COLOR, center, SQUARE_SIZE // 6)

    def draw_check_and_arrows(self):
        if not self.board:
            return

        if self.board.is_check():
            k_sq = self.board.king(self.board.turn)
            kr, kc = 7 - chess.square_rank(k_sq), chess.square_file(k_sq)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((*CHECK_SQUARE_COLOR, 128))
            self.screen.blit(s, (kc * SQUARE_SIZE, kr * SQUARE_SIZE))

        if self.best_move_arrow:
            f, t = self.best_move_arrow
            start = (chess.square_file(f) * SQUARE_SIZE + SQUARE_SIZE // 2,
                     (7 - chess.square_rank(f)) * SQUARE_SIZE + SQUARE_SIZE // 2)
            end = (chess.square_file(t) * SQUARE_SIZE + SQUARE_SIZE // 2,
                   (7 - chess.square_rank(t)) * SQUARE_SIZE + SQUARE_SIZE // 2)

            pygame.draw.line(self.screen, SUGGESTION_ARROW_COLOR, start, end, 12)
            vec = pygame.math.Vector2(end) - pygame.math.Vector2(start)
            if vec.length() > 0:
                angle = vec.angle_to(pygame.math.Vector2(1, 0))
                points = [(0, 0), (-25, -12), (-25, 12)]
                r_pts = [pygame.math.Vector2(p).rotate(-angle) + end for p in points]
                pygame.draw.polygon(self.screen, SUGGESTION_ARROW_COLOR, r_pts)

    def draw_pieces(self):
        if not self.board: return
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.board.piece_at(chess.square(c, 7 - r))
                if p:
                    key = f"{'b' if p.color == chess.BLACK else 'w'}{p.symbol().upper()}"
                    if PIECE_IMAGES.get(key) and not (self.dragging_piece and (r, c) == self.selected_square_on_board):
                        self.screen.blit(PIECE_IMAGES[key], (c * SQUARE_SIZE, r * SQUARE_SIZE))
        if self.dragging_piece and self.selected_piece_image:
            mx, my = pygame.mouse.get_pos()
            self.screen.blit(self.selected_piece_image, (mx - self.drag_offset[0], my - self.drag_offset[1]))

    def draw_side_panel(self):
        pygame.draw.rect(self.screen, PANEL_COLOR, (BOARD_WIDTH, 0, PANEL_WIDTH, HEIGHT))
        self.screen.blit(self.font.render("Análise e Histórico", True, TEXT_COLOR), (BOARD_WIDTH + 20, 20))
        pygame.draw.line(self.screen, HIGHLIGHT_COLOR, (BOARD_WIDTH + 20, 55), (WIDTH - 20, 55))
        if self.board:
            ev = self.ai_engine.get_position_evaluation(self.board) * (1 if self.board.turn == chess.WHITE else -1)
            self.screen.blit(self.small_font.render(f"Avaliação: {ev / 100:+.2f}", True, TEXT_COLOR),
                             (BOARD_WIDTH + 20, 70))

        self.draw_wrapped_text(self.analysis_message, self.analysis_message_color,
                               pygame.Rect(BOARD_WIDTH + 20, 150, PANEL_WIDTH - 40, 160))
        self.screen.blit(self.font.render("Histórico", True, TEXT_COLOR), (BOARD_WIDTH + 20, 320))
        pygame.draw.line(self.screen, HIGHLIGHT_COLOR, (BOARD_WIDTH + 20, 355), (WIDTH - 20, 355))
        self.draw_move_history()

        self.undo_button_rect = pygame.Rect(BOARD_WIDTH + 20, 105, 140, 35)
        can_undo = self.board and len(self.board.move_stack) > 0
        pygame.draw.rect(self.screen, BUTTON_COLOR if can_undo else DISABLED_COLOR, self.undo_button_rect,
                         border_radius=5)
        self.screen.blit(self.small_font.render("Voltar Jogada", True, TEXT_COLOR),
                         self.small_font.render("Voltar Jogada", True, TEXT_COLOR).get_rect(
                             center=self.undo_button_rect.center))

    def draw_wrapped_text(self, text, color, rect):
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = f" {word}" if current_line else word
            if self.small_font.size(current_line + test_line)[0] < rect.width:
                current_line += test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        y = rect.top
        for line in lines:
            if y + self.small_font.get_height() > rect.bottom:
                break
            text_surf = self.small_font.render(line, True, color)
            self.screen.blit(text_surf, (rect.left, y))
            y += self.small_font.get_height()

    def draw_move_history(self):
        area = pygame.Rect(BOARD_WIDTH + 10, 370, PANEL_WIDTH - 20, HEIGHT - 390)
        if not self.board or not self.board.move_stack: return

        t_board, san_moves = chess.Board(), []
        for move in self.board.move_stack:
            try:
                san_moves.append(t_board.san(move))
                t_board.push(move)
            except:
                break

        history_lines = []
        for i in range(0, len(san_moves), 2):
            move_num = (i // 2) + 1
            white_move = san_moves[i]
            if i + 1 < len(san_moves):
                black_move = san_moves[i + 1]
                history_lines.append(f"{move_num: >2}. {white_move:<7} {black_move:<7}")
            else:
                history_lines.append(f"{move_num: >2}. {white_move:<7}")

        h = len(history_lines) * self.history_font.get_height()
        surface = pygame.Surface((area.width, h))
        surface.fill(PANEL_COLOR)
        for i, line in enumerate(history_lines):
            surface.blit(self.history_font.render(line, True, TEXT_COLOR), (5, i * self.history_font.get_height()))

        self.history_scroll_y = max(-max(0, h - area.height), min(0, self.history_scroll_y))
        self.screen.blit(surface, area.topleft, (0, -self.history_scroll_y, area.width, area.height))

    def handle_mouse_down_playing(self, event):
        if self.game_over: return

        is_human_turn = (self.game_state == "PLAYING_VS_PLAYER") or \
                        (self.board and ((self.board.turn and self.player_is_white) or (
                                    not self.board.turn and not self.player_is_white)))
        if not is_human_turn: return

        x, y = event.pos
        r, c = self._get_square_from_coords(x, y)
        if r is None: return

        self.analysis_message = ""
        self.best_move_arrow = None
        self.selected_square = (r, c)
        from_sq = chess.square(c, 7 - r)
        piece = self.board.piece_at(from_sq)

        if piece and piece.color == self.board.turn:
            if self.game_state == "ANALYSIS":
                best_move = self.ai_engine.find_best_move(self.board.copy())
                if best_move:
                    self.best_move_arrow = (best_move.from_square, best_move.to_square)

            key = f"{'b' if piece.color == chess.BLACK else 'w'}{piece.symbol().upper()}"
            if img := PIECE_IMAGES.get(key):
                self.selected_piece_image = img
                self.dragging_piece = True
                self.selected_square_on_board = (r, c)
                self.drag_offset = (x - c * SQUARE_SIZE, y - r * SQUARE_SIZE)
        else:
            self.selected_square = None

    def handle_mouse_up_playing(self, event):
        if not self.dragging_piece:
            self.selected_square = None
            return

        x, y = event.pos
        tr, tc = self._get_square_from_coords(x, y)
        self.dragging_piece = False
        if tr is None or self.selected_square is None:
            self.selected_square = None
            return

        fr, fc = self.selected_square
        from_sq, to_sq = chess.square(fc, 7 - fr), chess.square(tc, 7 - tr)
        piece = self.board.piece_at(from_sq)
        if not piece:
            self.selected_square = None
            return

        is_promo = piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in [0, 7]
        is_legal = any(m.from_square == from_sq and m.to_square == to_sq for m in self.board.legal_moves)

        if is_legal:
            if is_promo:
                self.promotion_move_candidate, self.promotion_target_square = chess.Move(from_sq, to_sq), to_sq
                self.previous_game_state, self.game_state = self.game_state, "PROMOTION_SELECTION"
            else:
                self.make_player_move(chess.Move(from_sq, to_sq))
        else:
            self.analysis_message, self.analysis_message_color = "Movimento ilegal.", BLUNDER_COLOR
        self.selected_square = None

    def make_player_move(self, move):
        board_before = self.board.copy()
        try:
            san = self.board.san(move)
        except:
            return

        if self.game_state in ["PLAYING_ANALYZE", "ANALYSIS"]:
            m_type, b_move, s_drop, expl = self.ai_engine.analyze_move(board_before, move)
            self.analysis_message = f"Sua jogada ({san}): {m_type}! {expl}"
            self.analysis_message_color = self.get_color_for_move_type(m_type)

            if self.game_state == "PLAYING_ANALYZE":
                self.best_move_arrow = (b_move.from_square, b_move.to_square) if m_type not in ["Best Move",
                                                                                                "Good Move"] and b_move else None
            elif self.game_state == "ANALYSIS":
                self.best_move_arrow = None

        self.board.push(move)
        self.check_game_status()

        is_ai_turn = self.game_state in ["PLAYING_VS_AI", "PLAYING_ANALYZE", "ANALYSIS"]
        if not self.game_over and is_ai_turn:
            pygame.display.flip()
            self.make_ai_move()

    def make_ai_move(self):
        print("IA pensando...")
        pygame.time.wait(200)
        ai_move = self.ai_engine.find_best_move(self.board)
        if ai_move:
            self.board.push(ai_move)
            print(f"Movimento da IA: {ai_move.uci()}")
        self.check_game_status()

    def get_color_for_move_type(self, move_type):
        return {"Blunder": BLUNDER_COLOR, "Mistake": MISTAKE_COLOR, "Inaccuracy": INACCURACY_COLOR,
                "Good Move": GOOD_MOVE_COLOR, "Best Move": BEST_MOVE_COLOR, "Melhor Defesa": BEST_MOVE_COLOR}.get(
            move_type, TEXT_COLOR)

    def check_game_status(self):
        if self.board and self.board.outcome():
            self.game_over = True
            outcome = self.board.outcome()
            winner = "Brancas vencem" if outcome.winner else "Pretas vencem" if outcome.winner is False else "Empate"
            term = outcome.termination.name.replace('_', ' ').title()
            self.analysis_message = f"FIM DE JOGO: {winner} por {term}."
            self.analysis_message_color, self.best_move_arrow = TEXT_COLOR, None

    def start_game(self, mode):
        self.reset_game_variables()
        self.game_state = mode
        self.board = chess.Board()
        self.analysis_message = "Boa sorte!"
        self.ai_engine.set_difficulty_elo(self.selected_elo)
        if mode == "ANALYSIS":
            self.analysis_message = "Análise Livre: Clique na sua peça para ver a sugestão."
        if not self.player_is_white and mode in ["PLAYING_VS_AI", "PLAYING_ANALYZE", "ANALYSIS"]:
            self.make_ai_move()

    def draw_menu(self):
        self.screen.fill((50, 50, 50))
        title = self.big_font.render("Meu Jogo de Xadrez", True, TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 5)))

        buttons = {"J. vs IA (Normal)": (WIDTH // 2 - 160, HEIGHT // 2 - 130, 320, 50),
                   "Jogar com Análise": (WIDTH // 2 - 160, HEIGHT // 2 - 70, 320, 50),
                   "Análise Livre": (WIDTH // 2 - 160, HEIGHT // 2 - 10, 320, 50),
                   "Jogar PvP": (WIDTH // 2 - 160, HEIGHT // 2 + 50, 320, 50)}
        self.menu_buttons = {}
        for text, (x, y, w, h) in buttons.items():
            rect = pygame.Rect(x, y, w, h)
            self.menu_buttons[text] = rect
            pygame.draw.rect(self.screen, BUTTON_COLOR, rect, border_radius=10)
            text_surf = self.font.render(text, True, TEXT_COLOR)
            self.screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        color_label = self.font.render("Jogar como:", True, TEXT_COLOR)
        self.screen.blit(color_label, color_label.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120)))
        self.white_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 150, 90, 40)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR if self.player_is_white else BUTTON_COLOR, self.white_rect,
                         border_radius=5)
        self.screen.blit(self.font.render("Brancas", True, TEXT_COLOR),
                         self.font.render("Brancas", True, TEXT_COLOR).get_rect(center=self.white_rect.center))
        self.black_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2 + 150, 90, 40)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR if not self.player_is_white else BUTTON_COLOR, self.black_rect,
                         border_radius=5)
        self.screen.blit(self.font.render("Pretas", True, TEXT_COLOR),
                         self.font.render("Pretas", True, TEXT_COLOR).get_rect(center=self.black_rect.center))

        elo_label = self.font.render("Dificuldade (Elo):", True, TEXT_COLOR)
        self.screen.blit(elo_label, elo_label.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 220)))
        total_w = sum(80 for _ in self.elo_options) + (len(self.elo_options) - 1) * 15
        start_x = WIDTH // 2 - total_w // 2
        for i, elo in enumerate(self.elo_options):
            rect = pygame.Rect(start_x + i * 95, HEIGHT // 2 + 250, 80, 40)
            setattr(self, f'elo_button_rect_{elo}', rect)
            pygame.draw.rect(self.screen, HIGHLIGHT_COLOR if self.selected_elo == elo else BUTTON_COLOR, rect,
                             border_radius=5)
            self.screen.blit(self.font.render(str(elo), True, TEXT_COLOR),
                             self.font.render(str(elo), True, TEXT_COLOR).get_rect(center=rect.center))

    def handle_menu_click(self, event):
        pos = event.pos
        if self.menu_buttons["J. vs IA (Normal)"].collidepoint(pos):
            self.start_game("PLAYING_VS_AI")
        elif self.menu_buttons["Jogar com Análise"].collidepoint(pos):
            self.start_game("PLAYING_ANALYZE")
        elif self.menu_buttons["Análise Livre"].collidepoint(pos):
            self.start_game("ANALYSIS")
        elif self.menu_buttons["Jogar PvP"].collidepoint(pos):
            self.start_game("PLAYING_VS_PLAYER")
        elif self.white_rect.collidepoint(pos):
            self.player_is_white = True
        elif self.black_rect.collidepoint(pos):
            self.player_is_white = False
        for elo in self.elo_options:
            if hasattr(self, f'elo_button_rect_{elo}') and getattr(self, f'elo_button_rect_{elo}').collidepoint(pos):
                self.selected_elo = elo

    def handle_undo_click(self):
        if self.game_over or not self.board or not self.board.move_stack: return
        num_pops = 1
        if self.game_state in ["PLAYING_VS_AI", "PLAYING_ANALYZE", "ANALYSIS"]: num_pops = 2
        if len(self.board.move_stack) >= num_pops:
            for _ in range(num_pops): self.board.pop()
        self.analysis_message, self.analysis_message_color, self.best_move_arrow = "Jogada desfeita.", TEXT_COLOR, None
        self.game_over = False

    def handle_promotion_selection_click(self, event):
        if not self.promotion_move_candidate: return
        x, y = event.pos
        target_col = chess.square_file(self.promotion_target_square)
        start_y = 0 if chess.square_rank(self.promotion_target_square) == 7 else HEIGHT - (SQUARE_SIZE * 4)
        if not (target_col * SQUARE_SIZE <= x < (target_col + 1) * SQUARE_SIZE and start_y <= y < start_y + (
                SQUARE_SIZE * 4)):
            self.game_state = self.previous_game_state
            self.promotion_move_candidate = self.promotion_target_square = None
            return

        promo_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        choice_idx = (y - start_y) // SQUARE_SIZE
        if 0 <= choice_idx < len(promo_pieces):
            final_move = chess.Move(self.promotion_move_candidate.from_square, self.promotion_move_candidate.to_square,
                                    promotion=promo_pieces[choice_idx])
            if final_move in self.board.legal_moves:
                self.game_state = self.previous_game_state
                self.make_player_move(final_move)
        self.promotion_move_candidate, self.promotion_target_square = None, None

    def draw_promotion_selection(self):
        if not self.promotion_target_square: return
        target_col, is_white = chess.square_file(self.promotion_target_square), self.board.turn == chess.WHITE
        start_y = 0 if chess.square_rank(self.promotion_target_square) == 7 else HEIGHT - (SQUARE_SIZE * 4)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE * 4), pygame.SRCALPHA)
        s.fill(PROMOTION_BG_COLOR)
        self.screen.blit(s, (target_col * SQUARE_SIZE, start_y))
        for i, sym in enumerate(['Q', 'R', 'B', 'N']):
            if img := PIECE_IMAGES.get(f"{'w' if is_white else 'b'}{sym}"):
                self.screen.blit(img, (target_col * SQUARE_SIZE, start_y + i * SQUARE_SIZE))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if self.game_state == "PROMOTION_SELECTION":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: self.handle_promotion_selection_click(
                    event)
                continue
            if self.game_state != "MENU":
                if event.type == pygame.MOUSEWHEEL: self.history_scroll_y += event.y * 30
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_state == "MENU":
                    self.handle_menu_click(event)
                else:
                    if pygame.Rect(WIDTH - 160, 10, 140, 40).collidepoint(
                        event.pos): self.reset_game_variables(); return True
                    if hasattr(self, 'undo_button_rect') and self.undo_button_rect.collidepoint(
                        event.pos): self.handle_undo_click(); continue
                    self.handle_mouse_down_playing(event)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.game_state not in ["MENU",
                                                                                                    "PROMOTION_SELECTION"]:
                self.handle_mouse_up_playing(event)
        return True

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            if not running: break
            self.screen.fill(PANEL_COLOR)
            if self.game_state == "MENU":
                self.draw_menu()
            else:
                self.draw_board()
                self.draw_move_hints()
                self.draw_pieces()
                self.draw_check_and_arrows()
                self.draw_side_panel()
                if self.game_state == "PROMOTION_SELECTION":
                    self.draw_promotion_selection()
                menu_r = pygame.Rect(WIDTH - 160, 10, 140, 40)
                pygame.draw.rect(self.screen, BUTTON_COLOR, menu_r, border_radius=5)
                self.screen.blit(self.small_font.render("Menu Principal", True, TEXT_COLOR),
                                 self.small_font.render("Menu Principal", True, TEXT_COLOR).get_rect(
                                     center=menu_r.center))
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()