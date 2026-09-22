PRINT "========================================"
PRINT "       WELCOME TO CALCBASIC 1.0         "
PRINT "  A BASIC Interpreter Built From Scratch "
PRINT "========================================"
PRINT ""

INPUT "What is your name? "; DAD_NAME$
PRINT "Hello, " + DAD_NAME$ + "! Welcome to my custom programming language."
PRINT ""

PRINT "--- Part 1: Interactive Math Calculations ---"
INPUT "Enter the radius of a circle: ", RADIUS
AREA = PI * RADIUS ^ 2
CIRCUMFERENCE = 2 * PI * RADIUS
PRINT "Circle Area (pi * r^2):"
PRINT ROUND(AREA, 2)
PRINT "Circumference (2 * pi * r):"
PRINT ROUND(CIRCUMFERENCE, 2)
PRINT ""

PRINT "--- Part 2: Number Guessing Game ---"
PRINT "I am thinking of a secret number between 1 and 20..."
SECRET = RND(20)
WON = 0

FOR ATTEMPTS = 1 TO 5
    IF WON = 0 THEN
        PRINT "Attempt:"
        PRINT ATTEMPTS
        INPUT "Enter your guess: ", GUESS
        IF GUESS = SECRET THEN
            PRINT "CONGRATULATIONS! You guessed the secret number!"
            WON = 1
        ELSE
            IF GUESS < SECRET THEN
                PRINT "Too low! Try higher."
            ELSE
                PRINT "Too high! Try lower."
            END IF
        END IF
    END IF
NEXT ATTEMPTS

IF WON = 0 THEN
    PRINT "Good try! The secret number was:"
    PRINT SECRET
END IF

PRINT ""
PRINT "Thank you for testing my project, " + DAD_NAME$ + "!"
