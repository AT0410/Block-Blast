import copy
from typing import List, Tuple, Optional
import numpy as np
from main import BlockBlast, SCREEN, FPS, BG_COLOR
import pygame

class BlockBlastAI:
    def __init__(self, game: BlockBlast):
        self.game = game
        self.weights = {
            'combo_multiplier': 500,
            'clear_bonus': 500,
            'density_penalty': -10,
            'edge_bonus': 20,
            'future_viability': 300,
            'complete_clear_bonus': 5000,
            'clumping': 10
        }
        
        
    ################################################
    # SCORE EVALUATION
    def evaluate_board_state(self, grid, combo, since_clear):
        """Evaluates the current board state with multiple criteria"""
        score = 0
        
        # 1. Combo preservation (most important)
        if since_clear < 3:
            score += self.weights['combo_multiplier'] * combo
        else:
            score -= self.weights['combo_multiplier'] * 2  # Penalty for losing combo
        
        # 2. Clear potential analysis
        clear_potential = self.analyze_clear_potential(grid)
        score += self.weights['clear_bonus'] * clear_potential
        
        # 3. Board density management
        density = self.calculate_density(grid)
        score += self.weights['density_penalty'] * density
        
        # 4. Edge utilization bonus
        edge_score = self.calculate_edge_utilization(grid)
        score += self.weights['edge_bonus'] * edge_score
        
        # 5. Future placement viability
        viability = self.calculate_future_viability(grid)
        score += self.weights['future_viability'] * viability
        
        # 6. Complete Clear
        if all(cell == self.game.grid_bg_colour for row in grid for cell in row):
            score += self.weights['complete_clear_bonus']
        
        return score
    
    def analyze_clear_potential(self, grid):
        """Analyzes potential for clearing multiple lines"""
        potential = 0
        
        # rows
        for i in range(len(grid)):
            filled_cells = sum(1 for cell in grid[i] if cell != self.game.grid_bg_colour)
            if filled_cells >= 5:
                potential += filled_cells * 2
        
        # cols
        for j in range(len(grid[0])):
            filled_cells = sum(1 for i in range(len(grid)) if grid[i][j] != self.game.grid_bg_colour)
            if filled_cells >= 5:
                potential += filled_cells * 2
        
        return potential
    
    def calculate_density(self, grid):
        """Calculates board density to avoid overcrowding"""
        total_cells = len(grid) * len(grid[0])
        filled_cells = sum(1 for row in grid for cell in row if cell != self.game.grid_bg_colour)
        return filled_cells / total_cells
    
    def calculate_edge_utilization(self, grid):
        """Rewards placing blocks sticking to edges and corners"""
        edge_score = 0
        size = len(grid)
        
        # Corner utilization
        corners = [(0,0), (0,size-1), (size-1,0), (size-1,size-1)]
        for r, c in corners:
            if grid[r][c] != self.game.grid_bg_colour:
                edge_score += 5
        
        # Edge utilization
        for i in range(size):
            if grid[0][i] != self.game.grid_bg_colour:  # Top edge
                edge_score += 2
            if grid[size-1][i] != self.game.grid_bg_colour:  # Bottom edge
                edge_score += 2
            if grid[i][0] != self.game.grid_bg_colour:  # Left edge
                edge_score += 2
            if grid[i][size-1] != self.game.grid_bg_colour:  # Right edge
                edge_score += 2
        
        return edge_score
    
    def calculate_future_viability(self, grid):
        """Estimates how many future blocks can be placed"""
        viability_score = 0
        
        # Test placability of common block shapes
        
        for block in self.game.block_shapes:
            placement_count = 0
            for r in range(len(grid)):
                for c in range(len(grid[0])):
                    if self.game.can_place_block(grid, block, r, c):
                        placement_count += 1
            viability_score += placement_count
        
        return viability_score

    def calculate_clumping_score(self, grid):
        """Rewards blocks clumped together in rectangles to enable multi-row/col clears"""
        
    ################################################
    # Simulation and evaluation
    
    def evaluate_move(self, block_idx, block, colour, row, col, depth):
        """Evaluate a specific move with lookahead"""
        # Simulate placement
        grid = self.game.get_deepcopy()
        self.simulate_placement(grid, block, row, col, colour)
        lines_cleared = self.simulate_clear(grid)
        
        # Calculate immediate score
        immediate_score = len([cell for row in block for cell in row if cell == 1])  # Placement points
        
        # Add clearing bonus
        if lines_cleared > 0:
            combo_multiplier = self.game.combo + 1
            clear_bonus = combo_multiplier * 10 * self.game.clear_multiplier[min(lines_cleared - 1, 5)]
            immediate_score += clear_bonus
            new_since_clear = 0
            new_combo = self.game.combo + 1
        else:
            new_since_clear = self.game.since_clear + 1
            new_combo = self.game.combo if new_since_clear < 3 else 0
        
        # Add complete clear bonus
        if all(cell == self.game.grid_bg_colour for row in grid for cell in row):
            immediate_score += 300
        
        # Evaluate board state
        state_score = self.evaluate_board_state(grid, new_combo, new_since_clear)
        
        return immediate_score + state_score
    
    
    def simulate_placement(self, grid, block, top, left, colour):
        """Simulate placing a block and return new grid state"""
        self.game.place_block(grid, block, top, left, colour)
    
    def simulate_clear(self, grid):
        """Simulate clearing lines and return (new_grid, lines_cleared)"""
        lines_cleared = self.game.clear(grid)
        return lines_cleared
    
    def find_best_move(self, depth=2):
        """Find the best move using lookahead search"""
        available_blocks = []
        for i in range(3):
            if not self.game.placed_preview[i]:
                available_blocks.append((i, self.game.current_blocks[i]))
        
        if not available_blocks:
            return None
        
        best_move = None
        best_score = float('-inf')
        
        # Try each available block
        for block_idx, (block, colour) in available_blocks:
            # Try all possible positions
            for row in range(self.game.grid_size):
                for col in range(self.game.grid_size):
                    if self.game.can_place_block(self.game.grid, block, row, col):
                        # Simulate this move
                        move_score = self.evaluate_move(block_idx, block, colour, row, col, depth)
                        
                        if move_score > best_score:
                            best_score = move_score
                            best_move = (block_idx, row, col)
        
        return best_move
    
    def get_ai_move(self):
        return self.find_best_move()

# Integration with the main game
class AIBlockBlast(BlockBlast):
    def __init__(self):
        super().__init__()
        self.ai = BlockBlastAI(self)
        self.auto_play = False
    
    def ai_make_move(self):
        """Have AI make the best move"""
        if not self.is_game_over(self.grid):
            best_move = self.ai.find_best_move()
            if best_move:
                block_idx, row, col = best_move
                block, colour = self.current_blocks[block_idx]
                
                if self.can_place_block(self.grid, block, row, col):
                    self.place_block(self.grid, block, row, col, colour)
                    clear_num = self.clear(self.grid)
                    self.increment_score(self.grid, block, clear_num)
                    
                    self.placed_preview[block_idx] = True
                    
                    # Refill blocks when all placed
                    if all(self.placed_preview):
                        self.current_blocks = self.get_preview_blocks()
                        self.placed_preview = [False, False, False]
                        
                        while self.is_game_over(self.grid):
                            self.current_blocks = self.get_preview_special_blocks()

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
