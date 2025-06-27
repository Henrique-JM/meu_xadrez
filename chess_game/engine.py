# meu_xadrez/chess_game/engine.py (VERSÃO FINAL COM ANÁLISE ESTRATÉGICA)
import chess
import random

PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}

PAWN_TABLE = [[0, 0, 0, 0, 0, 0, 0, 0], [50, 50, 50, 50, 50, 50, 50, 50], [10, 10, 20, 30, 30, 20, 10, 10],
              [5, 5, 10, 25, 25, 10, 5, 5], [0, 0, 0, 20, 20, 0, 0, 0], [5, -5, -10, 0, 0, -10, -5, 5],
              [5, 10, 10, -20, -20, 10, 10, 5], [0, 0, 0, 0, 0, 0, 0, 0]]
KNIGHT_TABLE = [[-50, -40, -30, -30, -30, -30, -40, -50], [-40, -20, 0, 0, 0, 0, -20, -40],
                [-30, 0, 10, 15, 15, 10, 0, -30], [-30, 5, 15, 20, 20, 15, 5, -30], [-30, 0, 15, 20, 20, 15, 0, -30],
                [-30, 5, 10, 15, 15, 10, 5, -30], [-40, -20, 0, 5, 5, 0, -20, -40],
                [-50, -40, -30, -30, -30, -30, -40, -50]]
BISHOP_TABLE = [[-20, -10, -10, -10, -10, -10, -10, -20], [-10, 0, 0, 0, 0, 0, 0, -10], [-10, 0, 5, 10, 10, 5, 0, -10],
                [-10, 5, 5, 10, 10, 5, 5, -10], [-10, 0, 10, 10, 10, 10, 0, -10], [-10, 10, 10, 10, 10, 10, 10, -10],
                [-10, 5, 0, 0, 0, 0, 5, -10], [-20, -10, -10, -10, -10, -10, -10, -20]]
ROOK_TABLE = [[0, 0, 0, 0, 0, 0, 0, 0], [5, 10, 10, 10, 10, 10, 10, 5], [-5, 0, 0, 0, 0, 0, 0, -5],
              [-5, 0, 0, 0, 0, 0, 0, -5], [-5, 0, 0, 0, 0, 0, 0, -5], [-5, 0, 0, 0, 0, 0, 0, -5],
              [-5, 0, 0, 0, 0, 0, 0, -5], [0, 0, 0, 5, 5, 0, 0, 0]]
QUEEN_TABLE = [[-20, -10, -10, -5, -5, -10, -10, -20], [-10, 0, 0, 0, 0, 0, 0, -10], [-10, 0, 5, 5, 5, 5, 0, -10],
               [-5, 0, 5, 5, 5, 5, 0, -5], [0, 0, 5, 5, 5, 5, 0, -5], [-10, 5, 5, 5, 5, 5, 0, -10],
               [-10, 0, 5, 0, 0, 0, 0, -10], [-20, -10, -10, -5, -5, -10, -10, -20]]
KING_TABLE_MIDDLE_GAME = [[-30, -40, -40, -50, -50, -40, -40, -30], [-30, -40, -40, -50, -50, -40, -40, -30],
                          [-30, -40, -40, -50, -50, -40, -40, -30], [-30, -40, -40, -50, -50, -40, -40, -30],
                          [-20, -30, -30, -40, -40, -30, -30, -20], [-10, -20, -20, -20, -20, -20, -20, -10],
                          [20, 20, 0, 0, 0, 0, 20, 20], [20, 30, 10, 0, 0, 10, 30, 20]]
KING_TABLE_END_GAME = [[-50, -40, -30, -20, -20, -30, -40, -50], [-30, -20, -10, 0, 0, -10, -20, -30],
                       [-30, -10, 20, 30, 30, 20, -10, -30], [-30, -10, 30, 40, 40, 30, -10, -30],
                       [-30, -10, 30, 40, 40, 30, -10, -30], [-30, -10, 20, 30, 30, 20, -10, -30],
                       [-30, -20, -10, 0, 0, -10, -20, -30], [-50, -40, -30, -20, -20, -30, -40, -50]]
PIECE_TABLES = {chess.PAWN: PAWN_TABLE, chess.KNIGHT: KNIGHT_TABLE, chess.BISHOP: BISHOP_TABLE, chess.ROOK: ROOK_TABLE,
                chess.QUEEN: QUEEN_TABLE}


def get_piece_position_value(piece_type, square, color, is_endgame):
    table = KING_TABLE_END_GAME if is_endgame and piece_type == chess.KING else PIECE_TABLES.get(piece_type)
    if piece_type == chess.KING and not is_endgame: table = KING_TABLE_MIDDLE_GAME
    if table:
        rank, file = chess.square_rank(square), chess.square_file(square)
        return table[7 - rank][file] if color == chess.WHITE else table[rank][file]
    return 0


class ChessEngine:
    def __init__(self, depth=2):
        self.depth = depth
        self.elo_depth_map = {100: 1, 400: 2, 800: 3, 1200: 4, 1600: 5}

    def set_difficulty_elo(self, elo):
        selected_depth = 1
        for current_elo, depth_val in sorted(self.elo_depth_map.items()):
            if elo >= current_elo:
                selected_depth = depth_val
            else:
                break
        self.depth = selected_depth
        print(f"Dificuldade da IA definida para Elo {elo}, Profundidade: {self.depth}")

    def evaluate_board(self, board: chess.Board):
        if board.is_checkmate(): return -float('inf') if board.turn == chess.WHITE else float('inf')
        if board.is_stalemate() or board.is_insufficient_material(): return 0

        score = 0;
        is_endgame = len(board.piece_map()) < 10

        for square, piece in board.piece_map().items():
            value = PIECE_VALUES.get(piece.piece_type, 0)
            value += get_piece_position_value(piece.piece_type, square, piece.color, is_endgame)
            score += value if piece.color == chess.WHITE else -value

        if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2: score += 50
        if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2: score -= 50

        for square in [chess.D4, chess.E4, chess.D5, chess.E5]:
            score += len(board.attackers(chess.WHITE, square)) * 5
            score -= len(board.attackers(chess.BLACK, square)) * 5

        for file_index in range(8):
            white_pawns = len(board.pieces(chess.PAWN, chess.WHITE).intersection(chess.BB_FILES[file_index]))
            black_pawns = len(board.pieces(chess.PAWN, chess.BLACK).intersection(chess.BB_FILES[file_index]))
            if white_pawns > 1: score -= 20 * (white_pawns - 1)
            if black_pawns > 1: score += 20 * (black_pawns - 1)
        return score

    def minimax(self, board: chess.Board, depth, alpha, beta, maximizing_player):
        if depth == 0 or board.is_game_over(): return self.evaluate_board(board)
        legal_moves = sorted(list(board.legal_moves), key=board.is_capture, reverse=True)
        if maximizing_player:
            max_eval = -float('inf')
            for move in legal_moves:
                board.push(move);
                eval = self.minimax(board, depth - 1, alpha, beta, False);
                board.pop()
                max_eval = max(max_eval, eval);
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move);
                eval = self.minimax(board, depth - 1, alpha, beta, True);
                board.pop()
                min_eval = min(min_eval, eval);
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    def find_best_move(self, board: chess.Board):
        best_move, maximizing = None, board.turn == chess.WHITE
        best_eval = -float('inf') if maximizing else float('inf')
        legal_moves = list(board.legal_moves)
        if self.depth <= 1 and legal_moves: return random.choice(legal_moves)
        random.shuffle(legal_moves)
        for move in legal_moves:
            board.push(move);
            eval = self.minimax(board, self.depth - 1, -float('inf'), float('inf'), not maximizing);
            board.pop()
            if maximizing:
                if eval > best_eval: best_eval, best_move = eval, move
            elif not maximizing:
                if eval < best_eval: best_eval, best_move = eval, move
        return best_move

    def get_position_evaluation(self, board: chess.Board):
        return self.evaluate_board(board)

    def get_move_explanation(self, board_before_move: chess.Board, move_type: str, best_move: chess.Move,
                             score_drop: float):
        if move_type == "Best Move": return "Excelente! Este é o lance mais forte, criando a maior vantagem."
        if move_type == "Good Move": return "Boa jogada! Você mantém a pressão e melhora sua posição."
        if move_type == "Melhor Defesa": return "Boa defesa. Era o melhor lance para minimizar as perdas numa posição difícil."

        explanation = ""
        if best_move:
            opportunity = ""
            if board_before_move.is_capture(best_move):
                captured = board_before_move.piece_at(best_move.to_square) or board_before_move.piece_at(
                    best_move.from_square)
                opportunity += f"capturar o/a {chess.piece_name(captured.piece_type).lower()} inimigo"

            temp_board = board_before_move.copy();
            temp_board.push(best_move)
            if temp_board.is_check():
                if opportunity: opportunity += " e"
                opportunity += " aplicar um xeque"

            if opportunity: explanation += f"A jogada ideal era {board_before_move.san(best_move)} para {opportunity}. "

        if not explanation:
            explanation = f"Esta jogada resultou em uma perda posicional de {score_drop / 100:.2f} pontos. "

        return explanation

    def analyze_move(self, board_before_move: chess.Board, player_move: chess.Move):
        analysis_depth = min(self.depth + 1, 4);
        engine = ChessEngine(depth=analysis_depth)
        if player_move not in board_before_move.legal_moves:
            return "Erro", None, 0, "Movimento ilegal detectado."

        player_color = board_before_move.turn

        eval_before = engine.evaluate_board(board_before_move.copy())
        best_move = engine.find_best_move(board_before_move.copy())

        board_after_best = board_before_move.copy()
        if best_move: board_after_best.push(best_move)
        eval_after_best = engine.evaluate_board(board_after_best)

        board_after_player = board_before_move.copy();
        board_after_player.push(player_move)
        eval_after_player = engine.evaluate_board(board_after_player)

        if player_color == chess.BLACK:
            eval_before, eval_after_best, eval_after_player = -eval_before, -eval_after_best, -eval_after_player

        score_drop_vs_best = eval_after_best - eval_after_player
        score_change_vs_previous = eval_after_player - eval_before

        BLUNDER_THRESHOLD, MISTAKE_THRESHOLD, INACCURACY_THRESHOLD = 200, 80, 30

        move_type = "Good Move"
        if score_drop_vs_best >= BLUNDER_THRESHOLD:
            move_type = "Blunder"
        elif score_drop_vs_best >= MISTAKE_THRESHOLD:
            move_type = "Mistake"
        elif score_drop_vs_best >= INACCURACY_THRESHOLD:
            move_type = "Inaccuracy"

        if move_type == "Good Move" and score_change_vs_previous < -30:
            move_type = "Inaccuracy"

        if best_move and player_move.uci() == best_move.uci():
            move_type = "Best Move" if score_change_vs_previous >= 0 else "Melhor Defesa"

        explanation = self.get_move_explanation(board_before_move, move_type, best_move, score_drop_vs_best)
        return move_type, best_move, score_drop_vs_best, explanation