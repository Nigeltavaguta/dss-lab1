"""Problem model for the Exam Timetabling Engine (ETE).

An instance consists of exams, venues, lecturers and student groups
(cohorts, elective groups and carry-over students). The engine assigns each
exam a time slot. A slot is feasible for a set of exams when:

* no two exams in the slot share a student group (student conflict);
* no two exams in the slot share a lecturer (invigilation conflict);
* every exam's lecturer is available in that slot (unary constraint);
* the exams in the slot can be placed in distinct venues, each venue large
  enough for the exam it receives (venue capacity constraint).

The first two constraints are binary "not equal" constraints, so they are
stored as an undirected conflict graph ``adj``. Without venues and
availability restrictions the problem is exactly graph colouring.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Exam:
    id: int
    code: str
    size: int
    lecturer: int


@dataclass(frozen=True)
class Venue:
    id: int
    name: str
    capacity: int


@dataclass(frozen=True)
class Lecturer:
    id: int
    name: str
    unavailable: frozenset = frozenset()


@dataclass(frozen=True)
class StudentGroup:
    """A set of students who sit exactly the same exams.

    ``kind`` is ``"cohort"`` for a programme-year class, ``"elective"`` for
    the part of a cohort taking an optional course, or ``"carry-over"`` for
    students repeating a course from an earlier year.
    """

    id: int
    name: str
    size: int
    exams: tuple
    kind: str = "cohort"


class Instance:
    """A timetabling instance with a fixed slot horizon ``num_slots``.

    ``venues`` may be ``None``, meaning rooms are unlimited. This is the pure
    graph-colouring case used for random graphs and for the reductions.
    """

    def __init__(self, exams, num_slots, venues=None, lecturers=None,
                 groups=None, extra_edges=(), name="instance"):
        self.name = name
        self.exams = list(exams)
        self.n = len(self.exams)
        self.num_slots = num_slots
        self.venues = list(venues) if venues is not None else None
        self.lecturers = list(lecturers) if lecturers is not None else []
        self.groups = list(groups) if groups is not None else []

        adj = [set() for _ in range(self.n)]

        def link(a, b):
            if a != b:
                adj[a].add(b)
                adj[b].add(a)

        for g in self.groups:
            members = g.exams
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    link(members[i], members[j])
        by_lecturer = {}
        for e in self.exams:
            by_lecturer.setdefault(e.lecturer, []).append(e.id)
        for members in by_lecturer.values():
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    link(members[i], members[j])
        for a, b in extra_edges:
            link(a, b)
        self.adj = adj
        self.num_edges = sum(len(s) for s in adj) // 2

        unavailable = {lec.id: lec.unavailable for lec in self.lecturers}
        all_slots = frozenset(range(num_slots))
        self.allowed = [all_slots - unavailable.get(e.lecturer, frozenset())
                        for e in self.exams]
        self.sizes = [e.size for e in self.exams]
        # Slots are interchangeable (colour symmetry) only when no exam has
        # a restricted domain. Branch-and-bound uses this to break symmetry.
        self.symmetric = all(len(a) == num_slots for a in self.allowed)
        if self.venues is not None:
            self.caps_desc = sorted((v.capacity for v in self.venues), reverse=True)
            self.cap_values = sorted(set(self.caps_desc))
        else:
            self.caps_desc = None
            self.cap_values = None

    def degree(self, v):
        return len(self.adj[v])

    def max_degree(self):
        return max((len(s) for s in self.adj), default=0)

    def density(self):
        if self.n < 2:
            return 0.0
        return 2 * self.num_edges / (self.n * (self.n - 1))

    def summary(self):
        return {
            "name": self.name,
            "exams": self.n,
            "edges": self.num_edges,
            "density": round(self.density(), 4),
            "max_degree": self.max_degree(),
            "venues": len(self.venues) if self.venues is not None else "unlimited",
            "groups": len(self.groups),
            "slots": self.num_slots,
            "restricted_exams": sum(1 for a in self.allowed if len(a) < self.num_slots),
        }


# ---------------------------------------------------------------------------
# Venue capacity: a slot is feasible iff a matching exists from its exams to
# distinct venues with capacity >= exam size. Because "venue fits exam" is a
# threshold relation, the matching exists iff the i-th largest exam fits the
# i-th largest venue for every i (proved in the report, Section 4.4).
# ---------------------------------------------------------------------------

def sizes_fit(sizes_desc, caps_desc):
    if len(sizes_desc) > len(caps_desc):
        return False
    return all(s <= c for s, c in zip(sizes_desc, caps_desc))


class VenueState:
    """Per-slot exam sizes with an O(m) incremental feasibility check."""

    def __init__(self, inst, num_slots):
        self.inst = inst
        self.unlimited = inst.venues is None
        self.loads = [[] for _ in range(num_slots)]  # ascending sizes

    def can_add(self, slot, size):
        if self.unlimited:
            return True
        load = self.loads[slot]
        caps = self.inst.caps_desc
        m = len(load)
        if m + 1 > len(caps):
            return False
        # Walk the merged descending sequence without building it.
        i = m - 1          # index into load (ascending, so walk backwards)
        placed = False
        for pos in range(m + 1):
            if not placed and (i < 0 or size >= load[i]):
                value = size
                placed = True
            else:
                value = load[i]
                i -= 1
            if value > caps[pos]:
                return False
        return True

    def add(self, slot, size):
        if not self.unlimited:
            bisect.insort(self.loads[slot], size)

    def remove(self, slot, size):
        if not self.unlimited:
            load = self.loads[slot]
            del load[bisect.bisect_left(load, size)]

    def max_addable(self, slot):
        """Largest exam size that still fits in ``slot`` (0 if none)."""
        if self.unlimited:
            return float("inf")
        values = self.inst.cap_values
        lo, hi, best = 0, len(values) - 1, 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.can_add(slot, values[mid]):
                best = values[mid]
                lo = mid + 1
            else:
                hi = mid - 1
        return best


def assign_venues(inst, assignment):
    """Return {exam: venue_id} for a feasible assignment, or None."""
    if inst.venues is None:
        return {}
    by_slot = {}
    for e, t in enumerate(assignment):
        by_slot.setdefault(t, []).append(e)
    venues_desc = sorted(inst.venues, key=lambda v: -v.capacity)
    rooms = {}
    for t, exams in by_slot.items():
        exams = sorted(exams, key=lambda e: -inst.sizes[e])
        if len(exams) > len(venues_desc):
            return None
        for e, v in zip(exams, venues_desc):
            if inst.sizes[e] > v.capacity:
                return None
            rooms[e] = v.id
    return rooms


def violations(inst, assignment):
    """Count every violated hard constraint. Zero means conflict-free.

    Unassigned exams (slot -1 or None) count as one violation each.
    """
    count = 0
    for e, t in enumerate(assignment):
        if t is None or t < 0 or t >= inst.num_slots:
            count += 1
        elif t not in inst.allowed[e]:
            count += 1
    for v in range(inst.n):
        tv = assignment[v]
        if tv is None or tv < 0:
            continue
        for u in inst.adj[v]:
            if u > v and assignment[u] == tv:
                count += 1
    if inst.venues is not None:
        by_slot = {}
        for e, t in enumerate(assignment):
            if t is not None and t >= 0:
                by_slot.setdefault(t, []).append(inst.sizes[e])
        caps_asc = sorted(inst.caps_desc)
        for sizes in by_slot.values():
            sizes.sort()
            # Exams that cannot be seated: m minus the size of a maximum
            # matching. Matching the smallest unseated exam to the smallest
            # venue that fits it is optimal for threshold relations.
            i = matched = 0
            for cap in caps_asc:
                if i < len(sizes) and sizes[i] <= cap:
                    matched += 1
                    i += 1
            count += len(sizes) - matched
    return count


def slots_used(assignment):
    """Timetable length: highest slot index used plus one."""
    if not assignment:
        return 0
    return max(assignment) + 1


@dataclass
class SolveResult:
    algorithm: str
    assignment: list | None
    slots: int | None
    nodes: int = 0
    seconds: float = 0.0
    status: str = "solved"         # solved | infeasible | limit | failed
    optimal: bool = False          # proven optimal for the min-slots problem
    lower_bound: int | None = None
    extra: dict = field(default_factory=dict)
