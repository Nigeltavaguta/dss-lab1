"""Sorting algorithms for Lab 2. Records are tuples (timestamp, amount, merchant, id)."""
from __future__ import annotations
import heapq

COMPARISONS = 0
COUNT_COMPARISONS = False

class _CountedKey(tuple):
    def _compare(self, other, op):
        global COMPARISONS
        if COUNT_COMPARISONS: COMPARISONS += 1
        return op(tuple(self), tuple(other))
    def __lt__(self, other): return self._compare(other, tuple.__lt__)
    def __le__(self, other): return self._compare(other, tuple.__le__)
    def __gt__(self, other): return self._compare(other, tuple.__gt__)
    def __ge__(self, other): return self._compare(other, tuple.__ge__)

def reset_comparisons(enabled=False):
    global COMPARISONS, COUNT_COMPARISONS
    COMPARISONS=0; COUNT_COMPARISONS=enabled

def key(r):
    values=(r[0], r[1], r[2])
    return _CountedKey(values) if COUNT_COMPARISONS else values

def insertion(a, lo=0, hi=None):
    hi = len(a) if hi is None else hi
    for i in range(lo + 1, hi):
        x, j = a[i], i
        while j > lo and key(a[j - 1]) > key(x):
            a[j] = a[j - 1]; j -= 1
        a[j] = x

def merge_sort(a):
    n = len(a); buf = [None] * n
    def rec(lo, hi):
        if hi - lo < 2: return
        mid = (lo + hi) // 2; rec(lo, mid); rec(mid, hi)
        i, j, k = lo, mid, lo
        while i < mid and j < hi:
            if key(a[i]) <= key(a[j]): buf[k] = a[i]; i += 1
            else: buf[k] = a[j]; j += 1
            k += 1
        while i < mid: buf[k] = a[i]; i += 1; k += 1
        while j < hi: buf[k] = a[j]; j += 1; k += 1
        a[lo:hi] = buf[lo:hi]
    rec(0, n); return a

def quick_lomuto(a):
    def part(lo, hi):
        p = key(a[hi]); i = lo
        for j in range(lo, hi):
            if key(a[j]) <= p: a[i], a[j] = a[j], a[i]; i += 1
        a[i], a[hi] = a[hi], a[i]; return i
    stack = [(0, len(a)-1)] if a else []
    while stack:
        lo, hi = stack.pop()
        while lo < hi:
            p = part(lo, hi)
            left, right = (lo, p-1), (p+1, hi)
            # Defer the larger side and immediately process the smaller one.
            if left[1]-left[0] < right[1]-right[0]:
                if right[0] < right[1]: stack.append(right)
                lo, hi = left
            else:
                if left[0] < left[1]: stack.append(left)
                lo, hi = right
    return a

def quick_hoare(a):
    def part(lo, hi):
        p = key(a[(lo+hi)//2]); i, j = lo-1, hi+1
        while True:
            i += 1
            while key(a[i]) < p: i += 1
            j -= 1
            while key(a[j]) > p: j -= 1
            if i >= j: return j
            a[i], a[j] = a[j], a[i]
    stack = [(0, len(a)-1)] if a else []
    while stack:
        lo, hi = stack.pop()
        if lo < hi:
            p = part(lo, hi); stack.extend(((lo, p), (p+1, hi)))
    return a

def quick_median_of_medians(a):
    """In-place BFPRT pivots, three-way partition, iterative quicksort."""
    def small_sort(lo,hi):
        for i in range(lo+1,hi+1):
            item=a[i]; j=i
            while j>lo and key(a[j-1])>key(item): a[j]=a[j-1]; j-=1
            a[j]=item
    def select(lo,hi,k):
        while True:
            size=hi-lo+1
            if size<=5:
                small_sort(lo,hi); return a[k]
            groups=0; start=lo
            while start<=hi:
                end=min(start+4,hi); small_sort(start,end)
                median=start+(end-start)//2
                a[lo+groups],a[median]=a[median],a[lo+groups]
                groups+=1; start+=5
            pivot=select(lo,lo+groups-1,lo+(groups-1)//2)
            p=key(pivot); lt,i,gt=lo,lo,hi
            while i<=gt:
                ki=key(a[i])
                if ki<p: a[lt],a[i]=a[i],a[lt]; lt+=1; i+=1
                elif ki>p: a[i],a[gt]=a[gt],a[i]; gt-=1
                else: i+=1
            if k<lt: hi=lt-1
            elif k>gt: lo=gt+1
            else: return a[k]
    if len(a)<2:return a
    stack=[(0,len(a)-1)]
    while stack:
        lo,hi=stack.pop()
        while lo<hi:
            pivot=select(lo,hi,(lo+hi)//2); p=key(pivot); lt,i,gt=lo,lo,hi
            while i<=gt:
                ki=key(a[i])
                if ki<p: a[lt],a[i]=a[i],a[lt]; lt+=1; i+=1
                elif ki>p: a[i],a[gt]=a[gt],a[i]; gt-=1
                else: i+=1
            left,right=(lo,lt-1),(gt+1,hi)
            if lt-lo < hi-gt:
                if right[0]<right[1]: stack.append(right)
                lo,hi=left
            else:
                if left[0]<left[1]: stack.append(left)
                lo,hi=right
    return a

def heap_sort(a):
    n = len(a)
    def sift(root, end):
        while 2*root+1 < end:
            child=2*root+1
            if child+1 < end and key(a[child]) < key(a[child+1]): child += 1
            if key(a[root]) >= key(a[child]): return
            a[root],a[child]=a[child],a[root]; root=child
    for i in range(n//2-1,-1,-1): sift(i,n)
    for end in range(n-1,0,-1): a[0],a[end]=a[end],a[0]; sift(0,end)
    return a

def tim_sort(a):
    a.sort(key=key); return a

def tim_sort_educational(a, min_run=32):
    """Simplified stable Timsort with run detection and stack-based merging."""
    n=len(a)
    if n<2:return a
    runs=[]
    def merge_at(i):
        lo,mid=runs[i]; _,hi=runs[i+1]
        _merge_sorted_runs(a,lo,mid,hi)
        runs[i:i+2]=[[lo,hi]]
    start=0
    while start<n:
        end=start+1
        descending=end<n and key(a[end])<key(a[start])
        if descending:
            end+=1
            while end<n and key(a[end])<key(a[end-1]):end+=1
            a[start:end]=reversed(a[start:end])
        else:
            while end<n and key(a[end])>=key(a[end-1]):end+=1
        target=min(n,max(end,start+min_run))
        # Binary insertion extends a short natural run to min_run.
        for i in range(end,target):
            item=a[i]; lo,hi=start,i
            while lo<hi:
                mid=(lo+hi)//2
                if key(item)<key(a[mid]):hi=mid
                else:lo=mid+1
            a[lo+1:i+1]=a[lo:i]; a[lo]=item
        runs.append([start,target]); start=target
        while len(runs)>1:
            m=len(runs)
            if m>=3 and runs[m-3][1]-runs[m-3][0] <= (runs[m-2][1]-runs[m-2][0])+(runs[m-1][1]-runs[m-1][0]):
                merge_at(m-3 if runs[m-3][1]-runs[m-3][0] < runs[m-1][1]-runs[m-1][0] else m-2)
            elif runs[m-2][1]-runs[m-2][0] <= runs[m-1][1]-runs[m-1][0]:
                merge_at(m-2)
            else:
                break
    # Collapse runs in an order that keeps total merge work O(n log n).
    while len(runs)>1:
        m=len(runs)
        if m>=3 and runs[m-3][1]-runs[m-3][0] <= (runs[m-2][1]-runs[m-2][0])+(runs[m-1][1]-runs[m-1][0]):
            merge_at(m-3 if runs[m-3][1]-runs[m-3][0] < runs[m-1][1]-runs[m-1][0] else m-2)
        elif m>=2:merge_at(m-2)
    return a

def _merge_sorted_runs(a,lo,mid,hi):
    left=a[lo:mid]; right=a[mid:hi]; i=j=0; k=lo
    while i<len(left) and j<len(right):
        if key(left[i])<=key(right[j]):a[k]=left[i];i+=1
        else:a[k]=right[j];j+=1
        k+=1
    while i<len(left):a[k]=left[i];i+=1;k+=1
    while j<len(right):a[k]=right[j];j+=1;k+=1

def hybrid_sort(a, threshold=24):
    """Exploit natural runs; use introsort when run detection finds disorder."""
    n=len(a)
    if n < 2: return a
    # Detect/reverse descending runs, then merge adjacent runs (Timsort-like adaptivity).
    runs=[]; i=0
    while i<n:
        j=i+1
        if j<n and key(a[j]) < key(a[i]):
            j+=1
            while j<n and key(a[j]) < key(a[j-1]): j+=1
            a[i:j]=reversed(a[i:j])
        else:
            while j<n and key(a[j]) >= key(a[j-1]): j+=1
        runs.append((i,j)); i=j
    if len(runs)==1: return a
    # A highly fragmented run structure falls back to introsort, whose heap
    # fallback guarantees O(n log n) even for adversarial pivot patterns.
    if len(runs) > max(2, n // threshold):
        _introsort(a, threshold)
        return a
    while len(runs)>1:
        merged=[]
        for x in range(0,len(runs),2):
            if x+1==len(runs): merged.append(runs[x]); continue
            lo,mid=runs[x]; _,hi=runs[x+1]
            _merge_sorted_runs(a,lo,mid,hi); merged.append((lo,hi))
        runs=merged
    return a

def _introsort(a, threshold=24):
    n=len(a); limit=2*(n.bit_length()-1)
    def part(lo,hi):
        mid=(lo+hi)//2
        trio=sorted((a[lo],a[mid],a[hi]),key=key); pivot=key(trio[1])
        i,j=lo,hi
        while i<=j:
            while key(a[i])<pivot: i+=1
            while key(a[j])>pivot: j-=1
            if i<=j: a[i],a[j]=a[j],a[i]; i+=1; j-=1
        return i
    def rec(lo,hi,depth):
        while hi-lo>threshold:
            if depth==0:
                # In-place heap sort on this range.
                size=hi-lo+1
                def sift(root,end):
                    while 2*root+1<end:
                        c=2*root+1
                        if c+1<end and key(a[lo+c])<key(a[lo+c+1]): c+=1
                        if key(a[lo+root])>=key(a[lo+c]): return
                        a[lo+root],a[lo+c]=a[lo+c],a[lo+root]; root=c
                for q in range(size//2-1,-1,-1): sift(q,size)
                for e in range(size-1,0,-1): a[lo],a[lo+e]=a[lo+e],a[lo]; sift(0,e)
                return
            depth-=1; cut=part(lo,hi)
            # Recurse into smaller partition and loop over larger: bounded stack.
            if cut-lo < hi-cut+1: rec(lo,cut-1,depth); lo=cut
            else: rec(cut,hi,depth); hi=cut-1
        insertion(a,lo,hi+1)
    rec(0,n-1,limit)

ALGORITHMS={"merge":merge_sort,"quick_lomuto":quick_lomuto,"quick_hoare":quick_hoare,"quick_mom":quick_median_of_medians,"heap":heap_sort,"timsort":tim_sort,"timsort_edu":tim_sort_educational,"hybrid":hybrid_sort}
