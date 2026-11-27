"""Polynomial-time reductions used in the NP-completeness proof.

3-SAT <=p 3-COLOURING <=p EXAM-TIMETABLING (decision version).

A 3-CNF formula is a list of clauses. Each clause is a tuple of three
non-zero integers in DIMACS style: literal +i is x_i and -i is NOT x_i.
"""

from __future__ import annotations

import itertools
import random

from .model import Exam, Instance, StudentGroup

# Palette vertices of the 3-colouring gadget.
TRUE, FALSE, BASE = 0, 1, 2


def sat_to_colouring(clauses, num_vars):
    """Build a graph that is 3-colourable iff the formula is satisfiable.

    Vertices 0, 1, 2 form the palette triangle (T, F, B). For each variable
    x_i, the vertices x_i and NOT x_i form a triangle with B, so one of them
    is coloured T and the other F. Each clause (a or b or c) uses two OR
    gadgets: o1 = OR(a, b) and o2 = OR(o1, c), where o2 is joined to F and
    B. The output of OR(p, q) can be coloured T iff p or q is coloured T.
    Size: 3 + 2n + 6m vertices and 3 + 3n + 12m edges.
    """
    edges = [(TRUE, FALSE), (FALSE, BASE), (TRUE, BASE)]
    count = 3

    def lit(l):
        i = abs(l) - 1
        return 3 + 2 * i + (0 if l > 0 else 1)

    for i in range(num_vars):
        pos, neg = 3 + 2 * i, 3 + 2 * i + 1
        edges += [(pos, neg), (pos, BASE), (neg, BASE)]
    count = 3 + 2 * num_vars

    def or_gadget(a, b):
        nonlocal count
        u, v, o = count, count + 1, count + 2
        count += 3
        edges.extend([(a, u), (b, v), (u, v), (u, o), (v, o)])
        return o

    for clause in clauses:
        a, b, c = (lit(l) for l in clause)
        o1 = or_gadget(a, b)
        o2 = or_gadget(o1, c)
        edges.extend([(o2, FALSE), (o2, BASE)])

    adj = [set() for _ in range(count)]
    for x, y in edges:
        adj[x].add(y)
        adj[y].add(x)
    return adj


def colouring_to_timetabling(adj, k):
    """Map a k-colouring question to a timetabling instance with k slots.

    Each vertex becomes an exam with its own lecturer. Each edge becomes a
    one-student group taking both exams. Rooms are unlimited and no lecturer
    has unavailable slots. A conflict-free timetable with k slots exists iff
    the graph is k-colourable, and the slot of each exam is its colour.
    """
    n = len(adj)
    exams = [Exam(v, f"V{v}", 1, lecturer=v) for v in range(n)]
    groups = []
    for v in range(n):
        for u in adj[v]:
            if v < u:
                groups.append(StudentGroup(len(groups), f"s{v}-{u}", 1, (v, u)))
    return Instance(exams, k, venues=None, groups=groups, name=f"reduced-k{k}")


def colouring_from_assignment(clauses, num_vars, values):
    """Build the 3-colouring promised by the proof from a satisfying
    assignment, following the same vertex numbering as sat_to_colouring.

    Literal vertices get T or F from the assignment. In each OR gadget the
    output is T when an input is T (else F), and the two inner vertices take
    the first colour pair that is consistent with their neighbours.
    Returns None if the assignment does not satisfy the formula, because the
    last gadget output then cannot be coloured T.
    """
    colour = [TRUE, FALSE, BASE]
    for i in range(num_vars):
        colour += [TRUE, FALSE] if values[i] else [FALSE, TRUE]

    def lit(l):
        return 3 + 2 * (abs(l) - 1) + (0 if l > 0 else 1)

    def gadget(ca, cb):
        out = TRUE if TRUE in (ca, cb) else FALSE
        for cu in range(3):
            for cv in range(3):
                if cu != ca and cv != cb and cu != cv and out not in (cu, cv):
                    return [cu, cv, out]
        raise AssertionError("OR gadget has no valid colouring")

    for clause in clauses:
        a, b, c = (lit(l) for l in clause)
        g1 = gadget(colour[a], colour[b])
        colour += g1
        g2 = gadget(g1[2], colour[c])
        colour += g2
        if g2[2] != TRUE:
            return None
    return colour


def assignment_from_colouring(colouring, num_vars):
    """Decode a satisfying assignment from a 3-colouring of the SAT graph."""
    t = colouring[TRUE]
    return [colouring[3 + 2 * i] == t for i in range(num_vars)]


def is_satisfied(clauses, values):
    return all(any(values[abs(l) - 1] == (l > 0) for l in c) for c in clauses)


def brute_force_sat(clauses, num_vars):
    for values in itertools.product((False, True), repeat=num_vars):
        if is_satisfied(clauses, values):
            return list(values)
    return None


def random_3sat(num_vars, num_clauses, seed):
    rng = random.Random(seed)
    clauses = []
    for _ in range(num_clauses):
        chosen = rng.sample(range(1, num_vars + 1), 3)
        clauses.append(tuple(v if rng.random() < 0.5 else -v for v in chosen))
    return clauses
