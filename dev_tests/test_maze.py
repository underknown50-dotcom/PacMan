"""Exercise the real assigned wheel and the game's read-only maze adapter."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import random
from types import MappingProxyType
import unittest

from mazegenerator import MazeGenerator

from pacman.ghost_ai import (
    calculate_ghost_target, choose_step, nearest_reachable,
)
from pacman.maze_adapter import (
    Cell, Direction, Maze, MazeError, _build_graph, _freeze_walls,
    _largest_component,
)


class MazeIntegrationTests(unittest.TestCase):
    """Verify real dependency integration, safe placement and walls."""

    def assert_topology(self, maze: Maze) -> None:
        """Check borders, masks, reciprocal passages and connectivity."""
        self.assertEqual(len(maze.walls), maze.height)
        self.assertTrue(all(len(row) == maze.width for row in maze.walls))
        self.assertEqual(set(maze.distances(maze.spawn)), maze.reachable)
        self.assertEqual(set(maze.adjacency), maze.reachable)
        directions = (
            (Direction.UP, 1, 4), (Direction.RIGHT, 2, 8),
            (Direction.DOWN, 4, 1), (Direction.LEFT, 8, 2),
        )
        for y, row in enumerate(maze.walls):
            for x, mask in enumerate(row):
                self.assertIs(type(mask), int)
                self.assertTrue(0 <= mask <= 15)
                cell = (x, y)
                if mask == 15:
                    self.assertNotIn(cell, maze.reachable)
                for direction, bit, opposite in directions:
                    dx, dy = direction.delta
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < maze.width and 0 <= ny < maze.height):
                        self.assertTrue(mask & bit)
                        self.assertIsNone(maze.step(cell, direction))
                    else:
                        self.assertEqual(
                            bool(mask & bit),
                            bool(maze.walls[ny][nx] & opposite),
                        )
                        expected = (
                            (nx, ny)
                            if cell in maze.reachable and not mask & bit
                            else None
                        )
                        self.assertEqual(maze.step(cell, direction), expected)
                        if expected is not None:
                            self.assertIn(cell, maze.neighbors(expected))
        positions = (
            {maze.spawn} | set(maze.ghost_spawns) | set(maze.power_cells)
        )
        self.assertEqual(len(maze.ghost_spawns), 4)
        self.assertEqual(len(maze.power_cells), 4)
        self.assertEqual(len(positions), 9)
        self.assertLessEqual(positions, maze.reachable)

    def test_real_wheel_public_api_and_exact_wall_copy(self) -> None:
        """Use size and perfect=False, preserving the assigned wall masks."""
        generator = MazeGenerator(size=(20, 17), perfect=False, seed=42)
        original = tuple(tuple(row) for row in generator.maze)
        maze = Maze.generate(20, 17, 42)
        self.assertEqual(maze.walls, original)
        self.assertEqual(tuple(tuple(r) for r in generator.maze), original)
        self.assertEqual(generator.maze_entry, (0, 0))
        self.assertEqual(generator.maze_exit, (19, 16))
        self.assertTrue(generator.shortest_path)
        self.assert_topology(maze)

    def test_every_supported_side_and_rectangular_dimensions(self) -> None:
        """Exercise odd/even sizes throughout the complete configured range."""
        dimensions = [(side, side) for side in range(15, 36)]
        dimensions.extend([(15, 35), (35, 15), (20, 25), (26, 19)])
        for width, height in dimensions:
            with self.subTest(width=width, height=height):
                self.assert_topology(Maze.generate(width, height, 42))

    def test_fixed_seeds_are_repeatable_across_varied_levels(self) -> None:
        """A positive seed repeats the maze, placement and adjacency graph."""
        for seed in (1, 42, 9817):
            for width, height in ((15, 15), (20, 20), (35, 25)):
                with self.subTest(seed=seed, size=(width, height)):
                    first = Maze.generate(width, height, seed)
                    second = Maze.generate(width, height, seed)
                    self.assertEqual(first, second)
                    self.assert_topology(first)

    def test_random_seed_generates_fresh_mazes(self) -> None:
        """Zero uses the wheel's randomness rather than a repeatable seed."""
        mazes = [Maze.generate(20, 20, 0).walls for _ in range(3)]
        self.assertGreater(len(set(mazes)), 1)

    def test_blocked_even_center_uses_nearest_geometric_position(self) -> None:
        """The protected 42 never becomes Pac-Man's initial position."""
        maze = Maze.generate(20, 20, 42)
        self.assertEqual(maze.walls[10][10], 15)
        self.assertNotEqual(maze.spawn, (10, 10))
        nearest = min(
            (2 * x - 19) ** 2 + (2 * y - 19) ** 2
            for x, y in maze.reachable
        )
        x, y = maze.spawn
        self.assertEqual((2 * x - 19) ** 2 + (2 * y - 19) ** 2, nearest)

    def test_open_center_is_preferred(self) -> None:
        """The central tile is selected directly whenever it is playable."""
        maze = Maze.generate(21, 21, 42)
        self.assertIn((10, 10), maze.reachable)
        self.assertEqual(maze.spawn, (10, 10))

    def test_corners_have_separate_reachable_entities_and_power_pellets(
        self,
    ) -> None:
        """All four regions receive their own ghost and adjacent power tile."""
        maze = Maze.generate(20, 20, 42)
        corners = ((0, 0), (19, 0), (19, 19), (0, 19))
        self.assertEqual(maze.ghost_spawns, corners)
        for corner in corners:
            distance = min(
                (x - corner[0]) ** 2 + (y - corner[1]) ** 2
                for x, y in maze.power_cells
            )
            self.assertEqual(distance, 1)
        self.assert_topology(maze)

    def test_adapter_outputs_are_immutable(self) -> None:
        """Neither the graph nor the maze's frozen fields can be changed."""
        maze = Maze.generate(15, 15, 42)
        self.assertIsInstance(maze.adjacency, MappingProxyType)
        self.assertIsInstance(maze.walls, tuple)
        self.assertTrue(all(isinstance(row, tuple) for row in maze.walls))
        with self.assertRaises(FrozenInstanceError):
            setattr(maze, "spawn", (0, 0))

    def test_braided_gameplay_has_loops(self) -> None:
        """The original wheel's non-perfect mode provides looped corridors."""
        for seed in (2, 42, 999):
            maze = Maze.generate(20, 20, seed)
            passages = sum(len(n) for n in maze.adjacency.values()) // 2
            self.assertGreater(passages, len(maze.reachable) - 1)

    def test_invalid_dimensions_and_seed_fail_clearly(self) -> None:
        """Reject unsafe dimensions before calling into the dependency."""
        for dimensions in ((14, 20), (20, 36), (0, 0), (True, 20)):
            with self.subTest(dimensions=dimensions):
                with self.assertRaises(MazeError):
                    Maze.generate(*dimensions, 42)
        for seed in (-1, True):
            with self.subTest(seed=seed):
                with self.assertRaises(MazeError):
                    Maze.generate(20, 20, seed)

    def test_outside_cells_and_isolated_cells_cannot_move(self) -> None:
        """All public traversal helpers safely reject non-playable cells."""
        maze = Maze.generate(20, 20, 42)
        for cell in ((-1, 0), (20, 20), (10, 10)):
            self.assertEqual(maze.neighbors(cell), ())
            self.assertEqual(maze.distances(cell), {})
            for direction in Direction:
                self.assertIsNone(maze.step(cell, direction))


class MazeValidationTests(unittest.TestCase):
    """Check malformed application inputs without patching the dependency."""

    def test_shape_and_mask_validation(self) -> None:
        """Reject missing rows, malformed row widths and invalid mask types."""
        invalid_grids: tuple[object, ...] = (
            None, [], [[15]], [[15, 15]], [[15], [15]],
            [[True, 15], [15, 15]], [[16, 15], [15, 15]],
            [[-1, 15], [15, 15]], [["15", 15], [15, 15]],
        )
        for raw in invalid_grids:
            with self.subTest(raw=raw):
                with self.assertRaises(MazeError):
                    _freeze_walls(raw, 2, 2)

    def test_border_and_reciprocal_validation(self) -> None:
        """Refuse topology with open boundaries or one-way passages."""
        with self.assertRaisesRegex(MazeError, "open edge"):
            _build_graph(((14, 15), (15, 15)), 2, 2)
        with self.assertRaisesRegex(MazeError, "inconsistent"):
            _build_graph(((13, 15), (15, 15)), 2, 2)

    def test_grid_copy_preserves_input_and_detaches_rows(self) -> None:
        """Adapter validation copies masks without writing to its input."""
        source = [[15, 15], [15, 15]]
        frozen = _freeze_walls(source, 2, 2)
        self.assertEqual(source, [[15, 15], [15, 15]])
        source[0][0] = 0
        self.assertEqual(frozen, ((15, 15), (15, 15)))

    def test_largest_connected_component_selection(self) -> None:
        """Ignore disconnected minor regions when choosing playable cells."""
        graph = {
            (0, 0): ((1, 0),), (1, 0): ((0, 0),),
            (5, 5): ((6, 5),),
            (6, 5): ((5, 5), (7, 5)), (7, 5): ((6, 5),),
        }
        self.assertEqual(
            _largest_component(graph), frozenset({(5, 5), (6, 5), (7, 5)}),
        )
        self.assertEqual(_largest_component({}), frozenset())


class GhostAITests(unittest.TestCase):
    """Verify pathfinding, frightened flight and isolated randomness."""

    def setUp(self) -> None:
        """Use the assigned generator for every AI traversal test."""
        self.maze = Maze.generate(20, 20, 42)

    def test_chase_chooses_a_shortest_path_neighbor(self) -> None:
        """Dangerous ghosts always reduce player distance when possible."""
        distances = self.maze.distances(self.maze.spawn)
        rng = random.Random(3)
        for cell in self.maze.reachable:
            destination = choose_step(
                self.maze, cell, self.maze.spawn, None, False, rng,
            )
            self.assertIn(destination, self.maze.neighbors(cell))
            self.assertEqual(
                distances[destination],
                min(distances[n] for n in self.maze.neighbors(cell)),
            )

    def test_frightened_ghosts_choose_the_farthest_neighbor(self) -> None:
        """Edible ghosts maximize their graph distance from the player."""
        distances = self.maze.distances(self.maze.spawn)
        rng = random.Random(9)
        for cell in self.maze.reachable:
            destination = choose_step(
                self.maze, cell, self.maze.spawn, None, True, rng,
            )
            self.assertIn(destination, self.maze.neighbors(cell))
            self.assertEqual(
                distances[destination],
                max(distances[n] for n in self.maze.neighbors(cell)),
            )

    def test_avoids_reversal_among_equally_good_routes(self) -> None:
        """Previous-cell memory affects ties without breaking pursuit."""
        cell = self.maze.spawn
        neighbors = self.maze.neighbors(cell)
        self.assertGreaterEqual(len(neighbors), 2)
        previous = neighbors[0]
        for frightened in (False, True):
            destination = choose_step(
                self.maze, cell, cell, previous,
                frightened, random.Random(42),
            )
            self.assertNotEqual(destination, previous)

    def test_ties_vary_reproducibly(self) -> None:
        """An independent random instance provides controlled tie variation."""
        cell = self.maze.spawn

        def sequence(seed: int) -> list[Cell]:
            """Capture equivalent decisions made with the same local seed."""
            rng = random.Random(seed)
            return [
                choose_step(self.maze, cell, cell, None, False, rng)
                for _ in range(30)
            ]

        first = sequence(71)
        Maze.generate(15, 15, 999)
        self.assertEqual(first, sequence(71))
        self.assertGreater(len(set(first)), 1)

    def test_no_standing_still_except_without_a_legal_passage(self) -> None:
        """An invalid or protected isolated tile produces no illegal jump."""
        cell = (10, 10)
        self.assertEqual(
            choose_step(
                self.maze, cell, self.maze.spawn, None,
                False, random.Random(1),
            ),
            cell,
        )

    def test_nearest_reachable_clamps_and_finds_in_bounds(self) -> None:
        """Targeting coordinates outside the grid resolve to playable cells."""
        near = nearest_reachable(self.maze, (-10, -10))
        self.assertIn(near, self.maze.reachable)
        far = nearest_reachable(self.maze, (100, 100))
        self.assertIn(far, self.maze.reachable)

    def test_ghost_personalities_distinct_targeting(self) -> None:
        """Verify each ghost personality computes distinct, valid targets."""
        player = (10, 12)
        blinky = (10, 15)
        home = (0, 0)
        t0 = calculate_ghost_target(
            0, (5, 5), home, player, Direction.UP, blinky, self.maze,
        )
        self.assertEqual(t0, player)

        t1 = calculate_ghost_target(
            1, (5, 5), home, player, Direction.UP, blinky, self.maze,
        )
        self.assertIn(t1, self.maze.reachable)

        t2 = calculate_ghost_target(
            2, (5, 5), home, player, Direction.UP, blinky, self.maze,
        )
        self.assertIn(t2, self.maze.reachable)

        close_cell = (10, 13)
        t3_close = calculate_ghost_target(
            3, close_cell, home, player, Direction.UP, blinky, self.maze,
        )
        self.assertEqual(t3_close, home)

        far_cell = (0, 0)
        t3_far = calculate_ghost_target(
            3, far_cell, home, player, Direction.UP, blinky, self.maze,
        )
        self.assertEqual(t3_far, player)


if __name__ == "__main__":
    unittest.main()
