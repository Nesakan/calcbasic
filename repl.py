#!/usr/bin/env python3
"""
CalcBASIC REPL (Read-Eval-Print Loop)
A simple interactive interpreter for CalcBASIC
"""

import sys
from calcbasic.interpreter import Interpreter

def main():
    interpreter = Interpreter()

    # If a file path is provided as an argument, run it
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            interpreter.interpret(source)
        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found.")
        except Exception as e:
            print(f"Error: {e}")
        return

    print("CalcBASIC REPL v0.2.0")
    print("Type 'exit' or 'quit' to leave")
    print("Enter CalcBASIC statements to evaluate them")
    print("-" * 40)

    while True:
        try:
            # Get input from user
            source = input("CalcBASIC> ").strip()

            # Check for exit commands
            if source.lower() in ('exit', 'quit'):
                print("Goodbye!")
                break

            # Skip empty lines
            if not source:
                continue

            # Interpret the input
            result = interpreter.interpret(source)
            if result is not None:
                print(result)

        except KeyboardInterrupt:
            print("\nUse 'exit' or 'quit' to leave")
            continue
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()