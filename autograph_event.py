import json
import math
import random
from pathlib import Path

import pygame


AUTOGRAPH_CANVAS_RECT = pygame.Rect(333, 185, 700, 370)
AUTOGRAPH_CLEAR_RECT = pygame.Rect(390, 590, 210, 46)
AUTOGRAPH_SUBMIT_RECT = pygame.Rect(766, 590, 210, 46)


# Normalized continuous doodles. These are deliberately simple enough to trace
# with a mouse, but visually different enough that the event does not feel like
# the same autograph every time the event appears.
AUTOGRAPH_SHAPES_PATH = Path(__file__).parent / "data" / "autograph_shapes.json"


def _load_autograph_templates():
    try:
        with AUTOGRAPH_SHAPES_PATH.open("r", encoding="utf-8") as file:
            raw = json.load(file)
    except (OSError, json.JSONDecodeError):
        raw = []

    templates = []
    for entry in raw if isinstance(raw, list) else []:
        if not isinstance(entry, dict):
            continue
        points = entry.get("points")
        if not isinstance(points, list) or len(points) < 2:
            continue

        cleaned_points = []
        valid = True
        for point in points:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                valid = False
                break
            try:
                x = max(0.0, min(1.0, float(point[0])))
                y = max(0.0, min(1.0, float(point[1])))
            except (TypeError, ValueError):
                valid = False
                break
            cleaned_points.append((x, y))

        if not valid:
            continue

        templates.append({
            "id": str(entry.get("id") or f"shape_{len(templates) + 1}"),
            "name": str(entry.get("name") or "Autograph"),
            "points": tuple(cleaned_points),
        })

    if not templates:
        templates = [{
            "id": "star",
            "name": "Star",
            "points": (
                (0.50, 0.08), (0.61, 0.39), (0.94, 0.39),
                (0.67, 0.58), (0.77, 0.90), (0.50, 0.70),
                (0.23, 0.90), (0.33, 0.58), (0.06, 0.39),
                (0.39, 0.39), (0.50, 0.08),
            ),
        }]

    return tuple(templates)


AUTOGRAPH_TEMPLATES = _load_autograph_templates()


def _point_segment_distance(point, start, end):
    px, py = point
    ax, ay = start
    bx, by = end
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    nearest_x = ax + t * dx
    nearest_y = ay + t * dy
    return math.hypot(px - nearest_x, py - nearest_y)


def _distance_to_polyline(point, polyline):
    if not polyline:
        return float("inf")
    if len(polyline) == 1:
        return math.hypot(point[0] - polyline[0][0], point[1] - polyline[0][1])
    return min(
        _point_segment_distance(point, polyline[index], polyline[index + 1])
        for index in range(len(polyline) - 1)
    )


def _sample_polyline(polyline, samples_per_segment=10):
    if len(polyline) < 2:
        return list(polyline)
    points = []
    for index in range(len(polyline) - 1):
        ax, ay = polyline[index]
        bx, by = polyline[index + 1]
        for step in range(samples_per_segment):
            t = step / float(samples_per_segment)
            points.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    points.append(polyline[-1])
    return points


class AutographEvent:
    def __init__(self):
        self.templates = []
        self.index = 0
        self.trace_points = []
        self.drawing = False
        self.scores = []
        self.feedback = "Hold the mouse button and trace the pale line."
        self.complete = False

    def start(self):
        self.templates = random.sample(
            list(AUTOGRAPH_TEMPLATES),
            1,
        )
        self.index = 0
        self.trace_points = []
        self.drawing = False
        self.scores = []
        self.feedback = "Hold the mouse button and trace the pale line."
        self.complete = False

    @property
    def current_template(self):
        if 0 <= self.index < len(self.templates):
            return self.templates[self.index]
        return None

    def get_target_points(self):
        template = self.current_template
        if template is None:
            return []
        inset = AUTOGRAPH_CANVAS_RECT.inflate(-90, -70)
        return [
            (
                inset.x + int(x * inset.width),
                inset.y + int(y * inset.height),
            )
            for x, y in template["points"]
        ]

    def begin_trace(self, position):
        if self.complete or position is None:
            return False
        if not AUTOGRAPH_CANVAS_RECT.collidepoint(position):
            return False
        self.trace_points = [position]
        self.drawing = True
        self.feedback = "Keep tracing..."
        return True

    def add_trace_point(self, position):
        if not self.drawing or self.complete or position is None:
            return False
        if not AUTOGRAPH_CANVAS_RECT.inflate(12, 12).collidepoint(position):
            return False
        if not self.trace_points:
            self.trace_points.append(position)
            return True
        last = self.trace_points[-1]
        if math.hypot(position[0] - last[0], position[1] - last[1]) >= 3.0:
            self.trace_points.append(position)
        return True

    def end_trace(self):
        was_drawing = self.drawing
        self.drawing = False
        return was_drawing

    def clear_trace(self):
        self.trace_points = []
        self.drawing = False
        self.feedback = "Cleared. Try the autograph again."

    def current_accuracy(self):
        target = self.get_target_points()
        trace = self.trace_points
        if len(target) < 2 or len(trace) < 2:
            return 0.0

        tolerance = 24.0
        target_samples = _sample_polyline(target, 12)
        trace_samples = trace[::max(1, len(trace) // 160)]

        coverage_hits = sum(
            1 for point in target_samples
            if _distance_to_polyline(point, trace) <= tolerance
        )
        coverage = coverage_hits / max(1, len(target_samples))

        precision_hits = sum(
            1 for point in trace_samples
            if _distance_to_polyline(point, target) <= tolerance
        )
        precision = precision_hits / max(1, len(trace_samples))

        # Coverage matters more than simply staying near one small part of the line.
        score = (coverage * 0.72 + precision * 0.28) * 100.0

        # Very short traces should not score highly even if they happen to sit on-line.
        if len(trace) < 15:
            score *= len(trace) / 15.0

        return max(0.0, min(100.0, score))

    def submit_current(self):
        if self.complete:
            return None

        score = self.current_accuracy()
        self.scores.append(score)

        if score >= 90:
            self.feedback = f"Excellent autograph: {score:.0f}% accuracy."
        elif score >= 75:
            self.feedback = f"Good autograph: {score:.0f}% accuracy."
        elif score >= 55:
            self.feedback = f"Recognizable autograph: {score:.0f}% accuracy."
        else:
            self.feedback = f"That one got away from you: {score:.0f}% accuracy."

        self.index += 1
        self.trace_points = []
        self.drawing = False

        if self.index >= len(self.templates):
            self.complete = True

        return score

    def average_accuracy(self):
        if not self.scores:
            return 0.0
        return sum(self.scores) / len(self.scores)
