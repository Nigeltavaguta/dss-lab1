"""Seeded instance generators.

* ``random_instance``: Erdos-Renyi conflict graph, unlimited rooms. This is
  plain graph colouring and is the "Random" dataset in the experiments.
* ``uz_instance``: a synthetic instance shaped like a university exam
  session (faculties, programmes, Part 1-4 cohorts, shared service courses,
  electives, carry-over students, lecturers with unavailable sessions, and
  venues of mixed capacity). It is "UZ-inspired": the structure follows how
  a large university schedules exams, but every name and number is generated.
* ``crown_instance``: the bipartite crown graph used to show that greedy
  colouring can be arbitrarily far from optimal.
"""

from __future__ import annotations

import random

from .model import Exam, Instance, Lecturer, StudentGroup, Venue


def _graph_instance(adj_edges, n, name, num_slots=None):
    exams = [Exam(i, f"E{i:03d}", 1, lecturer=i) for i in range(n)]
    return Instance(exams, num_slots if num_slots is not None else max(n, 1),
                    venues=None, extra_edges=adj_edges, name=name)


def random_instance(n, p, seed):
    rng = random.Random(seed)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
    return _graph_instance(edges, n, f"random-n{n}-p{p}-s{seed}")


def graph_instance(adj, name="graph", num_slots=None):
    edges = [(v, u) for v in range(len(adj)) for u in adj[v] if v < u]
    return _graph_instance(edges, len(adj), name, num_slots)


def crown_instance(k):
    """Crown graph on 2k vertices: a_i -- b_j for all i != j.

    Vertex a_i is 2i and b_i is 2i + 1, so the natural order 0, 1, 2, ...
    is the interleaved order a_0, b_0, a_1, b_1, ... that defeats greedy.
    """
    edges = [(2 * i, 2 * j + 1) for i in range(k) for j in range(k) if i != j]
    return _graph_instance(edges, 2 * k, f"crown-{k}")


FACULTIES = ["ENG", "SCI", "COM", "LAW", "MED", "AGR", "SOC", "EDU", "ART", "VET"]
VENUE_TYPES = [  # (name prefix, capacity)
    ("Hall", 600), ("Hall", 400), ("LT", 250), ("LT", 180),
    ("LT", 120), ("Room", 80), ("Room", 60), ("Room", 40),
]


def uz_instance(n_exams, seed, days=15, sessions_per_day=2,
                unavailable_share=0.15):
    """Generate a UZ-inspired instance with exactly ``n_exams`` exams.

    Structure, per faculty and per Part (year) 1-4:
      * 1-2 faculty service courses taken by every cohort in that Part;
      * 2-4 programme cohorts, each with 3-4 core courses of its own;
      * one elective per cohort taken by a subset of the cohort;
      * a few carry-over students who sit a Part k course and a Part k-1
        course of the same programme.
    Courses are generated faculty by faculty until ``n_exams`` exist; groups
    that refer to courses beyond the cut-off are trimmed.
    """
    rng = random.Random(seed)
    num_slots = days * sessions_per_day
    courses = []          # (code, faculty index)
    groups_raw = []       # (name, size, [courses], kind, [courses it adds seats to])
    lecturer_of = []
    faculty_lecturers = {}
    next_lecturer = [0]

    def new_lecturer(fac):
        pool = faculty_lecturers.setdefault(fac, [])
        # Lecturers usually teach 1-3 courses; reuse one 45% of the time.
        if pool and rng.random() < 0.45:
            return rng.choice(pool)
        lid = next_lecturer[0]
        next_lecturer[0] += 1
        pool.append(lid)
        return lid

    def new_course(code, fac):
        courses.append(code)
        lecturer_of.append(new_lecturer(fac))
        return len(courses) - 1

    fac_round = 0
    while len(courses) < n_exams:
        fac = fac_round % len(FACULTIES)
        prefix = FACULTIES[fac] + (str(fac_round // len(FACULTIES)) if fac_round >= len(FACULTIES) else "")
        fac_round += 1
        n_programmes = rng.randint(2, 4)
        previous_core = {}
        for part in range(1, 5):
            service = [new_course(f"{prefix}{part}0{s}", fac)
                       for s in range(rng.randint(1, 2))]
            for prog in range(n_programmes):
                pcode = f"{prefix}-{chr(65 + prog)}"
                size = max(15, int(rng.gauss(120 - 18 * part, 35)))
                core = [new_course(f"{pcode}{part}{c + 1}", fac)
                        for c in range(rng.randint(3, 4))]
                elective = new_course(f"{pcode}{part}9", fac)
                groups_raw.append((f"{pcode} Part {part}", size, service + core,
                                   "cohort", service + core))
                # Elective students are a subset of the cohort, so they add
                # seats only to the elective course itself.
                take = max(5, int(size * rng.uniform(0.2, 0.5)))
                groups_raw.append((f"{pcode} Part {part} elective", take,
                                   service + core + [elective], "elective",
                                   [elective]))
                if part > 1 and previous_core.get(prog):
                    for _ in range(rng.randint(1, 3)):
                        carried = rng.choice(previous_core[prog])
                        groups_raw.append((f"{pcode} Part {part} carry-over",
                                           rng.randint(1, 6),
                                           core + [carried], "carry-over",
                                           [carried]))
                previous_core[prog] = core

    # Trim to exactly n_exams and drop references to removed courses.
    # Carry-over students are already counted in their current cohort, so
    # they add seats only to the repeated course.
    keep = n_exams
    sizes = [0] * keep
    groups = []
    for name, size, members, kind, seats_for in groups_raw:
        members = tuple(sorted({m for m in members if m < keep}))
        if len(members) == 0:
            continue
        groups.append(StudentGroup(len(groups), name, size, members, kind))
        for m in seats_for:
            if m < keep:
                sizes[m] += size
    sizes = [max(1, s) for s in sizes]

    used_lecturers = sorted(set(lecturer_of[:keep]))
    lecturers = []
    for lid in used_lecturers:
        unavailable = frozenset()
        if rng.random() < unavailable_share:
            unavailable = frozenset(rng.sample(range(num_slots), rng.randint(2, 6)))
        lecturers.append(Lecturer(lid, f"L{lid:03d}", unavailable))
    exams = [Exam(i, courses[i], sizes[i], lecturer_of[i]) for i in range(keep)]

    # Venues: enough rooms that each session can host roughly n/10 exams,
    # with the largest hall big enough for the largest exam.
    n_venues = max(5, n_exams // 8)
    venues = []
    for i in range(n_venues):
        prefix, cap = VENUE_TYPES[i % len(VENUE_TYPES)] if i < len(VENUE_TYPES) \
            else rng.choice(VENUE_TYPES[2:])
        venues.append(Venue(i, f"{prefix} {i + 1}", cap))
    biggest = max(sizes)
    if venues[0].capacity < biggest:
        venues[0] = Venue(0, venues[0].name, biggest)
    return Instance(exams, num_slots, venues=venues, lecturers=lecturers,
                    groups=groups, name=f"uz-n{n_exams}-s{seed}")

