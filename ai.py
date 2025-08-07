import copy
from typing import List, Tuple, Optional
import numpy as np
from blockblast import BlockBlast, SCREEN, FPS, BG_COLOR
import pygame
from itertools import permutations


class BlockBlastAI:
    def __init__(self, game: BlockBlast):
        self.game = game
        self.weights = {
            "combo_multiplier": 5,
            "clear_bonus": 30,
            "density_penalty": -5,
            "edge_bonus": 10,
            "future_viability": 10,
            "complete_clear_bonus": 5000,
            "clumping": 30,
        }

    ################################################
    # SCORE EVALUATION
    def evaluate_board_state(self, grid, combo, since_clear):
        """Evaluates the current grid state with multiple heuristics"""
        """All heuristics have range [0, 1]"""
        score = 0
        # 1. Combo preservation (most important)
        if since_clear < 3:
            score += self.weights["combo_multiplier"] * combo
        else:
            score -= self.weights["combo_multiplier"] * 2  # Penalty for losing combo

        # 2. Clear potential analysis
        clear_potential = self.analyze_clear_potential(grid)
        score += self.weights["clear_bonus"] * clear_potential

        # 3. Board density management
        density = self.calculate_density(grid)
        score += self.weights["density_penalty"] * density

        # 4. Edge utilization bonus
        edge_score = self.calculate_edge_utilization(grid)
        score += self.weights["edge_bonus"] * edge_score

        # 5. Future placement viability
        viability = self.calculate_future_viability(grid)
        score += self.weights["future_viability"] * viability

        # 6. Complete Clear
        if all(cell == self.game.grid_bg_colour for row in grid for cell in row):
            score += self.weights["complete_clear_bonus"]

        # 7. Clumping Score
        clumping = self.calculate_clumping_score(grid)
        score += clumping
        return score

    def analyze_clear_potential(self, grid):
        """Analyzes potential for clearing multiple lines"""
        potential = 0

        # rows
        for i in range(len(grid)):
            filled_cells = sum(
                1 for cell in grid[i] if cell != self.game.grid_bg_colour
            )
            if filled_cells >= 5:
                potential += filled_cells

        # cols
        for j in range(len(grid[0])):
            filled_cells = sum(
                1 for i in range(len(grid)) if grid[i][j] != self.game.grid_bg_colour
            )
            if filled_cells >= 5:
                potential += filled_cells

        return potential / (self.game.grid_size**2)

    def calculate_density(self, grid):
        """Calculates board density to avoid overcrowding"""
        total_cells = len(grid) * len(grid[0])
        filled_cells = sum(
            1 for row in grid for cell in row if cell != self.game.grid_bg_colour
        )
        return filled_cells / total_cells

    def calculate_edge_utilization(self, grid):
        """Rewards placing blocks sticking to edges and corners"""
        size = self.game.grid_size

        edge_score = 0
        max_edge_score = 2 * (size + 1) * 4

        for i in range(size):
            if grid[0][i] != self.game.grid_bg_colour:  # Top edge
                edge_score += 2
            if grid[size - 1][i] != self.game.grid_bg_colour:  # Bottom edge
                edge_score += 2
            if grid[i][0] != self.game.grid_bg_colour:  # Left edge
                edge_score += 2
            if grid[i][size - 1] != self.game.grid_bg_colour:  # Right edge
                edge_score += 2

        return edge_score / max_edge_score

    def calculate_future_viability(self, grid):
        """Estimates how many future blocks can be placed"""
        viability_score = 0
        max_viability = len(self.game.block_shapes) * (self.game.grid_size**2)

        # Test placability of common block shapes

        for block in self.game.block_shapes:
            placement_count = 0
            for r in range(len(grid)):
                for c in range(len(grid[0])):
                    if self.game.can_place_block(grid, block, r, c):
                        placement_count += 1
            viability_score += placement_count

        return viability_score / max_viability

    def calculate_clumping_score(self, grid):
        """Rewards blocks clumped together in rectangles to enable multi-row/col clears"""

        def maxrect(bars):
            stack = []
            res = 0
            for bar in bars + [-1]:

                steps = 0
                while stack and stack[-1][1] >= bar:
                    w, h = stack.pop()
                    steps += w
                    res = max(res, h * steps)
                stack.append((steps + 1, bar))

            return res

        histo = [0] * self.game.grid_size
        max_rect = 0
        for i in range(self.game.grid_size):
            for j in range(self.game.grid_size):
                if grid[i][j] == self.game.grid_bg_colour:
                    histo[j] = 0
                else:
                    histo[j] += 1
            max_rect = max(maxrect(histo), max_rect)

        clumping_score = 0
        if max_rect > 1:
            clumping_score = max_rect
        return clumping_score / (self.game.grid_size**2)

    ################################################
    # Simulation and evaluation
    def evaluate_move_sequence(self, move_sequence):
        current_grid = self.game.get_deepcopy()
        total_score = 0
        move_seq = []
        temp_combo = self.game.combo
        temp_since_clear = self.game.since_clear

        for block_i, (block, colour) in move_sequence:
            best_move_score = float("-inf")
            best_position = None
            best_resulting_grid = None
            best_combo_state = None

            # Try all positions for this block
            for row in range(self.game.grid_size):
                for col in range(self.game.grid_size):
                    if self.game.can_place_block(current_grid, block, row, col):
                        # Calculate score for this placement
                        grid = copy.deepcopy(current_grid)
                        move_score, new_combo, new_since_clear = self.evaluate_move(
                            grid, block, colour, row, col, temp_combo, temp_since_clear
                        )
                        if move_score > best_move_score:
                            best_move_score = move_score
                            best_position = (row, col)
                            best_resulting_grid = grid
                            best_combo_state = (new_combo, new_since_clear)

            # If no valid position found i.e game over, return very low score
            if best_position is None:
                return -10000, []

            # Add this move to sequence
            move_seq.append((block_i, best_position[0], best_position[1]))
            total_score += best_move_score
            current_grid = best_resulting_grid
            temp_combo, temp_since_clear = best_combo_state
        return total_score, move_seq

    def evaluate_move(self, grid, block, colour, row, col, combo, since_cleared):
        """Evaluate a specific move with lookahead"""
        # Simulate placement
        self.simulate_placement(grid, block, row, col, colour)
        lines_cleared = self.simulate_clear(grid)

        # Calculate immediate score
        immediate_score = len(
            [cell for row in block for cell in row if cell == 1]
        )  # Placement points

        # Add clearing bonus
        if lines_cleared > 0:
            combo_multiplier = combo + 1
            clear_bonus = (
                combo_multiplier * 10 * self.game.clear_multiplier[lines_cleared - 1]
            )
            immediate_score += clear_bonus
            new_since_clear = 0
            new_combo = combo + 1
        else:
            new_since_clear = since_cleared + 1
            new_combo = combo if new_since_clear < 3 else 0

        # Add complete clear bonus
        if all(cell == self.game.grid_bg_colour for row in grid for cell in row):
            immediate_score += 300

        # Evaluate board state
        state_score = self.evaluate_board_state(grid, new_combo, new_since_clear)

        return immediate_score + state_score, new_combo, new_since_clear

    def simulate_placement(self, grid, block, top, left, colour):
        """Simulate placing a block and return new grid state"""
        self.game.place_block(grid, block, top, left, colour)

    def simulate_clear(self, grid):
        """Simulate clearing lines and return (new_grid, lines_cleared)"""
        lines_cleared = self.game.clear(grid)
        return lines_cleared

    def find_best_move_sequence(self):
        move_sequences = permutations(enumerate(self.game.current_blocks))
        best_score = float("-inf")
        best_seq = None
        for seq in move_sequences:
            score, move_seq = self.evaluate_move_sequence(seq)
            if score > best_score:
                best_score = score
                best_seq = move_seq
        return best_seq


# Integration with the main game
class AIBlockBlast(BlockBlast):
    def __init__(self):
        super().__init__()
        self.ai = BlockBlastAI(self)
        self.auto_play = False
        self.moves = self.ai.find_best_move_sequence()

    def ai_make_move(self):
        """Have AI make the best move"""
        if not self.moves:
            return
        block_i, row, col = self.moves.pop(0)
        block, colour = self.current_blocks[block_i]

        self.place_block(self.grid, block, row, col, colour)
        clear_num = self.clear(self.grid)
        self.score += self.get_score_increment(self.grid, block, clear_num)

        self.placed_preview[block_i] = True

        # Refill blocks when all placed
        if all(self.placed_preview):
            self.current_blocks = self.get_preview_blocks()
            self.placed_preview = [False, False, False]

            while self.is_game_over(self.grid):
                self.current_blocks = self.get_preview_special_blocks()
            self.moves = self.ai.find_best_move_sequence()


# Modified main loop for AI
def main_ai():
    run = True
    clock = pygame.time.Clock()
    block_blast = AIBlockBlast()
    gameover = False

    while run:
        SCREEN.fill(BG_COLOR)
        block_blast.draw_board(dragging_i=None, drag_pos=(0, 0))
        if gameover:
            block_blast.draw_gameover()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    block_blast.ai_make_move()
                    if block_blast.is_game_over(block_blast.grid):
                        gameover = True
                elif event.key == pygame.K_a:
                    block_blast.auto_play = not block_blast.auto_play

        # Auto-play mode
        if block_blast.auto_play:
            block_blast.ai_make_move()
            pygame.time.wait(500)  # Slow down for visualization

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main_ai()  # Run AI version
