"""Small symbolic Baba planner used by the instructor reference agent."""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass

from workshop.types import Observation


DIRECTIONS = (
    ("up", -1, 0),
    ("right", 0, 1),
    ("down", 1, 0),
    ("left", 0, -1),
)
PROPERTIES = {"you", "win", "stop", "push"}
TOKEN_RE = re.compile(r"(Obj|Rule)\[([A-Za-z_]+)(?:,[^\]]*)?\]")


@dataclass(frozen=True)
class Piece:
    kind: str
    name: str


@dataclass(frozen=True)
class World:
    height: int
    width: int
    pieces: tuple[Piece, ...]
    positions: tuple[tuple[int, int], ...]

    @classmethod
    def from_observation(cls, observation: Observation) -> "World":
        pieces = []
        positions = []
        width = 0
        height = 0
        for raw_row in observation.grid.splitlines()[1:]:
            match = re.match(r"(\d+) \| (.*)", raw_row)
            if not match:
                continue
            row = int(match.group(1))
            cells = match.group(2).split(" | ")
            height = max(height, row + 1)
            width = max(width, len(cells))
            for column, cell in enumerate(cells):
                for token in TOKEN_RE.finditer(cell):
                    pieces.append(Piece("object" if token.group(1) == "Obj" else "text", token.group(2)))
                    positions.append((row, column))
        return cls(height, width, tuple(pieces), tuple(positions))

    def at(self, positions, row, column):
        return [index for index, position in enumerate(positions) if position == (row, column)]

    def rules(self, positions):
        words: dict[tuple[int, int], set[str]] = {}
        for piece, position in zip(self.pieces, positions):
            if piece.kind == "text":
                words.setdefault(position, set()).add(piece.name)
        rules = set()
        for (row, column), names in words.items():
            for subject in names - PROPERTIES - {"is"}:
                for dr, dc in ((0, 1), (1, 0)):
                    middle = words.get((row + dr, column + dc), set())
                    target = words.get((row + 2 * dr, column + 2 * dc), set())
                    if "is" not in middle:
                        continue
                    for prop in target & PROPERTIES:
                        rules.add((subject, prop))
        return rules

    def properties(self, positions):
        properties: dict[str, set[str]] = {}
        for subject, prop in self.rules(positions):
            properties.setdefault(subject, set()).add(prop)
        return properties

    def is_win(self, positions) -> bool:
        properties = self.properties(positions)
        you_cells = {
            position
            for piece, position in zip(self.pieces, positions)
            if piece.kind == "object" and "you" in properties.get(piece.name, set())
        }
        win_cells = {
            position
            for piece, position in zip(self.pieces, positions)
            if piece.kind == "object" and "win" in properties.get(piece.name, set())
        }
        return bool(you_cells & win_cells)

    def step(self, positions, dr: int, dc: int):
        properties = self.properties(positions)
        you = [
            index
            for index, piece in enumerate(self.pieces)
            if piece.kind == "object" and "you" in properties.get(piece.name, set())
        ]
        if not you:
            return positions

        updated = list(positions)

        def move(index: int, moving: set[int]) -> bool:
            if index in moving:
                return False
            row, column = updated[index]
            destination = (row + dr, column + dc)
            if not (0 <= destination[0] < self.height and 0 <= destination[1] < self.width):
                return False

            occupants = self.at(updated, *destination)
            pushable = []
            for occupant in occupants:
                piece = self.pieces[occupant]
                props = properties.get(piece.name, set())
                if piece.kind == "text" or "push" in props:
                    pushable.append(occupant)
                elif "stop" in props:
                    return False

            snapshot = list(updated)
            next_moving = moving | {index}
            for occupant in pushable:
                if not move(occupant, next_moving):
                    updated[:] = snapshot
                    return False
            updated[index] = destination
            return True

        for index in you:
            move(index, set())
        return tuple(updated)


def find_plan(observation: Observation, max_depth: int | None = None) -> list[str] | None:
    world = World.from_observation(observation)
    start = world.positions
    if world.is_win(start):
        return []
    depth_limit = max_depth or observation.steps_remaining
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        positions, path = queue.popleft()
        if len(path) >= depth_limit:
            continue
        for action, dr, dc in DIRECTIONS:
            next_positions = world.step(positions, dr, dc)
            if next_positions == positions or next_positions in seen:
                continue
            next_path = path + [action]
            if world.is_win(next_positions):
                return next_path
            seen.add(next_positions)
            queue.append((next_positions, next_path))
    return None
