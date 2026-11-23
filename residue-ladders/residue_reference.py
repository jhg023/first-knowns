# residue_reference.py -- THE ORACLE for the power-residue ladders.
#
#   A002226  Smallest prime p such that first n primes (p_1=2, ..., p_n) are
#            quintic residues mod p.
#   A002227  ... are 7th power residues mod p.
#   A002228  ... are 11th power residues mod p.
#   A060363  ... are 13th power residues mod p.
#   A060364  ... are 17th power residues mod p.
#
# Slow and boring on purpose (CONVENTIONS.md): sympy for primality, plain
# Python integers and sets for everything else, no optimization, and never a
# call into the engines.  It holds the frozen tables of published terms.
#
# THE CONVENTION THE ENTRIES LEAVE UNSAID.  When p - 1 is not a multiple of
# the power, EVERY nonzero residue mod p is such a power (x -> x^5 permutes
# the nonzero residues mod 7), so read literally the entries would begin
# a(n) = 3 or 7.  They begin 151, 631, 331, 4421, 1429: the tables (Western
# and Miller 1968) are over the primes p with p - 1 divisible by the power,
# where exactly one residue in that many is a power.  A002225, the cubic
# sibling, says so in a comment.  Gate G0 pins this reading to the published
# first terms.
#
# The RUN of a prime p (p - 1 divisible by the power) is the number of
# leading primes 2, 3, 5, ... that are residues mod p; a(n) is the least p
# of run >= n.  A prime that divides p's modulus -- the prime p itself, met
# among 2, 3, 5, ... only when p is tiny -- is 0 mod p and ends the run.

import sys

from sympy import isprime, primerange

# the primes a run is read against (40 of them: a run of 40 is far beyond
# anything a sweep below 2^63 can meet)
PRIMES = list(primerange(2, 174))
assert len(PRIMES) == 40

# sequence -> the power, the word the %N line uses for it, the published
# terms a(1), a(2), ... (OEIS data, export of 2026-11-21) and their sources
FAMILIES = {
    "A002226": {
        "power": 5, "residues": "quintic residues",
        "known": [151, 431, 6581, 67651, 241981, 2081921, 3395921,
                  116900011, 650086271, 858613901, 11736494711, 50888057851,
                  303855349271, 2459339487751, 3167880361091],
        "source": "Western & Miller 1968; Reble 2001; a(13)-a(15) "
                  "Paramonov, Apr 2024"},
    "A002227": {
        "power": 7, "residues": "7th power residues",
        "known": [631, 5531, 72661, 865957, 2375059, 32353609, 175175603,
                  945552637, 945552637, 54144188771, 688203780167,
                  2701344818803],
        "source": "Western & Miller 1968; Reble 2001; a(11)-a(12) "
                  "Paramonov, Apr 2024, who adds a(13) > 2^42"},
    "A002228": {
        "power": 11, "residues": "11th power residues",
        "known": [331, 39139, 253243, 4397207, 21587171, 781712537,
                  781712537, 25467966877, 1304374210679, 4331892405391],
        "source": "Western & Miller 1968; Reble 2001; a(9)-a(10) "
                  "Paramonov, Apr 2024"},
    "A060363": {
        "power": 13, "residues": "13th power residues",
        "known": [4421, 44851, 1194961, 2367691, 138609979, 820015717,
                  72942989237, 72942989237],
        "source": "Reble 2001 (no more terms through 10^11)"},
    "A060364": {
        "power": 17, "residues": "17th power residues",
        "known": [1429, 6563, 1458601, 55981069, 250844317, 4926746609,
                  225578509837, 1118584849397, 4143277702703],
        "source": "Reble 2001; a(7)-a(9) Paramonov, Apr 2024"},
}
# bounds the entries themselves state on the first open term
SEARCHED_ABOVE = {"A002227": 2 ** 42, "A060363": 10 ** 11}

SCRATCH_LIMIT = 25_000_000      # G2 rebuilds every term below this


def forms(seq):
    """The condition in the entry's own letters (%N line), for evidence."""
    return (f"first n primes (p_1=2, ..., p_n) are "
            f"{FAMILIES[seq]['residues']} mod p")


def power_residues(p, power):
    """THE DEFINITION: the set of power-th powers of 1..p-1 mod p."""
    return {pow(x, power, p) for x in range(1, p)}


def run_by_definition(p, power):
    """Leading primes that ARE power-th powers mod p, by listing the powers."""
    res = power_residues(p, power)
    r = 0
    for q in PRIMES:
        if q % p not in res:        # 0 is never in res: it ends the run
            break
        r += 1
    return r


def is_residue(q, p, power):
    """Euler's criterion for a prime p with power | p - 1: q, not a multiple
    of p, is a power-th power mod p iff q^((p-1)/power) == 1 (mod p).  The
    nonzero residues are a cyclic group of order p - 1, and the powers are
    its subgroup of index `power`, which is the kernel of that map.  Gate G1
    checks it against the definition on every small prime."""
    if q % p == 0:
        return False
    return pow(q, (p - 1) // power, p) == 1


def run(p, power):
    """The run of the prime p (p - 1 divisible by the power)."""
    r = 0
    for q in PRIMES:
        if not is_residue(q, p, power):
            break
        r += 1
    return r


def first_occurrences(limit):
    """{sequence: [a(1), a(2), ...]} for every term below `limit`, from
    scratch: every prime in order, its run, the first prime of each run."""
    out = {seq: [] for seq in FAMILIES}
    for p in primerange(2, limit):
        for seq, fam in FAMILIES.items():
            if p % fam["power"] != 1:
                continue
            r = run(p, fam["power"])
            while len(out[seq]) < r:
                out[seq].append(p)
    return out


# ---------------------------------------------------------------- the gates
def gate_g0():
    """The reading: a(1) is the least prime p with power | p - 1 of which 2
    is a residue; without that restriction the least prime would be 3."""
    for seq, fam in FAMILIES.items():
        d = fam["power"]
        least = next(p for p in primerange(3, 10 ** 5)
                     if p % d == 1 and run_by_definition(p, d) >= 1)
        if least != fam["known"][0]:
            return False, f"G0 {seq}: least prime is {least}, table has a(1) = {fam['known'][0]}"
        if len(power_residues(3, d)) != 2 or len(power_residues(7, d)) != 6:
            return False, f"G0 {seq}: powers do not permute the residues mod 3, 7"
    return True, ("G0 reading: in all five entries a(1) is the least prime p "
                  "with p - 1 divisible by the power and 2 a residue (151, "
                  "631, 331, 4421, 1429); every nonzero residue mod 3 and mod "
                  "7 is such a power, so the unrestricted reading would start "
                  "at 3")


def gate_g1():
    """Euler's criterion equals the definition on every prime below 3000
    with power | p - 1, for all 40 primes q and all five powers."""
    n = 0
    for seq, fam in FAMILIES.items():
        d = fam["power"]
        for p in primerange(3, 3000):
            if p % d != 1:
                continue
            res = power_residues(p, d)
            if len(res) != (p - 1) // d:
                return False, f"G1 {seq}: {len(res)} powers mod {p}"
            for q in PRIMES:
                if is_residue(q, p, d) != (q % p in res):
                    return False, f"G1 {seq}: criterion != definition at q = {q}, p = {p}"
                n += 1
            if run(p, d) != run_by_definition(p, d):
                return False, f"G1 {seq}: run differs at p = {p}"
    return True, (f"G1 Euler's criterion equals the listed set of powers on "
                  f"{n} (q, p) pairs: every prime p < 3000 with p - 1 "
                  f"divisible by the power, 40 primes q, five powers; exactly "
                  f"(p - 1)/power residues are powers")


def gate_g2():
    """Every published term below SCRATCH_LIMIT is rebuilt from scratch."""
    got = first_occurrences(SCRATCH_LIMIT)
    bits, total, beyond = [], 0, 0
    for seq, fam in FAMILIES.items():
        reach = [t for t in fam["known"] if t < SCRATCH_LIMIT]
        if got[seq] != reach:
            return False, f"G2 {seq}: rebuilt {got[seq]}, table has {reach}"
        bits.append(f"{seq} a(1)..a({len(reach)})")
        total += len(reach)
        beyond += len(fam["known"]) - len(reach)
    return True, (f"G2 from scratch below {SCRATCH_LIMIT:.1e}: {total} "
                  f"published terms rebuilt exactly ({'; '.join(bits)}); the "
                  f"other {beyond} lie above the oracle's reach and are "
                  f"pinned by G3 and by the engines' canaries")


def gate_g3():
    """Every published term is a prime of its class with run >= n, and its
    run is EXACTLY n whenever the next term is larger (else the next term
    would not be larger)."""
    n_terms = 0
    for seq, fam in FAMILIES.items():
        d, known = fam["power"], fam["known"]
        for i, p in enumerate(known):
            n = i + 1
            r = run(p, d)
            if not (isprime(p) and p % d == 1 and r >= n):
                return False, f"G3 {seq}: a({n}) = {p} fails (run {r})"
            if i + 1 < len(known):
                strict = known[i + 1] > p
                if strict != (r == n):
                    return False, f"G3 {seq}: a({n}) = {p} has run {r} against a({n + 1}) = {known[i + 1]}"
            elif r != n:
                return False, f"G3 {seq}: the last term a({n}) has run {r}: a({n + 1}) would be free"
            n_terms += 1
        if known != sorted(known):
            return False, f"G3 {seq}: table not monotone"
    return True, (f"G3 all {n_terms} published terms: prime, p - 1 divisible "
                  f"by the power, run >= n, run exactly n wherever the next "
                  f"term is larger; no table ends on a term that already "
                  f"settles the next index")


GATES = [gate_g0, gate_g1, gate_g2, gate_g3]


def selftest():
    ok = True
    for g in GATES:
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg, flush=True)
        ok = ok and good
    return ok


if __name__ == "__main__":
    sys.path.insert(0, __import__("pathlib").Path(__file__).resolve()
                    .parents[1].as_posix())
    from huntlib import shutdown
    sys.exit(shutdown.graceful(lambda: 0 if selftest() else 1))
