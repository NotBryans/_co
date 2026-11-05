(RESTART)
@SCREEN
D=A
@addr
M=D

@KBD
D=M
@BLACK
D;JNE

@color
M=0
@DRAW
0;JMP

(BLACK)
@color
M=-1

(DRAW)
@addr
D=M
@KBD
D=D-A
@RESTART
D;JEQ

@color
D=M
@addr
A=M
M=D

@addr
M=M+1
@DRAW
0;JMP