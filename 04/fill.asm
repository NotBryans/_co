// fill.asm: Runs an infinite loop that listens to the keyboard input.
// When a key is pressed, the screen turns black; otherwise, it turns white.

(LOOP)
    // Read current keyboard state
    @KBD
    D=M

    // If a key is pressed (D != 0), jump to BLACK
    @BLACK
    D;JNE

    // No key pressed: set color to white (0)
    @color
    M=0
    @DRAW
    0;JMP

(BLACK)
    // Key pressed: set color to black (-1 / 0xFFFF)
    @color
    M=-1

(DRAW)
    // Initialize pointer to the start of screen memory (SCREEN = 16384)
    @SCREEN
    D=A
    @ptr
    M=D

(DRAW_LOOP)
    // Check if pointer has reached the end of screen memory (SCREEN + 8192 = 24576)
    @ptr
    D=M
    @KBD
    D=D-A
    @LOOP
    D;JGE    // If ptr >= 24576, full screen is drawn, return to main loop

    // Write color to the current screen memory word
    @color
    D=M
    @ptr
    A=M
    M=D

    // Advance pointer to the next word
    @ptr
    M=M+1

    // Continue drawing loop
    @DRAW_LOOP
    0;JMP