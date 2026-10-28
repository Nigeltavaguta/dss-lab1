"""Generate transaction-like test data."""
import random

def generate(kind, n, seed=42):
    rng=random.Random(seed)
    a=[(rng.randrange(1_700_000_000,1_800_000_000),rng.randrange(1,10_000_000),f"m{rng.randrange(1000):04d}",i) for i in range(n)]
    k=(0,1,2)
    if kind=="sorted": return sorted(a,key=lambda x:tuple(x[i] for i in k))
    if kind=="reverse": return sorted(a,key=lambda x:tuple(x[i] for i in k),reverse=True)
    if kind=="nearly_sorted":
        a.sort(key=lambda x:tuple(x[i] for i in k))
        for _ in range(max(1,n//100)):
            i,j=rng.randrange(n),rng.randrange(n); a[i],a[j]=a[j],a[i]
        return a
    if kind=="adversarial":
        # This pattern targets Lomuto endpoint pivots and includes repeated merchant names.
        return [(i, i%7, "same", i) for i in range(n)]
    if kind=="random": return a
    raise ValueError(kind)

KINDS=("random","sorted","reverse","nearly_sorted","adversarial")
