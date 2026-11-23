# residue_search.py -- THE CPU ENGINE for the power-residue ladders
# (A002226, A002227, A002228, A060363, A060364).
#
# An independent implementation of the sweep the GPU engine runs: numpy for
# the small-prime sieve, plain Python integers and `%` for every modular
# power (the GPU engine uses 64-bit Montgomery arithmetic and never calls
# this file; this file never calls it -- CLAUDE.md rule 3).  It appears in
# gates, in a campaign's sampled parity checks and in the confirmations of a
# find; it does not hunt.
#
# THE LINE.  A family is a power (5, 7, 11, 13 or 17).  Its candidates are
# the integers N = 2*power*j + 1, j = 1, 2, 3, ...: every prime p with p - 1
# divisible by the power is one of them (the power is odd, p is odd).  The
# engines index the line by j; every sentence a person reads says p.
#
# THE STREAM of a window [j0, j0 + count) at a floor f >= 1: every PRIME
# p = 2*power*j + 1 in it whose run -- the number of leading primes 2, 3, 5,
# ... that are residues of the power mod p -- is at least f, as (p, run),
# ascending.  Primality here is a complete sieve of Eratosthenes where the
# window's square root is within SIEVE_FULL, and the small-prime sieve plus
# huntlib's deterministic Miller-Rabin above it.
#
# Also here, because they are host mathematics a find's evidence needs and
# the oracle must stay boring: explicit roots (x with x^power == q mod p,
# so that "q is a residue" is checkable with one modular power), the
# witness that a prime is NOT a residue, and a Lucas certificate for p.

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from huntlib import primes as hprimes                         # noqa: E402

POWERS = (5, 7, 11, 13, 17)
P_CEIL = 2 ** 63            # the engines' enforced ceiling on p (README)
SIEVE_FULL = 1 << 22        # a complete sieve where sqrt(window top) <= this
RUN_CAP = 40                # primes a run is read against


def small_primes(limit):
    """The primes below `limit` (own sieve; no sympy in the engines)."""
    limit = int(limit)
    if limit < 3:
        return np.zeros(0, dtype=np.int64)
    s = np.ones(limit, dtype=bool)
    s[:2] = False
    for i in range(2, math.isqrt(limit - 1) + 1):
        if s[i]:
            s[i * i::i] = False
    return np.flatnonzero(s).astype(np.int64)


PRIMES = [int(q) for q in small_primes(174)]
assert len(PRIMES) == RUN_CAP
_SIEVE = small_primes(SIEVE_FULL + 1)


def value(power, j):
    """The candidate at index j of a family's line."""
    return 2 * int(power) * int(j) + 1


def index_of(power, p):
    """The index of p on the line (p - 1 must be divisible by 2*power)."""
    j, rem = divmod(int(p) - 1, 2 * int(power))
    if rem:
        raise ValueError(f"{p} is not on the line of power {power}")
    return j


def run_of(n, power, cap=RUN_CAP):
    """Leading primes q with q^((n-1)/power) == 1 (mod n); a q that is 0
    mod n ends the run.  For a prime n this is the run of the definition
    (Euler's criterion; the oracle's gate G1)."""
    e = (n - 1) // power
    r = 0
    for q in PRIMES[:cap]:
        if q % n == 0 or pow(q, e, n) != 1:
            break
        r += 1
    return r


def sieve_window(power, j0, count, bound=None):
    """Indices j in [j0, j0 + count) whose candidate has no prime factor
    <= bound other than itself; returns (js, complete), `complete` meaning
    the bound reaches the square root of the window's top (so every index
    returned is a prime's)."""
    power, j0, count = int(power), int(j0), int(count)
    top = value(power, j0 + count - 1)
    root = math.isqrt(top)
    if bound is None:
        bound = min(root, SIEVE_FULL)
    bound = min(int(bound), SIEVE_FULL)
    alive = np.ones(count, dtype=bool)
    step = 2 * power
    for q in _SIEVE[: int(np.searchsorted(_SIEVE, bound, side="right"))]:
        q = int(q)
        if q == 2 or q == power:
            continue                    # never divide a candidate
        # 2*power*(j0 + t) + 1 == 0 (mod q)
        t = (-pow(step, -1, q) - j0) % q
        alive[t::q] = False
        # the candidate that IS q stays
        jq, rem = divmod(q - 1, step)
        if rem == 0 and j0 <= jq < j0 + count:
            alive[jq - j0] = True
    js = np.flatnonzero(alive)
    return [j0 + int(t) for t in js], bound >= root


def sweep(power, j0, count, floor=1, bound=None):
    """THE STREAM: [(p, run)] for every prime p = 2*power*j + 1 with j in
    [j0, j0 + count) and run >= floor (floor >= 1), ascending."""
    if floor < 1:
        raise ValueError("the stream is defined for a floor of 1 or more")
    if value(power, int(j0) + int(count) - 1) >= P_CEIL:
        raise ValueError("window above the ceiling 2^63")
    js, complete = sieve_window(power, j0, count, bound)
    out = []
    for j in js:
        n = value(power, j)
        if n < 3:
            continue
        r = run_of(n, power)
        if r < floor:
            continue
        if not complete and not hprimes.mr_is_prime(n):
            continue
        out.append((n, r))
    return out


def first_test_composites(power, j0, count):
    """Composite candidates of the window that pass the GPU engine's first
    test anyway -- 2^j == +-1 (mod N), which for a prime N = 2*power*j + 1
    says 2^((N-1)/power) == 1: what a sweep with no sieve would hand the
    host besides primes.  Plain Python; for the GPU engine's gate P5."""
    out = []
    for j in range(int(j0), int(j0) + int(count)):
        n = value(power, j)
        if pow(2, j, n) in (1, n - 1) and not hprimes.mr_is_prime(n):
            out.append(n)
    return out


def first_test_passes(power, j0, count, skip=3):
    """Every index j of the window, prime or composite, whose candidate
    N = 2*power*j + 1 is not a proper multiple of `skip` and has
    2^j == +-1 (mod N): what the GPU engine's first test passes when its
    sieve holds the one prime `skip`.  Plain Python; for its gate P7."""
    out = []
    for j in range(int(j0), int(j0) + int(count)):
        n = value(power, j)
        if n > skip and n % skip == 0:
            continue
        if pow(2, j, n) in (1, n - 1):
            out.append(j)
    return out


# ------------------------------------------------------- a find's witnesses
def root(q, p, power):
    """x with x^power == q (mod p), for a prime p with power | p - 1 and q a
    residue (q^((p-1)/power) == 1).  Adleman-Manders-Miller for a prime
    power: split p - 1 = power^s * t, take the root in the part of order t
    by inverting the power mod t, and correct in the cyclic group of order
    power^s by a discrete logarithm found digit by digit.  The answer is
    checked before it is returned."""
    q, p, power = int(q) % int(p), int(p), int(power)
    if (p - 1) % power or pow(q, (p - 1) // power, p) != 1:
        raise ValueError(f"{q} is not a residue of the power {power} mod {p}")
    s, t = 0, p - 1
    while t % power == 0:
        s, t = s + 1, t // power
    u = pow(power, -1, t)
    x0 = pow(q, u, p)                    # x0^power = q * (q^t)^k
    k = (power * u - 1) // t
    if s == 1:
        x = x0                           # q^t = 1 when s = 1
    else:
        g = 2
        while pow(g, (p - 1) // power, p) == 1:
            g += 1                       # a non-residue: g^t has order power^s
        c = pow(g, t, p)
        a = pow(q, t, p)                 # in <c>; a power-th power there
        omega = pow(c, power ** (s - 1), p)
        table = {pow(omega, i, p): i for i in range(power)}
        m, cinv = 0, pow(c, -1, p)
        for i in range(s):               # a = c^m, digit i of m in base power
            w = pow(a * pow(cinv, m, p) % p, power ** (s - 1 - i), p)
            m += table[w] * power ** i
        if m % power:
            raise ArithmeticError("root: logarithm not divisible by the power")
        h = pow(c, m // power, p)        # h^power = a = q^t
        x = x0 * pow(h, -k, p) % p
    if pow(x, power, p) != q:
        raise ArithmeticError(f"root: {x}^{power} != {q} mod {p}")
    return x


def lucas_certificate(p):
    """A primality certificate for p a calculator can check: the complete
    factorization of p - 1 and a g with g^(p-1) == 1 and g^((p-1)/r) != 1
    for every prime r of it (Lucas 1876).  The prime factors are below 2^63
    and proved by huntlib's deterministic Miller-Rabin."""
    from sympy import factorint
    p = int(p)
    fac = {int(r): int(e) for r, e in factorint(p - 1).items()}
    # A prime has a primitive root, so for a prime p the search ends, and
    # early (no least primitive root above a few hundred is known at this
    # size); it is not cut at a bound, because a bounded search that fails
    # says nothing.  For a composite p no g passes and the loop is finite.
    for g in range(2, p):
        if pow(g, p - 1, p) == 1 and all(pow(g, (p - 1) // r, p) != 1
                                         for r in fac):
            return {"p_minus_1": {str(r): e for r, e in sorted(fac.items())},
                    "primitive_root": g}
    raise ArithmeticError(f"{p} has no primitive root: it is not prime")


def check_lucas(p, cert):
    """True iff `cert` proves p prime."""
    p = int(p)
    fac = {int(r): int(e) for r, e in cert["p_minus_1"].items()}
    prod = 1
    for r, e in fac.items():
        if not hprimes.mr_is_prime(r):
            return False
        prod *= r ** e
    g = int(cert["primitive_root"])
    return (prod == p - 1 and pow(g, p - 1, p) == 1
            and all(pow(g, (p - 1) // r, p) != 1 for r in fac))


def witnesses(p, power, n):
    """What makes "a(n) = p" checkable by hand: a root for each of the first
    `run` primes, and for the first prime that is NOT a residue the value
    w = q^((p-1)/power) mod p, which is not 1 (and has w^power == 1)."""
    p, power = int(p), int(power)
    r = run_of(p, power)
    if r < n:
        raise ValueError(f"run of {p} is {r} < {n}")
    roots = {str(q): root(q, p, power) for q in PRIMES[:r]}
    q = PRIMES[r]
    w = pow(q, (p - 1) // power, p)
    return {"run": r, "roots": roots,
            "stopper": {"i": r + 1, "prime": q, "symbol": w,
                        "note": (f"{q}^((p-1)/{power}) mod p; not 1, so {q} "
                                 f"is not a residue")}}


def check_witnesses(p, power, wit):
    p, power = int(p), int(power)
    r = int(wit["run"])
    if sorted(int(q) for q in wit["roots"]) != PRIMES[:r]:
        return False
    if any(pow(int(x), power, p) != int(q) % p
           for q, x in wit["roots"].items()):
        return False
    st = wit["stopper"]
    w = pow(int(st["prime"]), (p - 1) // power, p)
    return (int(st["prime"]) == PRIMES[r] and w == int(st["symbol"])
            and w != 1 and pow(w, power, p) == 1)


# ---------------------------------------------------------------- the gates
def _ref():
    import residue_reference as ref
    return ref


def gate_s1():
    """The stream equals the oracle on windows both can run: every prime of
    the class below 400,000, its run by the definition's criterion."""
    ref = _ref()
    from sympy import primerange
    n = 0
    for power in POWERS:
        count = 400_000 // (2 * power)
        got = sweep(power, 1, count, floor=1)
        want = []
        for p in primerange(3, value(power, count) + 1):
            if p % power == 1 and p <= value(power, count):
                r = ref.run(p, power)
                if r >= 1:
                    want.append((p, r))
        if got != want:
            return False, f"S1 power {power}: stream differs from the oracle"
        n += len(got)
    return True, (f"S1 stream = oracle: {n} (p, run) pairs with run >= 1 over "
                  f"every candidate below 400,000 of the five lines, the "
                  f"candidates that are sieve primes themselves included")


def gate_s2():
    """Complete sieve = partial sieve + Miller-Rabin, and split = unsplit."""
    n = 0
    for power in POWERS:
        j0 = 10 ** 9 // (2 * power)
        full = sweep(power, j0, 60_000, floor=1)
        part = sweep(power, j0, 60_000, floor=1, bound=1000)
        halves = (sweep(power, j0, 23_456, floor=1)
                  + sweep(power, j0 + 23_456, 60_000 - 23_456, floor=1))
        if not (full == part == halves) or not full:
            return False, f"S2 power {power}: routes disagree"
        n += len(full)
    return True, (f"S2 routes agree at p = 10^9: the complete sieve, a sieve "
                  f"to 1000 with Miller-Rabin, and a window split in two "
                  f"give the same {n} pairs")


def gate_s3():
    """The published terms come out of the stream end to end, each the first
    of its run in the window that holds it."""
    ref = _ref()
    n = 0
    for seq, fam in ref.FAMILIES.items():
        power = fam["power"]
        for i, p in enumerate(fam["known"]):
            j = index_of(power, p)
            got = dict(sweep(power, max(1, j - 3000), 6001, floor=i + 1))
            if p not in got or got[p] < i + 1:
                return False, f"S3 {seq}: a({i + 1}) = {p} not in the stream"
            if any(pp < p for pp in got):
                return False, f"S3 {seq}: a prime of run >= {i + 1} below a({i + 1})"
            n += 1
    return True, (f"S3 known terms end to end: all {n} published terms are "
                  f"in the stream of a window of 6001 candidates around them, "
                  f"at their index as floor, with nothing before them in it")


def gate_s4():
    """Roots and certificates: every published term's witnesses check, a
    bent root or symbol is refused, and the root routine is right where
    power^2 divides p - 1 (the digit-by-digit branch)."""
    ref = _ref()
    n = deep = 0
    for seq, fam in ref.FAMILIES.items():
        power = fam["power"]
        for i, p in enumerate(fam["known"]):
            wit = witnesses(p, power, i + 1)
            cert = lucas_certificate(p)
            if not (check_witnesses(p, power, wit) and check_lucas(p, cert)):
                return False, f"S4 {seq}: witnesses of a({i + 1}) fail"
            bad = dict(wit, roots=dict(wit["roots"], **{"2": int(wit["roots"]["2"]) + 1}))
            bad2 = dict(wit, stopper=dict(wit["stopper"], symbol=1))
            bad3 = dict(cert, primitive_root=1)
            if check_witnesses(p, power, bad) or check_witnesses(p, power, bad2) \
                    or check_lucas(p, bad3):
                return False, f"S4 {seq}: a bent witness was accepted"
            n += 1
        # primes with power^2 | p - 1 and power^3 | p - 1
        for mult in (power ** 2, power ** 3):
            j, found = 1, 0
            while found < 20:
                p = 2 * mult * j + 1
                j += 1
                if not hprimes.mr_is_prime(p):
                    continue
                for q in PRIMES[:12]:
                    if q % p and pow(q, (p - 1) // power, p) == 1:
                        if pow(root(q, p, power), power, p) != q % p:
                            return False, f"S4 root wrong at q = {q}, p = {p}"
                        deep += 1
                found += 1
    return True, (f"S4 witnesses: a root for each leading prime, the symbol "
                  f"of the first non-residue and a Lucas certificate check "
                  f"for all {n} published terms; a bent root, a symbol of 1 "
                  f"and a false primitive root are refused; {deep} roots "
                  f"taken where the square or cube of the power divides p - 1")


def gate_s5():
    """The ceiling is enforced, and a window against it is populated."""
    try:
        sweep(5, P_CEIL // 10, 10)
        return False, "S5 a window above 2^63 was swept"
    except ValueError:
        pass
    n = 0
    for power in POWERS:
        top = (P_CEIL - 2) // (2 * power)
        got = sweep(power, top - 20_000 + 1, 20_000, floor=1)
        if not got or got[-1][0] >= P_CEIL:
            return False, f"S5 power {power}: empty window at the ceiling"
        n += len(got)
    return True, (f"S5 ceiling: a window above p = 2^63 is refused; the last "
                  f"20,000 candidates below it hold {n} pairs with run >= 1 "
                  f"over the five lines (sieve to 2^22, then Miller-Rabin)")


GATES = [gate_s1, gate_s2, gate_s3, gate_s4, gate_s5]


def selftest():
    ok = True
    for g in GATES:
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg, flush=True)
        ok = ok and good
    return ok


if __name__ == "__main__":
    from huntlib import shutdown
    sys.exit(shutdown.graceful(lambda: 0 if selftest() else 1))
