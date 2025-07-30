import pygame
import sys
import random
from typing import Tuple

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 480, 800
FPS = 30
BG_COLOR = (245, 245, 245)
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.init()
pygame.display.set_caption("Block Blast")


class BlockBlast:
    def __init__(self):
        # Colours
        self.grid_bg_colour = (81, 114, 138)
        self.grid_line_colour = (13, 22, 38)
        self.block_colours = [
            (255, 99, 71),
            (100, 149, 237),
            (60, 179, 113),
            (255, 215, 0),
        ]

        # Grid
        self.grid_size = 8
        self.cell_size = 48
        self.grid_topleft = (40, 180)
        self.grid = [
            [self.grid_bg_colour] * self.grid_size for _ in range(self.grid_size)
        ]
        self.block_shapes = [
            [[1, 1, 1]],  # horizontal 3 line
            [[1, 1, 1, 1]],  # horizontal 4 line
            [[1, 1, 1, 1, 1]],  # horizontal 5 line
            [[1], [1], [1]],  # vertical 3 line
            [[1], [1], [1], [1]],  # vertical 4 line
            [[1], [1], [1], [1], [1]],  # vertical 5 line
            [[1, 1], [1, 1]],  # 2x2 square
            [[1, 1, 1], [1, 1, 1], [1, 1, 1]],  # 3x3 square
            [[1, 1], [1, 1], [1, 1]],  # 3x2 square
            [[1, 1, 1], [1, 1, 1]],  # 2x3 square
            [[1, 0, 0], [1, 1, 1]],  # horizontal l shape
            [[0, 0, 1], [1, 1, 1]],  # horizontal l shape
            [[1, 1, 1], [0, 0, 1]],  # horizontal l shape
            [[1, 1, 1], [1, 0, 0]],  # horizontal l shape
            [[1, 0], [1, 0], [1, 1]],  # vertical l shape
            [[0, 1], [0, 1], [1, 1]],  # vertical l shape
            [[1, 1], [0, 1], [0, 1]],  # vertical l shape
            [[1, 1], [1, 0], [1, 0]],  # vertical l shape
            [[1, 0, 0], [1, 0, 0], [1, 1, 1]],  # L shape
            [[0, 0, 1], [0, 0, 1], [1, 1, 1]],  # L shape
            [[1, 1, 1], [0, 0, 1], [0, 0, 1]],  # L shape
            [[1, 1, 1], [1, 0, 0], [1, 0, 0]],  # L shape
            [[1, 1], [1, 0]],  # r shape
            [[1, 1], [0, 1]],  # r shape
            [[1, 0], [1, 1]],  # r shape
            [[0, 1], [1, 1]],  # r shape
            [[0, 1], [1, 1], [0, 1]],  # t shape
            [[1, 0], [1, 1], [1, 0]],  # t shape
            [[0, 1, 0], [1, 1, 1]],  # t shape
            [[1, 1, 1], [0, 1, 0]],  # t shape
            [[1, 1, 0], [0, 1, 1]],  # z shape
            [[0, 1, 1], [1, 1, 0]],  # z shape
            [[0, 1], [1, 1], [1, 0]],  # z shape
            [[1, 0], [1, 1], [0, 1]],  # z shape
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],  # 3x3 diagonal
            [[0, 0, 1], [0, 1, 0], [1, 0, 0]],
        ]

        self.special_block_shapes = [
            [[1], [1]],  # vertical 2 line
            [[1, 1]],  # horizontal 2 line
            [[1, 0, 1], [1, 1, 1]],  # U shape
            [[1, 1, 1], [1, 0, 1]],  # U shape
            [[1, 1], [1, 0], [1, 1]],  # U shape
            [[1, 1], [0, 1], [1, 1]],  # U shape
            [[1, 0], [0, 1]],
            [[0, 1], [1, 0]],
        ]

        # preview blocks
        self.current_blocks = self.get_preview_blocks()
        self.preview_block_rects = []
        self.placed_preview = [False, False, False]

        # scoring
        self.score = 0
        self.combo = 0
        self.clear_multipler = [1, 2, 6, 12, 24, 48]
        self.since_clear = 0

    def draw_score(self):
        font = pygame.font.SysFont(None, 48)
        score_surf = font.render(f"{self.score}", True, (40, 40, 40))
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        SCREEN.blit(score_surf, score_rect)

    def draw_current_blocks(self, dragging_i=None):
        # Draw the 3 current blocks spaced evenly under the grid
        spacing = 20
        preview_cell_size = 32
        total_width = 0
        block_rects = []

        # Calculate total width needed for all blocks and their spacing
        for block, _ in self.current_blocks:
            w = len(block[0]) * preview_cell_size
            block_rects.append(w)
            total_width += w
        total_width += spacing * (len(self.current_blocks) - 1)
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = self.grid_topleft[1] + self.grid_size * self.cell_size + 40
        x = start_x
        self.preview_block_rects = []

        for i, (block, colour) in enumerate(self.current_blocks):
            if self.placed_preview[i] or i == dragging_i:
                x += block_rects[i] + spacing
                continue
            minx = x
            miny = y
            maxx = x + len(block[0]) * preview_cell_size
            maxy = y + len(block) * preview_cell_size
            self.preview_block_rects.append(
                (i, pygame.Rect(minx, miny, maxx - minx, maxy - miny))
            )
            for r in range(len(block)):
                for c in range(len(block[0])):
                    if block[r][c]:
                        rect = pygame.Rect(
                            x + c * preview_cell_size,
                            y + r * preview_cell_size,
                            preview_cell_size,
                            preview_cell_size,
                        )
                        pygame.draw.rect(SCREEN, colour, rect)
                        pygame.draw.rect(SCREEN, (0, 0, 0), rect, width=2)
            x += block_rects[i] + spacing

    def draw_dragging_block(self, dragging_idx, pos):
        # Draws a block following the mouse.
        block, colour = self.current_blocks[dragging_idx]
        offsetx, offsety = pos
        # (Align to mouse: center block on cursor)
        block_w = len(block[0]) * self.cell_size
        block_h = len(block) * self.cell_size
        startx = offsetx - block_w // 2
        starty = offsety - block_h // 2
        for r in range(len(block)):
            for c in range(len(block[0])):
                if block[r][c]:
                    rect = pygame.Rect(
                        startx + c * self.cell_size,
                        starty + r * self.cell_size,
                        self.cell_size,
                        self.cell_size,
                    )
                    pygame.draw.rect(SCREEN, colour, rect)
                    pygame.draw.rect(SCREEN, (0, 0, 0), rect, width=2)

    def draw_grid_lines(self):
        for x in range(self.grid_size + 1):
            pygame.draw.line(
                SCREEN,
                self.grid_line_colour,
                (self.grid_topleft[0] + x * self.cell_size, self.grid_topleft[1]),
                (
                    self.grid_topleft[0] + x * self.cell_size,
                    self.grid_topleft[1] + self.grid_size * self.cell_size,
                ),
                2,
            )
        for y in range(self.grid_size + 1):
            pygame.draw.line(
                SCREEN,
                self.grid_line_colour,
                (self.grid_topleft[0], self.grid_topleft[1] + y * self.cell_size),
                (
                    self.grid_topleft[0] + self.grid_size * self.cell_size,
                    self.grid_topleft[1] + y * self.cell_size,
                ),
                2,
            )

    def draw_blocks(self):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                colour = self.grid[r][c]
                rect = pygame.Rect(
                    self.grid_topleft[0] + c * self.cell_size + 2,
                    self.grid_topleft[1] + r * self.cell_size + 2,
                    self.cell_size - 2,
                    self.cell_size - 2,
                )
                pygame.draw.rect(SCREEN, colour, rect)

    def draw_board(self, dragging_i, drag_pos):
        self.draw_score()
        self.draw_grid_lines()
        self.draw_blocks()
        self.draw_current_blocks(dragging_i=dragging_i)
        if dragging_i is not None:
            self.draw_dragging_block(dragging_i, drag_pos)

    def get_preview_blocks(self):
        return [
            (random.choice(self.block_shapes), random.choice(self.block_colours))
            for _ in range(3)
        ]

    def get_preview_special_blocks(self):
        all_blocks = self.block_shapes + self.special_block_shapes
        return [
            (random.choice(all_blocks), random.choice(all_blocks)) for _ in range(3)
        ]

    def can_place_block(self, block, top, left):
        """Check if block placement is valid"""
        for r in range(len(block)):
            for c in range(len(block[0])):
                if not block[r][c]:
                    continue
                row, col = top + r, left + c
                if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
                    return False
                if self.grid[row][col] != self.grid_bg_colour:
                    return False
        return True

    def place_block(self, block, top, left, colour):
        for r in range(len(block)):
            for c in range(len(block[0])):
                if not block[r][c]:
                    continue
                row, col = top + r, left + c
                self.grid[row][col] = colour
                self.score += 1

    def block_preview_at_pos(self, pos: Tuple[int, int]) -> int:
        """Returns (block_idx, block_rect) if pos is inside a block preview"""
        x, y = pos
        for i, rect in self.preview_block_rects:
            if rect.collidepoint(x, y):
                return i
        return -1

    def mouse_to_grid(
        self, mouse_pos: Tuple[int, int], dragging_i: int
    ) -> Tuple[int, int]:
        block, _ = self.current_blocks[dragging_i]

        # which cell is topleft of block in
        mouse_x, mouse_y = mouse_pos
        block_w = len(block[0]) * (self.cell_size - 10)
        block_h = len(block) * (self.cell_size - 10)
        block_x = mouse_x - block_w // 2
        block_y = mouse_y - block_h // 2
        grid_x, grid_y = self.grid_topleft
        rel_x = block_x - grid_x
        rel_y = block_y - grid_y
        col = rel_x // self.cell_size
        row = rel_y // self.cell_size
        return (int(row), int(col))

    def clear(self) -> int:
        # rows
        clear_row_i = []
        for i in range(self.grid_size):
            clear = True
            for cell in self.grid[i]:
                if cell == self.grid_bg_colour:
                    clear = False
                    break
            if clear:
                clear_row_i.append(i)

        # cols
        clear_col_i = []
        for j in range(self.grid_size):
            clear = True
            for i in range(self.grid_size):
                cell = self.grid[i][j]
                if cell == self.grid_bg_colour:
                    clear = False
                    break
            if clear:
                clear_col_i.append(j)

        for i in clear_row_i:
            for j in range(self.grid_size):
                self.grid[i][j] = self.grid_bg_colour

        for j in clear_col_i:
            for i in range(self.grid_size):
                self.grid[i][j] = self.grid_bg_colour

        return len(clear_row_i) + +len(clear_col_i)

    def all_clear(self) -> bool:
        for r in self.grid:
            for cell in r:
                if cell != self.grid_bg_colour:
                    return False
        return True

    def is_game_over(self) -> bool:
        def is_block_placable(block):
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if self.can_place_block(block, r, c):
                        return True
            return False

        for i in range(3):
            if not self.placed_preview[i]:
                if is_block_placable(self.current_blocks[i][0]):
                    return False
        return True


# Main loop with drag-n-drop
def main():
    run = True
    clock = pygame.time.Clock()
    block_blast = BlockBlast()

    # Preview block drag
    dragging = False
    dragging_i = None
    drag_pos = (0, 0)
    while run:
        # Draw
        SCREEN.fill(BG_COLOR)
        block_blast.draw_board(dragging_i=dragging_i, drag_pos=drag_pos)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and not dragging
            ):
                # Check if clicking on one of the previewed blocks to drag
                mouse_pos = pygame.mouse.get_pos()
                i = block_blast.block_preview_at_pos(mouse_pos)
                if i >= 0:
                    dragging = True
                    dragging_i = i
                    drag_pos = mouse_pos

            elif (
                event.type == pygame.MOUSEMOTION and dragging_i is not None and dragging
            ):
                drag_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
                # Attempt to place block on main grid if released
                grid_row, grid_col = block_blast.mouse_to_grid(drag_pos, dragging_i)
                block, colour = block_blast.current_blocks[dragging_i]
                if block_blast.can_place_block(block, grid_row, grid_col):
                    block_blast.place_block(block, grid_row, grid_col, colour)
                    clear_num = block_blast.clear()
                    block_blast.since_clear += 1
                    if clear_num > 0:
                        print(clear_num)
                        block_blast.score += (
                            (block_blast.combo + 1)
                            * 10
                            * block_blast.clear_multipler[clear_num - 1]
                        )
                        block_blast.combo += 1
                        block_blast.since_clear = 0
                        if block_blast.all_clear():
                            block_blast.score += 300
                    if block_blast.since_clear >= 3:
                        block_blast.combo = 0

                    if block_blast.is_game_over():
                        print("GAME OVER")

                    # Mark block as placed
                    block_blast.placed_preview[dragging_i] = True

                    # Refill blocks when all placed
                    if all(block_blast.placed_preview):
                        block_blast.current_blocks = block_blast.get_preview_blocks()
                        block_blast.placed_preview = [False, False, False]

                        while block_blast.is_game_over():
                            block_blast.current_blocks = (
                                block_blast.get_preview_special_blocks()
                            )

                # Stop dragging
                dragging = False
                dragging_i = None

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
