"""Unit and edge-case tests for the Exam Timetabling Engine.

Run from the project folder:  python -m unittest discover -s tests -v
"""

import itertools
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ete.backtracking import backtracking, min_slots_backtracking, naive_backtracking
from ete.bounds import clique_bound, greedy_clique, lower_bound, venue_bound
from ete.branch_bound import branch_and_bound
from ete.generators import crown_instance, graph_instance, random_instance, uz_instance
from ete.greedy import greedy
from ete.hybrid import hybrid
from ete.local_search import local_search
from ete.model import (Exam, Instance, Lecturer, StudentGroup, Venue, VenueState,
                       assign_venues, sizes_fit, slots_used, violations)
from ete.reductions import (assignment_from_colouring, brute_force_sat,
                            colouring_to_timetabling, is_satisfied, random_3sat,
                            sat_to_colouring)


def cycle(n):
    return graph_instance([{(i - 1) % n, (i + 1) % n} for i in range(n)], f"C{n}")


def complete(n):
    return graph_instance([set(range(n)) - {i} for i in range(n)], f"K{n}")


def petersen():
    outer = [(i, (i + 1) % 5) for i in range(5)]
    spokes = [(i, i + 5) for i in range(5)]
    inner = [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    adj = [set() for _ in range(10)]
    for a, b in outer + spokes + inner:
        adj[a].add(b)
        adj[b].add(a)
    return graph_instance(adj, "petersen")


def brute_chromatic(inst):
    """Exhaustive minimum over all assignments (tiny instances only)."""
    for k in range(1, inst.n + 1):
        for colours in itertools.product(range(k), repeat=inst.n):
            if violations(inst, list(colours)) == 0:
                return k
    return None


KNOWN = [(cycle(5), 3), (cycle(6), 2), (complete(5), 5), (petersen(), 3),
         (crown_instance(4), 2), (graph_instance([set()], "K1"), 1)]


class ModelTests(unittest.TestCase):
    def test_conflict_graph_from_groups_and_lecturers(self):
        exams = [Exam(0, "A", 10, 0), Exam(1, "B", 10, 1), Exam(2, "C", 10, 0)]
        groups = [StudentGroup(0, "g", 10, (0, 1))]
        inst = Instance(exams, 3, groups=groups)
        self.assertEqual(inst.adj[0], {1, 2})   # student link and lecturer link
        self.assertEqual(inst.adj[1], {0})

    def test_unavailability_restricts_domain(self):
        exams = [Exam(0, "A", 10, 7)]
        inst = Instance(exams, 4, lecturers=[Lecturer(7, "L", frozenset({1, 3}))])
        self.assertEqual(inst.allowed[0], frozenset({0, 2}))
        self.assertFalse(inst.symmetric)
        self.assertEqual(violations(inst, [1]), 1)
        self.assertEqual(violations(inst, [2]), 0)

    def test_sizes_fit_matches_brute_force_matching(self):
        rng = random.Random(3)
        for _ in range(300):
            caps = [rng.randint(1, 10) for _ in range(rng.randint(1, 5))]
            sizes = [rng.randint(1, 10) for _ in range(rng.randint(1, 5))]
            brute = any(all(s <= caps[p] for s, p in zip(sizes, perm))
                        for perm in itertools.permutations(range(len(caps)), len(sizes))) \
                if len(sizes) <= len(caps) else False
            self.assertEqual(sizes_fit(sorted(sizes, reverse=True),
                                       sorted(caps, reverse=True)), brute)

    def test_venue_state_incremental(self):
        venues = [Venue(0, "big", 100), Venue(1, "small", 30)]
        inst = Instance([Exam(i, str(i), s, i) for i, s in enumerate([90, 25, 50])],
                        2, venues=venues)
        vs = VenueState(inst, 2)
        self.assertTrue(vs.can_add(0, 90))
        vs.add(0, 90)
        self.assertTrue(vs.can_add(0, 25))
        self.assertFalse(vs.can_add(0, 50))       # 50 does not fit the small room
        self.assertEqual(vs.max_addable(0), 30)
        vs.add(0, 25)
        self.assertFalse(vs.can_add(0, 1))        # both rooms taken
        vs.remove(0, 25)
        self.assertTrue(vs.can_add(0, 30))

    def test_violations_counts_each_problem(self):
        inst = complete(3)
        self.assertEqual(violations(inst, [0, 0, 0]), 3)
        self.assertEqual(violations(inst, [0, 1, -1]), 1)
        self.assertEqual(violations(inst, [0, 1, 2]), 0)

    def test_assign_venues_gives_distinct_fitting_rooms(self):
        inst = uz_instance(60, 4)
        res = hybrid(inst, time_limit=2)
        rooms = assign_venues(inst, res.assignment)
        caps = {v.id: v.capacity for v in inst.venues}
        seen = set()
        for e, room in rooms.items():
            self.assertLessEqual(inst.sizes[e], caps[room])
            key = (res.assignment[e], room)
            self.assertNotIn(key, seen)
            seen.add(key)


class BoundTests(unittest.TestCase):
    def test_clique_is_a_clique(self):
        inst = random_instance(40, 0.4, 2)
        clique = greedy_clique(inst.adj)
        for a, b in itertools.combinations(clique, 2):
            self.assertIn(b, inst.adj[a])

    def test_bounds_never_exceed_optimum(self):
        for seed in range(8):
            inst = random_instance(9, 0.45, seed)
            self.assertLessEqual(lower_bound(inst), brute_chromatic(inst))
        for inst, chi in KNOWN:
            self.assertLessEqual(clique_bound(inst), chi)

    def test_venue_bound(self):
        venues = [Venue(0, "a", 100), Venue(1, "b", 20)]
        exams = [Exam(i, str(i), 80, i) for i in range(3)] + [Exam(3, "x", 10, 3)]
        inst = Instance(exams, 6, venues=venues)
        self.assertEqual(venue_bound(inst), 3)  # three exams need the one big room


class SolverTests(unittest.TestCase):
    def test_known_chromatic_numbers(self):
        for inst, chi in KNOWN:
            with self.subTest(inst.name):
                res = branch_and_bound(inst)
                self.assertTrue(res.optimal)
                self.assertEqual(res.slots, chi)
                self.assertEqual(violations(inst, res.assignment), 0)

    def test_bnb_matches_brute_force(self):
        for seed in range(10):
            inst = random_instance(8, 0.5, seed)
            res = branch_and_bound(inst, use_greedy_ub=False, use_lower_bound=False)
            self.assertEqual(res.slots, brute_chromatic(inst))

    def test_all_backtracking_variants_agree(self):
        variants = [
            lambda i, k: naive_backtracking(i, k),
            lambda i, k: backtracking(i, k, mrv=False, degree=False),
            lambda i, k: backtracking(i, k, degree=False),
            lambda i, k: backtracking(i, k),
            lambda i, k: backtracking(i, k, mac=True),
        ]
        for seed in range(6):
            inst = random_instance(12, 0.4, seed)
            chi = branch_and_bound(inst).slots
            for solve in variants:
                ok = solve(inst, chi)
                self.assertEqual(ok.status, "solved")
                self.assertEqual(violations(inst, ok.assignment), 0)
                self.assertEqual(solve(inst, chi - 1).status, "infeasible")

    def test_backtracking_respects_venues_and_availability(self):
        inst = uz_instance(30, 2)
        res = min_slots_backtracking(inst, time_limit=20)
        self.assertEqual(res.status, "solved")
        self.assertEqual(violations(inst, res.assignment), 0)
        self.assertEqual(res.slots, branch_and_bound(inst).slots)

    def test_node_limit_reports_limit(self):
        inst = random_instance(40, 0.5, 1)
        res = naive_backtracking(inst, 3, node_limit=100)
        self.assertEqual(res.status, "limit")
        self.assertEqual(res.nodes, 100)

    def test_greedy_within_delta_plus_one(self):
        for seed in range(10):
            inst = random_instance(60, 0.2, seed)
            for order in ("natural", "largest_first", "dsatur", "random"):
                res = greedy(inst, order, seed)
                self.assertEqual(violations(inst, res.assignment), 0)
                self.assertLessEqual(res.slots, inst.max_degree() + 1)

    def test_greedy_crown_worst_case(self):
        for k in range(2, 8):
            inst = crown_instance(k)
            self.assertEqual(greedy(inst, "natural").slots, k)
            self.assertEqual(greedy(inst, "dsatur").slots, 2)

    def test_local_search_never_worsens(self):
        inst = random_instance(80, 0.15, 5)
        start = greedy(inst, "natural")
        res = local_search(inst, start.assignment, time_limit=1)
        self.assertLessEqual(res.slots, start.slots)
        self.assertEqual(violations(inst, res.assignment), 0)

    def test_hybrid_conflict_free_on_uz(self):
        for n in (40, 150):
            inst = uz_instance(n, 7)
            res = hybrid(inst, time_limit=3)
            self.assertEqual(violations(inst, res.assignment), 0)
            self.assertGreaterEqual(res.slots, res.lower_bound)

    def test_edge_cases(self):
        empty = Instance([], 3)
        self.assertEqual(branch_and_bound(empty).status, "solved")
        self.assertEqual(greedy(empty).slots, 0)
        one = graph_instance([set()], "single")
        self.assertEqual(hybrid(one).slots, 1)
        # An exam larger than every venue makes the instance infeasible.
        too_big = Instance([Exam(0, "A", 500, 0)], 3, venues=[Venue(0, "r", 100)])
        self.assertEqual(greedy(too_big).status, "failed")
        self.assertEqual(branch_and_bound(too_big).status, "infeasible")
        # Too few slots for a clique.
        k4 = graph_instance([set(range(4)) - {i} for i in range(4)], "K4", num_slots=3)
        self.assertEqual(branch_and_bound(k4).status, "infeasible")


class ReductionTests(unittest.TestCase):
    def test_sat_iff_three_colourable(self):
        for seed in range(25):
            nv = 3 + seed % 3
            clauses = random_3sat(nv, 4 + seed % 6, seed)
            adj = sat_to_colouring(clauses, nv)
            inst = colouring_to_timetabling(adj, 3)
            res = backtracking(inst, 3, mac=True)
            sat = brute_force_sat(clauses, nv) is not None
            self.assertEqual(res.status == "solved", sat)
            if sat:
                values = assignment_from_colouring(res.assignment, nv)
                self.assertTrue(is_satisfied(clauses, values))

    def test_unsatisfiable_formula(self):
        # All 8 sign patterns over x1, x2, x3: unsatisfiable.
        clauses = [tuple(s * v for s, v in zip(signs, (1, 2, 3)))
                   for signs in itertools.product((1, -1), repeat=3)]
        adj = sat_to_colouring(clauses, 3)
        self.assertEqual(len(adj), 3 + 2 * 3 + 6 * len(clauses))
        res = backtracking(colouring_to_timetabling(adj, 3), 3, mac=True)
        self.assertEqual(res.status, "infeasible")

    def test_colouring_to_timetabling_preserves_edges(self):
        inst = random_instance(15, 0.3, 9)
        reduced = colouring_to_timetabling(inst.adj, 4)
        self.assertEqual(reduced.adj, inst.adj)
        self.assertEqual(reduced.num_slots, 4)


if __name__ == "__main__":
    unittest.main()
