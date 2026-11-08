# Instance generators, all seeded. Graphs come back as adj: list of sets.
import random


def random_graph(n, p, seed):
    rng = random.Random(seed)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def timetabling_instance(num_exams, num_students, exams_per_student, seed):
    # Exams = vertices. Each student is enrolled in a random handful of
    # exams; two exams conflict (edge) if at least one student takes both.
    # This gives the clustered, uneven-degree structure real registration
    # data has, unlike a uniform-random Erdos-Renyi graph.
    rng = random.Random(seed)
    adj = [set() for _ in range(num_exams)]
    for _ in range(num_students):
        k = min(exams_per_student, num_exams)
        taken = rng.sample(range(num_exams), k)
        for i in range(len(taken)):
            for j in range(i + 1, len(taken)):
                a, b = taken[i], taken[j]
                adj[a].add(b)
                adj[b].add(a)
    return adj


def crown_graph(n):
    # Complete bipartite K(n,n) minus a perfect matching: a_i adjacent to
    # b_j for every i != j (a_i-b_i is the removed matching edge). Both
    # sides are independent sets, so chi = 2 (all a's one color, all b's
    # the other). But colored in the interleaved order a_0,b_0,a_1,b_1,...,
    # greedy is forced to keep opening new colors - see the report.
    size = 2 * n
    adj = [set() for _ in range(size)]

    def a(i):
        return 2 * i

    def b(i):
        return 2 * i + 1

    for i in range(n):
        for j in range(n):
            if i != j:
                adj[a(i)].add(b(j))
                adj[b(j)].add(a(i))
    return adj
