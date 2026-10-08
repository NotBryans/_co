// mult.asm: Computes R0 * R1 and stores the result in R2.
// Assumes R0 >= 0, R1 >= 0, and R0*R1 < 32768.

    // Initialize R2 = 0
    @R2
    M=0

    // Load R1 into counter variable 'i'
    @R1
    D=M
    @i
    M=D

(LOOP)
    // Check if counter i <= 0. If so, exit loop.
    @i
    D=M
    @END
    D;JLE

    // R2 = R2 + R0
    @R0
    D=M
    @R2
    M=M+D

    // Decrement counter i
    @i
    M=M-1

    // Jump back to start of loop
    @LOOP
    0;JMP

(END)
    // Infinite loop to terminate execution
    @END
    0;JMP