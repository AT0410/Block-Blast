import pygame
from blockblast import BlockBlast, SCREEN, BG_COLOR, FPS

# Main loop with drag-n-drop
def main_player():
    run = True
    clock = pygame.time.Clock()
    block_blast = BlockBlast()
    grid = block_blast.grid

    # Preview block drag
    dragging = False
    dragging_i = None
    drag_pos = (0, 0)
    gameover = False
    while run:
        # Draw
        SCREEN.fill(BG_COLOR)
        block_blast.draw_board(dragging_i=dragging_i, drag_pos=drag_pos)
        if gameover:
            block_blast.draw_gameover()

        
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
                if block_blast.can_place_block(grid, block, grid_row, grid_col):
                    block_blast.place_block(grid, block, grid_row, grid_col, colour)
                    clear_num = block_blast.clear(grid)
                    block_blast.score += block_blast.get_score_increment(grid, block, clear_num)
                    if block_blast.is_game_over(grid):
                        gameover = True

                    # Mark block as placed
                    block_blast.placed_preview[dragging_i] = True

                    # Refill blocks when all placed
                    if all(block_blast.placed_preview):
                        block_blast.current_blocks = block_blast.get_preview_blocks()
                        block_blast.placed_preview = [False, False, False]

                        while block_blast.is_game_over(grid):
                            block_blast.current_blocks = (
                                block_blast.get_preview_special_blocks()
                            )

                # Stop dragging
                dragging = False
                dragging_i = None

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main_player()