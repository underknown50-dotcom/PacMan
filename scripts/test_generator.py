"""Scratch script to inspect the external mazegenerator package.

Prints dimensions, raw bitmask cell values, and ASCII maze corridors
to stdout to verify non-perfect looping maze generation.
"""

from mazegenerator import MazeGenerator


def main() -> None:
    """Generate and display an ASCII representation of the maze."""
    generator = MazeGenerator(size=(15, 15), perfect=False, seed=42)

    grid = generator.maze

    print("Number of rows:", len(grid))
    print("Number of columns:", len(grid[0]))
    print("First row:", grid[0])

    for y in range(len(grid)):
        top_line = ""
        mid_line = ""
        for x in range(len(grid[0])):
            cell = grid[y][x]

            if cell & 1:
                top_line += "+---"
            else:
                top_line += "+   "

            if cell & 8:
                mid_line += "|   "
            else:
                mid_line += "    "

        print(top_line + "+")
        print(mid_line + "|")

    print("+---" * len(grid[0]) + "+")


if __name__ == "__main__":
    main()
