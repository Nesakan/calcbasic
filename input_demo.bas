PRINT "=== CalcBASIC Interactive Input Demo ==="
INPUT "Enter your name: "; USER_NAME$
PRINT "Hello, " + USER_NAME$ + "!"

INPUT "Enter two numbers (separated by comma): ", A, B
PRINT "Sum:"
PRINT A + B
PRINT "Product:"
PRINT A * B
PRINT "Hypotenuse (sqrt(A^2 + B^2)):"
PRINT SQRT(A ^ 2 + B ^ 2)
