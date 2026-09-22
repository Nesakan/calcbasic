NAME = "Alice"
GREETING = "Hello, " + NAME + "!"
PRINT GREETING
A = 5
B = 3
PRINT A + B
PRINT (A + B) * 2
PRINT A > B
PRINT A = B
PRINT A <> B
PRINT A > B AND NAME = "Alice"
PRINT A < B OR B = 3
PRINT NOT A = B

IF A > B THEN
    PRINT "Block IF: A is greater than B"
ELSE
    PRINT "Block IF: B is greater than or equal to A"
END IF

IF NAME = "Alice" THEN PRINT "Single-line IF: Hello Alice!" ELSE PRINT "Single-line IF: Unknown user"

TOTAL = 0
FOR I = 1 TO 5
    TOTAL = TOTAL + I
NEXT I
PRINT "Loop completed. Total sum:"
PRINT TOTAL

PRINT "--- Math Functions Demo ---"
RADIUS = 5
AREA = PI * RADIUS ^ 2
PRINT "Circle area with radius 5:"
PRINT ROUND(AREA, 2)

HYPOTENUSE = SQRT(3 ^ 2 + 4 ^ 2)
PRINT "Hypotenuse of 3 and 4:"
PRINT HYPOTENUSE

PRINT "Trigonometry identity: sin^2(x) + cos^2(x):"
ANGLE = PI / 4
PRINT ROUND(SIN(ANGLE) ^ 2 + COS(ANGLE) ^ 2, 4)

PRINT "Absolute value of -42:"
PRINT ABS(-42)

PRINT "Floor / INT of 3.7 and -3.7:"
PRINT INT(3.7)
PRINT INT(-3.7)

PRINT "Max of 12, 45, 7, 89, 23:"
PRINT MAX(12, 45, 7, 89, 23)

