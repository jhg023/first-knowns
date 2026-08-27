"""shiftladder_gpu.py -- the GPU engine for A130003 and A110096.

The same mathematics a third time, on the device, and never trusted alone:
G9 pins its survivor stream bit-for-bit against the CPU engine on populated
windows at several heights, including above 2^64.

    A(b, n) = least m with m + b^k prime for k = 1..n

WHAT THE KERNEL DOES.  A candidate is killed by a prime q exactly when
m mod q lands in K(q,n,b) = { -b^k mod q }, so the engine never forms a
value.  It generates only the m that survive every prime up to the WHEEL and
tests those against the remaining primes by one Barrett reduction and one
bit lookup each, bailing out at the first kill.

  m = j*W + r,   W = prod(q <= p1),   r a wheel residue,   j a period index

THE WHEEL IS TWO MECHANISMS, AND THE SECOND ONE IS v2.  The primes up to p1
are a flat residue table, as in v1.  The primes in (p1, p2] are BIT PLANES
OVER THE PERIOD INDEX, and that is the whole of this engine's advantage:

    q | m  <=>  (j*W + r) mod q in K(q)
            <=>  (j + Binv_q * r) mod q  in  Binv_q * K(q)  =: K'(q)

with Binv_q = W^-1 mod q, which exists because q > p1 does not divide W.
Read the right-hand side again: once r is fixed it is a condition on j
ALONE, and it is periodic in j with period q.  So a group g of primes above
the wheel has a fixed surviving-j set S_g mod Q_g = prod(g), stored as a bit
plane, and ONE 32-bit load plus ONE and filters THIRTY-TWO consecutive
periods.  That is OPTIMIZATION.md 2.1 -- tabulate the periodic quantity the
inner loop recomputes and process a block per step -- applied to the WHEEL
rather than to the sieve, and it is why this project can afford a wheel to
79 or 113 where a residue table dies at 23.

Two things make it fit this problem rather than the general one:

  * The shift is additive.  A multiplicative ladder's kill condition is not
    a translate of a fixed set, so no single plane serves every residue;
    here `cr` (one u32 per residue per group) is the whole per-residue
    state, and the launch base folds into one more scalar per group.
  * W IS UNCHANGED.  The plane primes never enter the modulus, so `sweep(j0,
    j1)` still means [j0*W, j1*W), coverage still advances every launch, the
    checkpoint's period unit is the same one v1 stored, and the frozen
    benchmark windows are the same windows.  A factored wheel of the kind
    square-ladders uses would have multiplied W by 2.8e9 and made the
    coverage claim advance in steps ten times wider than the whole hunt.

THE TEST LOOP IS COMPACTED, TWICE OVER (OPTIMIZATION.md 2.2).  A lane needs
about three tests but a warp of 32 runs to the deepest of them -- measured
on v1, 13.96 against a mean of 2.78, a 5.0x tax.  So the kernel runs slices
of the test primes BRANCHLESSLY over a dense shared queue and compacts the
survivors between slices, every lane alive.  The slice boundaries are
derived from the SURVIVAL CURVE and not from a prime count: a coarser wheel
or a smaller filter kills faster, and a fixed depth there tests past the
point where anything is left to kill.

  * The in-block chain stops at TAIL_SURV, because a block that has whittled
    itself down to a percent of its candidates has more idle warps than
    working ones.
  * What is left goes to a GLOBAL queue and a second kernel sweeps it with
    one item per lane, the whole device in flight -- and that kernel runs a
    compaction chain of its OWN, which is worth having there for exactly the
    reason it was not worth having in the block: its blocks are full.

THE (m, off) CARRY IS HERE FROM THE FIRST COMMIT (OPTIMIZATION.md 2.7).
Nothing on this device ever holds an absolute m: the kernel reduces the
launch OFFSET, and `base mod q` is folded once per launch on the host into
the uint4's `boff` slot against a DOUBLED kill bitmap, so it costs no
instruction in the hot loop.  The enforced ceiling is therefore the
primality-proof bound (3.317e24 minus b^n), not a machine word, and G15
checks that the stream does not depend on where the launch base was put.

Gates here: G7 (the CRT-lifted wheel == the oracle's period walk), G8 (the
wheel is exactly prod(q - w) residues, duplicate-free, none of them killed),
G9 (GPU stream == CPU stream on populated windows, both bases, including
above 2^64), G15 (the stream is invariant under the launch base and the
launch split), G16 (the v2 mechanisms: the bit planes against direct
divisibility, the derived schedules, and the three overflow fallbacks forced
and checked identical).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                       # noqa: E402
from huntlib.gpu import barrett_magics                          # noqa: E402
from shiftladder_reference import K_FLOOR, w                    # noqa: E402
from shiftladder_search import (CpuEngine, Q2_DEFAULT,          # noqa: E402
                                k_ceil, killed_residues, m_floor)

# The flat residue table's top per base.  It sets W and therefore the unit
# of the coverage cursor, so it is a per-base CONSTANT and not something the
# engine tunes: moving it re-denominates every checkpoint and re-freezes
# every benchmark window measured in periods.  The wheel gets deeper through
# the bit planes, which leave W alone.
#
# 29 at b = 4 (raised from 23, measured 1.198x): generation costs `ng` plane
# reads per 32 periods PER RESIDUE, so its cost per unit of m line is R/W --
# the flat table's density -- and halving that halves the dominant phase.
# 29 is the last step available there: p1 = 31 would want 613 million flat
# residues (16 GiB of tables), because a prime buys density (q - w)/q and
# costs (q - w) TIMES the residue count, and ord_31(4) = 5 makes 31 nearly
# all cost.
#
# 41 at b = 2 (raised from 37 on 2026-08-27, measured 1.398x).  The old
# comment here said b = 2 was at its top too, on a residue count taken at
# n = 17 (129 million).  IT IS AN n-DEPENDENT NUMBER and the campaign has
# moved: w(41,n,2) = min(n, 20), so at the n = 19 the hunt now runs, 41
# keeps 22 residues rather than 24 and the wheel is 44.5 million -- and it
# only shrinks from here, because w grows with n and every future filter is
# larger.  R/W falls 2.72e-7 -> 1.46e-7, a 1.864x cut in the dominant
# phase, for 1.5 GiB of device tables.
P1_DEFAULT = {4: 29, 2: 41}

# Barrett reduces the launch offset, which must stay a u64 and under 2^63
# for ONE conditional subtraction to be exact (see TEST in the kernel).
# That bounds nper * W, a property of the WHEEL AND THE BATCHING, both of
# which the engine picks -- never of m, which the mathematics picks.
REDUCE_MAX = 1 << 63

# The flat table's own ceiling.  "Which primes fit in the flat wheel" is a
# MEMORY question and it is answered by refusing, not by an allocation that
# fails 183 GiB in: the b = 2 wheel reaches 1.29e9 residues at p1 = 47.  The
# bit planes are what raise the wheel now, so this bound stops mattering to
# throughput and stays only as a guard.
# 2^26 since 2026-08-27, to admit the b = 2 wheel at p1 = 41 (44.5M
# residues at n >= 19).  It still refuses that family's n = 17 wheel
# (129M) and p1 = 47 (36 billion), which is what the guard is for.
RES_MAX = 1 << 26                # 67.1M residues = 537 MB as int64
HIT_CAP = 1 << 16                # survivors buffered per launch

# --------------------------- the bit-plane wheel ---------------------------
# Bits in one plane before a new group is started.  Bigger planes mean FEWER
# groups and so fewer loads per period, which is the thing the generation
# phase is paid in; the counterweight is cache.  Swept interleaved on both
# production shapes: 2^26 beat 2^20 / 2^22 / 2^24, because at 2^26 the b = 4
# wheel's first five primes (29..43, 5.9e7 residues) merge into ONE plane.
# RAISED 2^26 -> 2^28 (2026-08-27).  The old sweep stopped at its own
# default and never looked ABOVE it.  At a FIXED p2 = 103 the budget is
# worth 1.311x / 1.202x = 1.09x on the b = 4 resume shape -- 2^28 packs
# (29, 103] into 4 groups where 2^26 needs 5, and the group it saves costs
# more than the 27.6 MiB of L2 it spends.  The counterweight is real but it
# is further out than 2^26: at 2^30 the b = 4 wheel wants 119.5 MiB and the
# planes stop being L2-resident.
PLANE_BITS_MAX = 1 << 28
# All planes together.  A guard, not a tuning constant: p2 is derived and a
# pathological argument should refuse rather than allocate.
PLANE_TOTAL_MAX = 1 << 31        # 256 MB of planes
P2_SEARCH_MAX = 400              # how far pick_p2 looks

# ------------------------------ the kernel ---------------------------------
TPB_DEFAULT = 128
WPT_DEFAULT = 8                  # 32-bit plane words per thread
# TPB * WPT is the block's WORK ITEMS, and 1024 of them is the knee: swept
# interleaved over 64..512 threads and 1..32 words, 1.54x-1.64x over 256 on
# three shapes and 1.29x on the fourth.  It is a candidates-per-block knob
# in disguise -- at a deep wheel a narrower block reaches its compaction
# rounds with fewer candidates than it has threads.
# Residues one block may cover.  It bounds nothing but two small shared
# arrays (RPB_MAX * NG words plus RPB_MAX u64), and it has to be at least
# TPB*WPT / (words per residue) or a launch short in PERIODS leaves most of
# the block idle -- which is exactly the shape a deep flat wheel produces,
# because R goes up and per_launch comes down together.
RPB_MAX = 32
UNROLL = 4                       # independent Barrett chains in a tail loop
QCAP_SIGMA = 6.0                 # sigma of headroom on an analytic queue
ROUND_RATIO = 0.65               # survival drop that ends a compaction round
TAIL_SURV = 0.10                 # where the block hands over to the tail
TAIL2_SURV = 0.01                # where the tail kernel stops compacting
MAX_ROUNDS = 10
TTILE_MUL = 4                    # tail-kernel shared tile, in blocks of TPB
TAIL_BLOCKS_PER_SM = 64
# CRT-combined test units: "killed by 79 or by 83" is a function of
# m mod (79*83) alone, so a unit costs ONE reduction and ONE lookup instead
# of one of each per prime.  Measured near-null here (see OPTIMIZATION_LOG),
# and the cap is small deliberately -- the wide settings hit the L1 cliff.
# RE-SWEPT 2026-08-27 after p2 moved (OPTIMIZATION.md 3.4): the unit list
# starts at p2, so a deeper wheel top is a different unit list and the old
# optimum was measured against the old one.  2^15 measures 1.115x
# [1.051, 1.185] over 2^13 on the b = 4 resume shape and 1.04x [0.97, 1.04]
# on b = 2 -- at 2^15 the first units become PAIRS instead of singletons.
# 2^18 is still the L1 cliff (1.018x), so the cap moved two steps, not off.
UNIT_Q_MAX = 1 << 15
# j-slots (R * periods) aimed at per launch.  This is the invariant, and it
# is what per_launch is derived FROM: R and per_launch move in opposite
# directions as p1 changes, and it is their product that sets the work in a
# launch, the tail queue's occupancy and the coverage step.  2^35 is where
# the b = 4 wheel already sat before p1 moved (its old per_launch floor of
# one block tile happened to land there); measured flat from 2^34 to 2^35.
# RAISED 2^35 -> 2^37 on 2026-08-27, and demoted to a GUARD: the binding
# constraint on launch size is the TAIL QUEUE, and _pick_launch now derives
# against it directly (see there).  2^35 was itself a launch cap in
# disguise -- it held b = 4 at 1024 periods when the queue could take 4096.
CAND_SLOTS = 1 << 37
# Global tail queue ceiling, and the one constant here that the FROZEN
# BENCHMARK CANNOT SEE (OPTIMIZATION.md 2.13).  The queue is sized from
# per_launch, and SCORE's window is 8,192 periods -- a QUARTER of one
# production launch -- so on the benchmark the queue never fills and every
# capacity from 2^23 up measures identical.  Swept on a multi-launch span
# instead, at the launch size a campaign actually runs: 2^23 overflows 79%
# of the tail into the in-block fallback and costs 1.19x, and the ceiling
# has to clear the analytic need (3.2e7 entries at the b = 4 production
# wheel) or the campaign quietly runs at two thirds of its rate while the
# score says nothing is wrong.
Q3_MAX = 1 << 26                 # 537 MB, and see _pick_q3cap

# What the pieces cost, in units of ONE PACKED TEST (measured: 1.054 ps per
# candidate-test on SCORE, against 2.184 ps for v1's spelling of the same
# test).  They exist so the bit-plane wheel's top can be DERIVED per
# configuration rather than pinned per base: the measured optimum moved from
# 47 to 113 across the five benchmark shapes, and shipping a constant would
# be the "carry the fraction, not the count" mistake in another spelling.
# RE-MEASURED 2026-08-27: 3.8 -> 0.95, and this one constant was holding
# the wheel top four primes short on b = 4 and six on b = 2.  GEN_W is what
# pick_p2 trades a plane group AGAINST, so overpricing a plane read by 4x
# stops the wheel early; the fitted value comes from 15 measured (p2, rate)
# pairs across both production shapes (least squares in log rate), and it
# moves the DERIVED pick from 79 -> 103 at b = 4 and 89 -> 137 at b = 2,
# both of which land inside their own measured plateau.  Worth 1.288x and
# ~1.33x on the resume shapes.  Checked against a third, very different
# configuration (n = 10, p1 = 13) so the fit is not two shapes wide: p2 is
# flat 101..167 there and the new pick costs 0.991x.
GEN_W = 0.95                     # one plane read, per 32 periods
EXTRACT = 1.4                    # ffs + queue push, per candidate
ROUNDC = 1.4                     # dequeue + rebuild + push, per round

_WHEELS = {}
_MODULES = {}


def wheel(n, b, p1):
    """(W, residues): every m mod W surviving the primes q <= p1.

    Built by CRT lifting -- start from the empty product and, at each new
    prime, keep the q - w(q,n,b) lifts of every surviving residue that q
    does not kill.  The oracle builds the same set by walking the whole
    period; G7 pins the two together on small p1, which is the only place
    the walk is affordable.

    BOTH ceilings are computed before a single residue is built: the modulus
    and the residue count are plain products, so a wheel that would not fit
    is refused here rather than part way through an allocation.  (It was the
    other way round for one commit, and the b = 2 wheel at p1 = 47 asked
    numpy for 183 GiB.)

    CACHED ON THE EFFECTIVE `w` VECTOR, NOT ON `n`.  The wheel depends on
    the filter only through w(q,n,b) = min(n, ord_q(b)), so once n passes
    every ord below p1 the table stops changing: at b = 4, p1 = 29 the
    largest is ord_29(4) = 14, and `wheel(n, 4, 29)` is byte-identical for
    EVERY n >= 14.  A cache keyed on n rebuilds 23.6 million residues from
    scratch every time a find advances the filter, for a table it already
    holds.  b = 2 at p1 = 41 genuinely changes until n >= 36, because
    ord_37(2) = 36 -- which is the reason to key on the vector rather than
    to special-case a base.  G8 pins both halves.
    """
    qs = list(primerange(2, p1 + 1))
    key = (b, p1, tuple(w(q, n, b) for q in qs))
    if key in _WHEELS:
        return _WHEELS[key]
    W_final, R_final = 1, 1
    for q in qs:
        W_final *= q
        R_final *= q - w(q, n, b)
    if W_final >= REDUCE_MAX:
        raise ValueError(f"wheel modulus {W_final} passes the Barrett bound "
                         f"{REDUCE_MAX}: pick a smaller p1")
    if R_final > RES_MAX:
        raise ValueError(f"a flat wheel at p1 = {p1} would hold {R_final} "
                         f"residues, past RES_MAX = {RES_MAX}: raise the "
                         f"wheel with bit planes (p2), not with a bigger "
                         f"allocation")
    W, res = 1, np.zeros(1, dtype=np.int64)
    for q in qs:
        killed = np.array(sorted(killed_residues(q, n, b)), dtype=np.int64)
        ginv = pow(W, -1, q)              # W is squarefree, so this exists
        # r + W*t is killed exactly when t == (u - r) * W^-1 (mod q)
        bad = ((killed[None, :] - (res % q)[:, None]) * ginv) % q
        keep = np.ones((res.size, q), dtype=bool)
        keep[np.arange(res.size)[:, None], bad] = False
        res = (res[:, None] + np.arange(q, dtype=np.int64) * W)[keep]
        W *= q
    res.sort()
    _WHEELS[key] = (W, res)
    return W, res


def wheel_modulus(b, p1=None):
    """W for a base, without building the residue table.

    DERIVE THE CONFIGURATION IN EXACTLY ONE PLACE (OPTIMIZATION.md 2.9): the
    launcher needs W before it has an engine -- to re-denominate an adopted
    cursor, and to assert the unit of one it keeps -- and a second, private
    computation of the same quantity is a disagreement waiting for its
    second implementation to exist.  That is the exact shape of the bug 2.9
    is written about.
    """
    W = 1
    for q in primerange(2, (p1 or P1_DEFAULT[b]) + 1):
        W *= q
    return W


def plane_groups(p1, p2, budget=PLANE_BITS_MAX):
    """Partition the primes in (p1, p2] into bit-plane groups.

    Greedy, in order, growing a group while its product stays under
    `budget`.  The product is the plane's period in bits, so the budget is
    what keeps a plane cache-resident.
    """
    out, cur, prod = [], [], 1
    for q in primerange(p1 + 1, p2 + 1):
        if cur and prod * q > budget:
            out.append((tuple(cur), prod))
            cur, prod = [], 1
        cur.append(q)
        prod *= q
    if cur:
        out.append((tuple(cur), prod))
    return out


def build_planes(n, b, p1, p2, ypad, budget=PLANE_BITS_MAX):
    """The packed surviving-j bit planes for the primes in (p1, p2].

    Plane g holds bit z set when `z mod q not in Binv_q * K(q)` for every q
    in the group -- i.e. when a period index congruent to z survives the
    whole group.  It is stored with `ypad + 128` bits of its own head copied
    onto the end, so a read that starts anywhere in [0, Q) and runs a whole
    block's worth of periods further never wraps and never needs a modulo.
    """
    W = 1
    for q in primerange(2, p1 + 1):
        W *= q
    planes = []
    for prs, Q in plane_groups(p1, p2, budget):
        alive = np.ones(Q, dtype=bool)
        for q in prs:
            binv = pow(W % q, -1, q)
            for u in killed_residues(q, n, b):
                alive[(binv * u) % q::q] = False
        nbits = (Q + ypad + 128 + 63) // 64 * 64
        rep = np.resize(alive, nbits)               # periodic head copy
        planes.append({"primes": prs, "Q": Q,
                       "words": np.packbits(rep,
                                            bitorder="little").view(np.uint32),
                       "density": float(alive.mean())})
    total = sum(int(p["words"].size) * 32 for p in planes)
    if total > PLANE_TOTAL_MAX or total >= (1 << 32):
        raise ValueError(f"the bit planes for (p1, p2] = ({p1}, {p2}] would "
                         f"hold {total} bits, past PLANE_TOTAL_MAX = "
                         f"{PLANE_TOTAL_MAX} or the u32 index the kernel "
                         f"uses: lower p2")
    return planes


def plane_shifts(res, planes, W):
    """cr[g][i] = CRT_g(Binv_q * res[i] mod q), one u32 per residue.

    The whole per-residue state of the bit-plane wheel.  A candidate's plane
    index is `(cbase_g + cr_g[i] + j_local) mod Q_g`, and CRT is a ring
    isomorphism, so the launch base contributes one more scalar per group
    and never a per-candidate operation.

    THE ENGINE NO LONGER UPLOADS THIS.  It is the HOST-SIDE REFERENCE the
    kernel's computed form is gated against: the CRT reconstruction below
    is exactly `(W^-1 mod Q_g) * r mod Q_g`, because W^-1 mod Q_g reduces
    to W^-1 mod q at every q in the group.  Kept slow and explicit for that
    reason -- G16 compares it, residue for residue, with the constant and
    the expression the kernel is generated with.
    """
    out = []
    for g in planes:
        Q = g["Q"]
        acc = np.zeros(res.size, dtype=np.int64)
        for q in g["primes"]:
            binv = pow(W % q, -1, q)
            M = Q // q
            # M * (M^-1 mod q) mod Q is the CRT basis vector for this prime;
            # folding it here turns two passes over the residue table into
            # one, which matters at 23.6 million of them
            cq = (M * pow(M, -1, q)) % Q
            acc += (res % q) * binv % q * cq % Q
        out.append((acc % Q).astype(np.uint32))
    return out


def test_units(p2, q2, qmax=UNIT_Q_MAX):
    """CRT-combine the test primes into units of bounded modulus.

    A unit's kill pattern is a function of m mod Q = prod(unit), so one
    reduction and one lookup decide the whole unit.  The primes stay in
    order, so the survival curve -- and the round schedule cut from it --
    change only in granularity.
    """
    out, cur, prod = [], [], 1
    for q in primerange(p2 + 1, q2 + 1):
        if cur and prod * q > qmax:
            out.append((tuple(cur), prod))
            cur, prod = [], 1
        cur.append(q)
        prod *= q
    if cur:
        out.append((tuple(cur), prod))
    return out


def survival(n, b, units):
    """S[i] = the fraction of wheel survivors still alive after i units."""
    S, cur = [1.0], 1.0
    for prs, _Q in units:
        for q in prs:
            cur *= 1.0 - w(q, n, b) / q
        S.append(cur)
    return S


def schedule(S, npr, ratio, tail, start=0):
    """Round boundaries in the unit list, cut from the survival CURVE.

    A round ends when survival has fallen by `ratio`; the chain stops when
    survival reaches `tail`.  Boundaries are FRACTIONS made into counts per
    configuration, never counts carried between configurations.
    """
    b = [int(start)]
    while len(b) <= MAX_ROUNDS and b[-1] < npr and S[b[-1]] > tail:
        want = S[b[-1]] * ratio
        d = b[-1] + 1
        while d < npr and S[d] > want:
            d += 1
        b.append(min(d, npr))
    return b


def model_cost(n, b, p1, p2, q2, budget=PLANE_BITS_MAX, ratio=ROUND_RATIO,
               tail=TAIL_SURV, qmax=UNIT_Q_MAX):
    """Modelled cost per unit of m line, in tests, for a wheel top of p2.

    Generation is `ng` plane reads per 32 periods; everything else is per
    CANDIDATE, and the round chain is priced off the survival curve exactly.
    Rule 2: this generates the candidate and prices what is declined.  It is
    never the evidence -- the value it picks is checked by a sweep around it,
    and the measured curve is flat over a wide plateau either side.
    """
    d2 = 1.0
    for q in primerange(p1 + 1, p2 + 1):
        d2 *= (q - w(q, n, b)) / q
    ng = len(plane_groups(p1, p2, budget))
    units = test_units(p2, q2, qmax)
    S = survival(n, b, units)
    npr = len(units)
    bn = schedule(S, npr, ratio, tail)
    rounds = sum(S[bn[i]] * (bn[i + 1] - bn[i] + ROUNDC)
                 for i in range(len(bn) - 1))
    s0 = S[bn[-1]]
    tl = (sum(1.0 - (1.0 - S[j] / s0) ** 32 for j in range(bn[-1], npr + 1))
          * s0) if s0 > 0 else 0.0
    return ng * GEN_W / 32.0 + d2 * (EXTRACT + rounds + tl)


def pick_p2(n, b, p1, q2, **kw):
    """The bit-plane wheel top that minimises the modelled cost."""
    cands = [q for q in primerange(p1, min(q2, P2_SEARCH_MAX) + 1)] or [p1]
    return min(cands, key=lambda x: model_cost(n, b, p1, x, q2, **kw))


def _qcap(tile, surv, sigma=QCAP_SIGMA):
    """Queue capacity from the ANALYTIC survival plus sigma of margin.

    The count in a block is a sum of `tile` near-independent Bernoullis, so
    its mean and standard deviation are both known exactly
    (OPTIMIZATION.md 2.6).  Sizing for the impossible worst case instead
    would cost shared memory, and shared memory costs blocks per SM -- so
    overflow is made HARMLESS rather than impossible: a candidate that does
    not fit runs its tail on the spot, which is the same arithmetic and so
    the same answer.  Capacity is a tuning constant, not a correctness
    bound, and G16 proves it by forcing the path.
    """
    mean = tile * surv
    sd = (tile * surv * max(1.0 - surv, 0.0)) ** 0.5
    cap = int(mean + sigma * sd) + 32
    return int(min(int(tile), (cap + 31) // 32 * 32))


_SRC = r"""
#define TPB    %(tpb)d
#define WPT    %(wpt)d
#define NG     %(ng)d
#define Q1CAP  %(q1cap)d
#define Q2CAP  %(q2cap)d
#define NROUND %(nround)d
#define W1C    %(w1)dULL
#define UNROLL %(unroll)d
#define RPBMAX %(rpbmax)d
#define TTILE  %(ttile)d
#define TCAP   %(tcap)d
#define TROUND %(tround)d

/* One test against the packed per-unit uint4 (magic_lo, magic_hi, Q, boff).
   The remainder is 32-bit: the true value of off - qhat*Q lies in [0, 2Q)
   and arithmetic mod 2^32 is exact for a value that small.  ONE conditional
   subtraction is enough, and that is a theorem rather than a hope: with
   M = floor(2^64/Q) and x < 2^63,

       x*M/2^64 = x/Q - x*s/(Q*2^64),   s = 2^64 mod Q < Q,

   so the error term is under 1/2, qhat > x/Q - 3/2, and qhat is therefore
   floor(x/Q) or one less.  What is reduced is the launch OFFSET, bounded by
   W * per_launch, so the bound holds at every height and REDUCE_MAX enforces
   it against the wheel instead of against the mathematics.

   The launch base arrives through e.w, which the host set to
   `2Q-block base + (base mod Q)`; the bitmap holds each unit's pattern
   TWICE, so `e.w + r` lands in the right copy and `(off + base) mod Q` is
   read without ever adding the two. */
#define TEST(IDX, DST) { \
    const uint4 e = pk[IDX]; \
    const unsigned long long mg = ((unsigned long long)e.y << 32) | e.x; \
    unsigned int r = (unsigned int)off \
                   - (unsigned int)__umul64hi(off, mg) * e.z; \
    if (r >= e.z) r -= e.z; \
    const unsigned int bb = e.w + r; \
    DST |= (bits[bb >> 5] >> (bb & 31)) & 1u; }

/* The uncompacted remainder: every lane entering this is alive, so the
   early exit costs what it should, and UNROLL independent Barrett chains
   hide the dependent-chain latency. */
__device__ __forceinline__ bool tail_survives(
        const unsigned long long off, const int np_, const int from,
        const uint4* __restrict__ pk, const unsigned int* __restrict__ bits)
{
    int i = from;
    for (; i + UNROLL <= np_; i += UNROLL) {
        unsigned int kill = 0u;
#pragma unroll
        for (int z = 0; z < UNROLL; ++z) TEST(i + z, kill)
        if (kill) return false;
    }
    for (; i < np_; ++i) {
        unsigned int kill = 0u;
        TEST(i, kill)
        if (kill) return false;
    }
    return true;
}

#define EMIT(V) { const int _p = atomicAdd(nout, 1); \
                  if (_p < cap) out[_p] = (V); }

/* THE TAIL DOES NOT RUN IN THE SIEVE BLOCK.  A block reaches the end of its
   round chain with a few percent of its candidates -- a couple of dozen
   against TPB threads -- so most warps sit idle while the block waits on the
   single deepest early-exit chain among the survivors.  So the survivors go
   to a GLOBAL queue and this kernel sweeps it with one item per lane and the
   whole device in flight.  `n3` is read ON THE DEVICE, so the two kernels
   chain with no host round trip, and there is one atomic per BLOCK.

   And it COMPACTS, for the same reason the sieve kernel does: a warp of tail
   items still runs to the deepest chain among its 32.  The difference -- and
   the reason these rounds are worth running HERE and were not worth running
   back in the sieve block -- is that every block in this kernel is full. */
extern "C" __global__ void tailsweep(
        const unsigned long long* __restrict__ q3,
        const int* __restrict__ n3, const int q3cap,
        unsigned long long* out, int* nout, const int cap,
        const int np_, const uint4* __restrict__ pk,
        const unsigned int* __restrict__ bits)
{
    __shared__ unsigned long long ta[TTILE];
    __shared__ unsigned long long tb[TCAP];
    __shared__ int tn[TROUND > 0 ? TROUND : 1];
    const int n = min(*n3, q3cap);
    for (int base = blockIdx.x * TTILE; base < n; base += gridDim.x * TTILE) {
        const int m = min(TTILE, n - base);
        if ((int)threadIdx.x < TROUND) tn[threadIdx.x] = 0;
        for (int i = threadIdx.x; i < m; i += TPB) ta[i] = q3[base + i];
        __syncthreads();
        const int tm1 = m;
%(trounds)s
        __syncthreads();
    }
}

/* The block's tile is (rpb residues) x (wact words of j), chosen by the HOST
   so that TPB*WPT work items always land on real work: a launch with few
   periods spreads a block over more residues instead of masking off three
   quarters of its threads.  Both factors are powers of two, so the
   decomposition is a shift and a mask. */
#define OFF_OF(RL, YL) (r1s[RL] + W1C * (unsigned long long)(ybase + (YL)))

extern "C" __global__ void sieve(
        const unsigned long long* __restrict__ res, const int R,
        const unsigned int* __restrict__ gbits,
        const unsigned int* __restrict__ cbase,   /* NG per-launch shifts */
        const int nper,
        const int rpb, const int logw,
        const int np_,
        const uint4* __restrict__ pk,
        const unsigned int* __restrict__ bits,
        unsigned long long* q3, int* n3, const int q3cap,
        unsigned long long* out, int* nout, const int cap)
{
    __shared__ int q3b;
    __shared__ unsigned short qk[Q1CAP];
    __shared__ unsigned short qk2[Q2CAP];
    __shared__ int qn;
    __shared__ int qcnt[NROUND > 0 ? NROUND : 1];
    __shared__ unsigned int zc[RPBMAX * (NG > 0 ? NG : 1)];
    __shared__ unsigned long long r1s[RPBMAX];
    const int wact = 1 << logw;
    const int ymask = (wact << 5) - 1;
    const int r1base = blockIdx.x * rpb;
    const int nrl = min(rpb, R - r1base);
    const int ybase = blockIdx.y * (wact << 5);
    const int nyb = min(wact << 5, nper - ybase);
    if (threadIdx.x == 0) qn = 0;
    if ((int)threadIdx.x < NROUND) qcnt[threadIdx.x] = 0;
    if ((int)threadIdx.x < nrl) r1s[threadIdx.x] = res[r1base + threadIdx.x];
%(zbcalc)s
    __syncthreads();

    /* ---- generation: NG plane reads filter 32 periods per load ---- */
    unsigned int mine[WPT];
    int cnt = 0;
#pragma unroll
    for (int i = 0; i < WPT; ++i) {
        const int idx = threadIdx.x + i * TPB;
        const int rl = idx >> logw;
        const int wrd = idx & (wact - 1);
        const int y0 = wrd << 5;
        unsigned int mask = 0u;
        if (rl < nrl && y0 < nyb) {
            mask = (y0 + 32 <= nyb) ? 0xFFFFFFFFu
                                    : ((1u << (nyb - y0)) - 1u);
%(gload)s
        }
        mine[i] = mask;
        cnt += __popc(mask);
    }

    /* warp-aggregated queue push: one shared atomic per warp rather than
       one per candidate */
    int scan = cnt;
#pragma unroll
    for (int d = 1; d < 32; d <<= 1) {
        const int v = __shfl_up_sync(0xFFFFFFFFu, scan, d);
        if ((threadIdx.x & 31) >= d) scan += v;
    }
    const int wsum = __shfl_sync(0xFFFFFFFFu, scan, 31);
    int wbase = 0;
    if ((threadIdx.x & 31) == 31) wbase = atomicAdd(&qn, wsum);
    wbase = __shfl_sync(0xFFFFFFFFu, wbase, 31);
    int p = wbase + scan - cnt;
#pragma unroll
    for (int i = 0; i < WPT; ++i) {
        unsigned int mask = mine[i];
        const int idx = threadIdx.x + i * TPB;
        /* key0 == idx << 5.  The key packs (rl, wrd, bit) as
           (rl << (logw+5)) | (wrd << 5) | bit, and wact = 1 << logw, so
           rl and wrd are the disjoint high and low parts of idx and the
           first two terms collapse to ((rl << logw) | wrd) << 5 = idx << 5.
           Four ALU ops become one on a path every thread walks WPT times
           whether or not its word holds a candidate.  The DECODE below --
           `key >> (logw + 5)` and `key & ymask` -- is unchanged and is what
           makes the identity checkable: G16 pins encode against decode. */
        const int key0 = idx << 5;
        while (mask) {
            const int t = __ffs(mask) - 1;
            mask &= mask - 1u;
            const int key = key0 + t;
            if (p < Q1CAP) qk[p] = (unsigned short)key;
            else {
                const unsigned long long off =
                    OFF_OF(key >> (logw + 5), key & ymask);
                if (tail_survives(off, np_, 0, pk, bits)) EMIT(off)
            }
            ++p;
        }
    }
    __syncthreads();
    const int nq1 = min(qn, Q1CAP);

    /* ---- compaction rounds: a slice of the test units run BRANCHLESSLY
            over a dense queue (every lane alive, so the warp pays what a
            lane pays), then the survivors compacted again ---- */
%(rounds)s
}
"""


class GpuEngine:
    """Bit-plane wheel, compacted Barrett test loop, and a tail kernel."""

    def __init__(self, n, b, p1=None, q2=Q2_DEFAULT, per_launch=None,
                 p2=None, tpb=TPB_DEFAULT, wpt=WPT_DEFAULT,
                 plane_bits=PLANE_BITS_MAX, round_ratio=ROUND_RATIO,
                 tail_surv=TAIL_SURV, tail2_surv=TAIL2_SURV,
                 unit_q_max=UNIT_Q_MAX, force_caps=None):
        import cupy as cp
        self.cp = cp
        self.n, self.b, self.q2 = int(n), int(b), int(q2)
        self.p1 = int(p1 if p1 is not None else P1_DEFAULT[b])
        self.tpb, self.wpt = int(tpb), int(wpt)
        self.yblk = self.tpb * 32 * self.wpt
        self.plane_bits = int(plane_bits)
        self.unit_q_max = int(unit_q_max)

        # --- the wheel: flat table to p1, bit planes to p2 ---
        self.W, res = wheel(self.n, self.b, self.p1)
        self.R = int(res.size)
        want_p2 = (int(p2) if p2 is not None
                   else pick_p2(self.n, self.b, self.p1, self.q2,
                                budget=self.plane_bits, ratio=round_ratio,
                                tail=tail_surv, qmax=self.unit_q_max))
        self.p2 = max(self.p1, min(want_p2, self.q2))
        self.planes = build_planes(self.n, self.b, self.p1, self.p2,
                                   self.yblk, self.plane_bits)
        self.ng = len(self.planes)
        self.d2 = 1.0
        for g in self.planes:
            self.d2 *= g["density"]

        # --- the test units and the two round schedules ---
        self.units = test_units(self.p2, self.q2, self.unit_q_max)
        self.npr = len(self.units)
        self._S = survival(self.n, self.b, self.units)
        self.bounds = schedule(self._S, self.npr, round_ratio, tail_surv)
        self.tbounds = schedule(self._S, self.npr, round_ratio, tail2_surv,
                                start=self.bounds[-1])

        # --- device tables ---
        # THE PER-RESIDUE PLANE SHIFT IS NOT A TABLE.  `plane_shifts` builds
        # cr_g(r) = CRT_g(Binv_q * r mod q) one u32 per residue per group --
        # 360 MiB at the b = 4 wheel and 688 MiB at b = 2, half that family's
        # device footprint, streamed from HBM once per launch and costing
        # 8.5 s of every engine rebuild.  It is also exactly LINEAR:
        #
        #     cr_g(r) = (W^-1 mod Q_g) * r  mod  Q_g
        #
        # because W^-1 mod Q_g reduces to W^-1 mod q at every q in the group,
        # which is the CRT reconstruction `plane_shifts` performs.  So the
        # block prologue computes it from `res` -- which it already reads --
        # and one baked constant per group.  `plane_shifts` stays as the
        # host-side reference and G16 pins both the constant and the
        # expression against it, over the whole residue table.
        self.winv = [pow(self.W, -1, g["Q"]) for g in self.planes]
        self.d_res = cp.asarray(res.astype(np.uint64))
        # goff is a BIT offset into the concatenated planes
        self.goff, acc, tot = [], [], 0
        for g in self.planes:
            self.goff.append(tot * 32)
            acc.append(g["words"])
            tot += int(g["words"].size)
        self.d_gbits = (cp.asarray(np.concatenate(acc)) if acc
                        else cp.zeros(1, dtype=cp.uint32))
        self.d_cbase = cp.zeros(max(self.ng, 1), dtype=cp.uint32)

        # packed per-unit constants + the DOUBLED kill bitmap
        Qs = [Q for _p, Q in self.units]
        mag = (barrett_magics(Qs).astype(np.uint64) if Qs
               else np.zeros(0, dtype=np.uint64))
        offs, total = [], 0
        for Q in Qs:
            offs.append(total)
            total += 2 * Q
        bits = np.zeros(max(1, (total + 31) // 32), dtype=np.uint32)
        for t, (prs, Q) in enumerate(self.units):
            killed = np.zeros(2 * Q, dtype=bool)
            for q in prs:
                for u in killed_residues(q, self.n, self.b):
                    killed[u::q] = True
            idx = np.nonzero(killed)[0] + offs[t]
            np.bitwise_or.at(bits, idx >> 5,
                             np.uint32(1) << (idx & 31).astype(np.uint32))
        self.d_bits = cp.asarray(bits)
        self._boff = np.array(offs, dtype=np.uint64)
        self._qs = np.array(Qs, dtype=np.uint64)
        # W mod Q per unit, so a launch's base fold is one vectorised step
        # instead of thousands of big-int divisions -- see _basemod.
        self._wmod = np.array([self.W % int(q) for q in Qs] or [0],
                              dtype=np.uint64)[:max(len(Qs), 1)]
        self._pk = np.zeros((max(self.npr, 1), 4), dtype=np.uint32)
        if self.npr:
            self._pk[:, 0] = (mag & 0xFFFFFFFF).astype(np.uint32)
            self._pk[:, 1] = (mag >> 32).astype(np.uint32)
            self._pk[:, 2] = self._qs.astype(np.uint32)
        self.d_pk = cp.zeros(max(self.npr, 1) * 4, dtype=cp.uint32)

        # --- queues, launch size, kernels ---
        self.q1cap = _qcap(self.yblk, self.d2)
        tile = max(self.yblk * self.d2, 1.0)
        self.q2cap = max(32, _qcap(tile, self._S[self.bounds[1]]
                                   if len(self.bounds) > 1 else 1.0))
        self.ttile = self.tpb * TTILE_MUL
        s0 = self._S[self.bounds[-1]]
        nxt = (self._S[self.tbounds[1]] / s0
               if len(self.tbounds) > 1 and s0 > 0 else 1.0)
        self.tcap = max(32, _qcap(self.ttile, min(1.0, nxt)))
        self.per_launch = self._pick_launch(per_launch)
        self.q3cap = self._pick_q3cap()
        # Queue capacities are TUNING constants, never correctness bounds:
        # every overflow path finishes the candidate on the spot with the
        # same arithmetic.  G16 forces all four small and requires the
        # identical stream, which is the only way that claim is checkable.
        for k, v in (force_caps or {}).items():
            setattr(self, k, int(v))
        self.d_q3 = cp.empty(self.q3cap, dtype=cp.uint64)
        self.d_n3 = cp.zeros(1, dtype=cp.int32)
        self.d_out = cp.empty(HIT_CAP, dtype=cp.uint64)
        self.d_cnt = cp.zeros(1, dtype=cp.int32)
        self.k_sieve, self.k_tail = self._build()
        self.tail_grid = TAIL_BLOCKS_PER_SM * cp.cuda.runtime.\
            getDeviceProperties(cp.cuda.Device().id)["multiProcessorCount"]

    # --------------------------------------------------------- geometry
    def _pick_launch(self, per_launch):
        """Periods per launch: as wide as the TAIL QUEUE takes.

        An EXPLICIT per_launch is honoured exactly -- it is how the gates
        force a launch split, and rounding it to a whole block tile would
        turn "18 periods in one launch against six" into two identical
        single-launch sweeps and make that check vacuous.  Only the DERIVED
        value is rounded to whole tiles, where it costs nothing.
        """
        cap = max(1, (REDUCE_MAX - self.q2) // self.W)
        if per_launch:
            want = int(per_launch)
        else:
            # the largest power of two whose slot count fits the target, so
            # the block tile divides it exactly and no thread is masked off
            target = max(32, CAND_SLOTS // max(self.R, 1))
            # ... AND which the tail queue can still take.  That is the
            # constraint that actually binds, and it is a function of the
            # WHEEL: q3 holds R * per_launch * d2 * S_tail entries, so a
            # deeper p2 empties it and a wider flat table fills it.  A
            # launch past Q3_MAX spills into the in-block fallback and
            # costs ~19% (see _pick_q3cap), so the derivation stops one
            # power of two short of that rather than reporting q3_short
            # and running anyway.  Deriving against the slot count ALONE
            # got both families wrong the moment p2 moved: b = 4 stayed at
            # 1024 when 4096 measured 1.07x, and b = 4's old peak at 4096
            # was unreachable for exactly this reason.
            den = self.R * self.d2 * self._S[self.bounds[-1]] * 1.25
            if den > 0:
                target = min(target, max(32, int((Q3_MAX - 4096) / den)))
            want = 32
            while want * 2 <= target:
                want *= 2
        out = int(min(want, cap))
        if out < 1:
            raise ValueError(f"one period ({self.W}) already exceeds the "
                             f"Barrett bound {REDUCE_MAX}")
        return out

    def _pick_q3cap(self):
        """Global tail queue: analytic occupancy plus margin, capped.

        Overflow costs correctness nothing -- an item that does not fit runs
        its tail inside the sieve block, which is the same arithmetic -- but
        it costs a fifth of the rate at production launch size, so the
        ceiling is set to clear the analytic need rather than to be tidy.
        `q3_short` says whether it did, and config() reports it.
        """
        cands = self.R * self.per_launch * self.d2
        want = int(cands * self._S[self.bounds[-1]] * 1.25) + 4096
        cap = int(min(Q3_MAX, max(4096, want)))
        self.q3_short = want > cap
        return cap

    def _tile(self, nper):
        """(wact, rpb, logw): the block's (words of j) x (residues) tile."""
        wpb = self.tpb * self.wpt
        need = max(1, (int(nper) + 31) // 32)
        logw = 0
        while (1 << logw) < min(need, wpb):
            logw += 1
        wact = 1 << logw
        return wact, max(1, min(RPB_MAX, wpb // wact)), logw

    # --------------------------------------------------- generated source
    def _rounds_src(self):
        """The in-block compaction chain, then the push to the tail queue."""
        bufs = [("qk", "Q1CAP"), ("qk2", "Q2CAP")]
        cur, n, out = 0, "nq1", []
        for r in range(len(self.bounds) - 1):
            b0, b1 = self.bounds[r], self.bounds[r + 1]
            src, _ = bufs[cur]
            dst, dcap = bufs[1 - cur]
            out.append(f"""    for (int idx = threadIdx.x; idx < {n}; idx += TPB) {{
        const int key = {src}[idx];
        const unsigned long long off = OFF_OF(key >> (logw + 5), key & ymask);
        unsigned int kill = 0u;
#pragma unroll
        for (int t = {b0}; t < {b1}; ++t) TEST(t, kill)
        if (!kill) {{
            const int q = atomicAdd(&qcnt[{r}], 1);
            if (q < {dcap}) {dst}[q] = (unsigned short)key;
            else if (tail_survives(off, np_, {b1}, pk, bits)) EMIT(off)
        }}
    }}
    __syncthreads();
    const int nq{r + 2} = min(qcnt[{r}], {dcap});""")
            cur = 1 - cur
            n = f"nq{r + 2}"
        src, _ = bufs[cur]
        out.append(f"""    if (threadIdx.x == 0) q3b = ({n} > 0) ? atomicAdd(n3, {n}) : 0;
    __syncthreads();
    for (int idx = threadIdx.x; idx < {n}; idx += TPB) {{
        const int key = {src}[idx];
        const unsigned long long off = OFF_OF(key >> (logw + 5), key & ymask);
        const int p = q3b + idx;
        if (p < q3cap) q3[p] = off;
        else if (tail_survives(off, np_, {self.bounds[-1]}, pk, bits))
            EMIT(off)
    }}""")
        return chr(10).join(out)

    def _trounds_src(self):
        """The tail kernel's own compaction chain, ping-ponged in shared."""
        bufs = [("ta", "TTILE"), ("tb", "TCAP")]
        cur, n, out = 0, "tm1", []
        for r in range(len(self.tbounds) - 1):
            b0, b1 = self.tbounds[r], self.tbounds[r + 1]
            src, _ = bufs[cur]
            dst, dcap = bufs[1 - cur]
            out.append(f"""        for (int i = threadIdx.x; i < {n}; i += TPB) {{
            const unsigned long long off = {src}[i];
            unsigned int kill = 0u;
#pragma unroll
            for (int t = {b0}; t < {b1}; ++t) TEST(t, kill)
            if (!kill) {{
                const int q = atomicAdd(&tn[{r}], 1);
                if (q < {dcap}) {dst}[q] = off;
                else if (tail_survives(off, np_, {b1}, pk, bits)) EMIT(off)
            }}
        }}
        __syncthreads();
        const int tm{r + 2} = min(tn[{r}], {dcap});""")
            cur = 1 - cur
            n = f"tm{r + 2}"
        src, _ = bufs[cur]
        out.append(f"""        for (int i = threadIdx.x; i < {n}; i += TPB) {{
            const unsigned long long off = {src}[i];
            if (tail_survives(off, np_, {self.tbounds[-1]}, pk, bits))
                EMIT(off)
        }}""")
        return chr(10).join(out)

    def _build(self):
        cp = self.cp
        pro, gl = [], []
        for gi, g in enumerate(self.planes):
            # cr_g(r) = (W^-1 mod Q_g) * r mod Q_g -- see plane_shifts, which
            # stays as the host-side reference and is what G16 pins this
            # constant and this expression against.
            pro.append(f"""    for (int rl = threadIdx.x; rl < nrl; rl += TPB) {{
        unsigned long long z = (unsigned long long)cbase[{gi}]
            + (res[r1base + rl] % {g['Q']}ULL)
              * {self.winv[gi]}ULL % {g['Q']}ULL;
        if (z >= {g['Q']}ULL) z -= {g['Q']}ULL;
        z = (z + (unsigned long long)ybase) % {g['Q']}ULL;
        zc[rl * NG + {gi}] = (unsigned int)z + {self.goff[gi]}u;
    }}""")
            gl.append(f"""            {{ const unsigned int c = zc[zb + {gi}];
              const unsigned int* B = gbits + (c >> 5) + wrd;
              mask &= __funnelshift_r(B[0], B[1], c & 31); }}""")
        zbcalc = ""
        if self.ng:
            # ONE STRAIGHT-LINE PASS PER GROUP, NOT A SWITCH OVER GROUPS.
            # The prologue used to walk `nrl * NG` items with `g` fastest
            # and dispatch on it, so a warp covered every group at once and
            # ran all NG case bodies serially -- five times the cost of the
            # one body each lane needed.  That was survivable when a case
            # was a single modulo; it is not now that the case computes the
            # plane shift.  Per group the body is straight-line with its Q,
            # its W^-1 and its plane offset as literals, and `g` is gone
            # from the runtime entirely.
            zbcalc = chr(10).join(pro)
            gl.insert(0, "            const int zb = rl * NG;")
        src = _SRC % {
            "tpb": self.tpb, "wpt": self.wpt, "ng": self.ng,
            "q1cap": self.q1cap, "q2cap": self.q2cap, "w1": self.W,
            "unroll": UNROLL, "rpbmax": RPB_MAX,
            "nround": len(self.bounds) - 1, "ttile": self.ttile,
            "tcap": self.tcap, "tround": len(self.tbounds) - 1,
            "rounds": self._rounds_src(), "trounds": self._trounds_src(),
            "zbcalc": zbcalc, "gload": chr(10).join(gl)}
        self.src = src
        if src not in _MODULES:
            _MODULES[src] = cp.RawModule(code=src, options=("-std=c++14",),
                                         backend="nvrtc")
        mod = _MODULES[src]
        return mod.get_function("sieve"), mod.get_function("tailsweep")

    # ------------------------------------------------------------ metadata
    def config(self):
        return {"engine": "v2", "n": self.n, "b": self.b, "p1": self.p1,
                "p2": self.p2, "q2": self.q2, "W": self.W, "R": self.R,
                "ng": self.ng, "d2": self.d2, "units": self.npr,
                "bounds": list(self.bounds), "tbounds": list(self.tbounds),
                "per_launch": self.per_launch, "tpb": self.tpb,
                "wpt": self.wpt, "q1cap": self.q1cap, "q2cap": self.q2cap,
                "q3cap": self.q3cap, "ttile": self.ttile, "tcap": self.tcap,
                "q3_short": self.q3_short}

    def nbytes(self):
        return int(self.d_res.nbytes + self.d_gbits.nbytes
                   + self.d_bits.nbytes + self.d_pk.nbytes
                   + self.d_q3.nbytes + self.d_out.nbytes)

    def density(self):
        """Candidates per unit of m line -- what the wheel is worth."""
        return self.R * self.d2 / self.W

    # --------------------------------------------------------------- sweep
    def sweep(self, j0, j1):
        """Yield (j_next, survivors) after every launch.

        `j_next` is BOTH cursors at once: the wheel emits every candidate of
        a period inside one launch, so the line below j_next * W is swept and
        the work resumes there too.  The bit planes do not change that --
        they filter j, they do not reorder it, which is exactly why W is
        still the period the checkpoint counts in.

        The bounds are checked EAGERLY, here, and the launches are a separate
        generator: a `yield` in this body would defer every check to the
        first `next()`, and a caller that built the iterator and never
        consumed it would sail past the ceiling in silence.
        """
        j0, j1 = int(j0), int(j1)
        ceil = k_ceil(self.n, self.b)
        if j1 * self.W > ceil:
            raise ValueError(f"m {j1 * self.W} past the enforced ceiling "
                             f"{ceil}")
        if j0 * self.W <= m_floor(self.q2):
            raise ValueError(
                "engines refuse to run at or below max(K_FLOOR, q2): the "
                "wheel argument has an exception zone there and a kill by q "
                "needs value > q")
        return self._sweep(j0, j1)

    def _basemod(self, lo):
        """`(lo*W) mod Q` for every test unit, without a big-int division.

        (lo*W) mod Q = ((W mod Q) * (lo mod Q)) mod Q, and both factors are
        under 2^32 with Q under 2^17, so the product is exact in u64 for any
        lo whatsoever -- one vectorised numpy step for the whole table.
        Doing it the obvious way was 6,519 Python divisions of a big int per
        SWEEP, which is 4.4 ms against a 5.5 ms launch: 44% of the wall clock
        of the frozen SCORE window, which is one launch wide.
        """
        if lo < (1 << 64):
            return (self._wmod * (np.uint64(lo) % self._qs)) % self._qs
        # lo outgrows u64 only on a wheel far too narrow to hunt with, where
        # the modulo cannot be vectorised.  Kept exact anyway: a gate runs
        # here, and a gate that quietly went wrong at the top of the range is
        # the failure this path exists to prevent.
        return np.array([(int(wm) * (lo % int(q))) % int(q)
                         for wm, q in zip(self._wmod, self._qs)],
                        dtype=np.uint64)

    def _sweep(self, j0, j1):
        cp = self.cp
        for lo in range(j0, j1, self.per_launch):
            nper = min(self.per_launch, j1 - lo)
            base = self.W * lo
            if self.npr:
                self._pk[:, 3] = (self._boff
                                  + self._basemod(lo)).astype(np.uint32)
                self.d_pk.set(self._pk.ravel())
            if self.ng:
                self.d_cbase.set(np.array([lo % g["Q"] for g in self.planes],
                                          dtype=np.uint32))
            self.d_cnt.fill(0)
            self.d_n3.fill(0)
            wact, rpb, logw = self._tile(nper)
            grid = ((self.R + rpb - 1) // rpb,
                    (nper + (wact << 5) - 1) // (wact << 5))
            self.k_sieve(grid, (self.tpb,),
                         (self.d_res, np.int32(self.R),
                          self.d_gbits, self.d_cbase, np.int32(nper),
                          np.int32(rpb), np.int32(logw), np.int32(self.npr),
                          self.d_pk, self.d_bits, self.d_q3, self.d_n3,
                          np.int32(self.q3cap), self.d_out, self.d_cnt,
                          np.int32(HIT_CAP)))
            self.k_tail((self.tail_grid,), (self.tpb,),
                        (self.d_q3, self.d_n3, np.int32(self.q3cap),
                         self.d_out, self.d_cnt, np.int32(HIT_CAP),
                         np.int32(self.npr), self.d_pk, self.d_bits))
            cnt = int(self.d_cnt.get()[0])
            if cnt > HIT_CAP:
                raise RuntimeError(
                    f"survivor buffer overflow: {cnt} > {HIT_CAP}; the "
                    f"launch is too wide or the sieve too shallow")
            surv = []
            if cnt:
                offs = cp.asnumpy(self.d_out[:cnt])
                surv = sorted(base + int(o) for o in offs)
            yield lo + nper, surv

    def survivors_j(self, j0, j1):
        out = []
        for _jn, surv in self.sweep(j0, j1):
            out.extend(surv)
        return out

    def survivors_m(self, m_lo, m_hi):
        """The same stream, clipped to an arbitrary half-open m window."""
        m_lo, m_hi = int(m_lo), int(m_hi)
        j0, j1 = m_lo // self.W, (m_hi - 1) // self.W + 1
        return [m for m in self.survivors_j(j0, j1) if m_lo <= m < m_hi]


# --------------------------------- gates -----------------------------------

def g7_wheel_matches_oracle():
    """The CRT-lifted wheel == the oracle's brute-force period walk."""
    from shiftladder_reference import wheel_residues
    checks = 0
    for b, n, p1 in ((4, 5, 7), (4, 12, 11), (2, 9, 11), (2, 17, 13),
                     (4, 19, 13)):
        W, res = wheel(n, b, p1)
        W2, want = wheel_residues(n, b, p1)
        got = [int(x) for x in res]
        if W != W2 or got != sorted(want):
            return False, (f"G7 FAIL: b={b} n={n} p1={p1}: {len(got)} "
                           f"lifted vs {len(want)} walked")
        if not want:
            return False, f"G7 FAIL: b={b} n={n} p1={p1} wheel is empty"
        checks += len(want)
    return True, (f"G7 ok: CRT-lifted wheel == oracle period walk at 5 "
                  f"(b, n, p1) settings ({checks} residues), both bases")


def g8_wheel_is_exactly_the_product():
    """|wheel| = prod (q - w(q,n,b)), duplicate-free, nothing killed."""
    for b, n, p1 in ((4, 19, 23), (4, 12, 19), (2, 17, 37), (2, 21, 23)):
        W, res = wheel(n, b, p1)
        want = 1
        for q in primerange(2, p1 + 1):
            want *= q - w(q, n, b)
        if res.size != want:
            return False, (f"G8 FAIL: b={b} n={n} p1={p1}: {res.size} "
                           f"residues, formula says {want}")
        ints = [int(x) for x in res]
        if len(set(ints)) != len(ints):
            return False, f"G8 FAIL: b={b} n={n} p1={p1}: duplicate residues"
        tables = {q: set(killed_residues(q, n, b))
                  for q in primerange(2, p1 + 1)}
        for r in ints[::max(1, len(ints) // 512)]:
            for q, killed in tables.items():
                if r % q in killed:
                    return False, (f"G8 FAIL: b={b} n={n} p1={p1}: residue "
                                   f"{r} is killed by {q}")

    # THE CACHE IS KEYED ON THE EFFECTIVE `w` VECTOR, NOT ON n.  Both
    # directions, because the cheap half (reuse) is the one that can go
    # wrong silently: a wheel served for a filter whose w vector differs
    # would sieve for the wrong sequence and every downstream gate would
    # still be comparing it against itself.
    same = []
    for b, p1, n1, n2 in ((4, 29, 14, 21), (4, 29, 21, 40), (2, 41, 36, 41)):
        (W1, r1), (W2, r2) = wheel(n1, b, p1), wheel(n2, b, p1)
        if W1 != W2 or r1 is not r2:
            return False, (f"G8 FAIL: b={b} p1={p1}: n={n1} and n={n2} have "
                           f"the same w vector but were built twice")
        same.append(f"b={b} n={n1}=={n2}")
    for b, p1, n1, n2 in ((4, 13, 5, 6), (2, 13, 11, 12)):
        (_W1, r1), (_W2, r2) = wheel(n1, b, p1), wheel(n2, b, p1)
        if r1 is r2 or r1.size == r2.size:
            return False, (f"G8 FAIL: b={b} p1={p1}: n={n1} and n={n2} have "
                           f"DIFFERENT w vectors and must not share a wheel")
    return True, ("G8 ok: the wheel is exactly prod(q - w(q,n,b)) residues, "
                  "duplicate-free and unkilled, at (b,n,p1) = (4,19,23), "
                  "(4,12,19), (2,17,37), (2,21,23); and the cache is keyed "
                  f"on the w VECTOR -- {', '.join(same)} share one table "
                  "while n=5/6 at (b=4,p1=13) and n=11/12 at (b=2,p1=13) "
                  "do not")


def g9_gpu_matches_cpu():
    """GPU stream == CPU stream, bit for bit, on POPULATED windows.

    Both bases, several heights, and the top window sits ABOVE 2^64 -- the
    whole point of carrying (m, off), and a comparison of two empty sets
    would be no check at all, so each window is asserted non-empty.
    """
    cases = ((4, 5, 7, 64, 20_000, 400_000),
             (4, 12, 13, 128, 3_000_000, 2_000_000),
             (2, 9, 11, 64, 50_000, 2_000_000),
             (2, 14, 13, 64, 10_000_000, 20_000_000),
             (4, 8, 11, 64, 1 << 64, 4_000_000),
             (2, 10, 13, 64, (1 << 64) + 10 ** 12, 20_000_000))
    total = 0
    for b, n, p1, q2, m_lo, span in cases:
        eng = GpuEngine(n, b, p1=p1, q2=q2, per_launch=8)
        got = eng.survivors_m(m_lo, m_lo + span)
        cpu = CpuEngine(n, b, q2=q2)
        want = []
        for chunk in cpu.survivors(m_lo, m_lo + span):
            want.extend(int(x) for x in chunk)
        if got != want:
            bad = sorted(set(got) ^ set(want))[:4]
            return False, (f"G9 FAIL: b={b} n={n} p1={p1} q2={q2} window "
                           f"{m_lo}+{span}: {len(got)} GPU vs {len(want)} "
                           f"CPU, symmetric difference {bad}")
        if not want:
            return False, (f"G9 FAIL: b={b} n={n} window {m_lo}+{span} is "
                           f"empty -- vacuous check")
        total += len(want)
    return True, (f"G9 ok: GPU stream == CPU stream on {len(cases)} "
                  f"populated windows ({total} survivors), both bases, "
                  f"heights 2e4 -> 1.8e19, the top two ABOVE 2^64")


def g15_stream_is_invariant_under_the_base():
    """Nothing on the device may depend on where the launch base was put.

    Two checks, and the second is the one that matters for (m, off): the
    same window swept in one launch and in six must give the identical
    stream, and a window whose base is a big int far above 2^64 must give
    the stream the CPU engine gives -- which is only true if the per-unit
    `boff` fold and the per-plane `cbase` shift are both exact.
    """
    b, n, p1, q2 = 4, 8, 11, 64
    eng1 = GpuEngine(n, b, p1=p1, q2=q2, per_launch=64)
    eng6 = GpuEngine(n, b, p1=p1, q2=q2, per_launch=3)
    j0 = (10 ** 6) // eng1.W + 1
    a = eng1.survivors_j(j0, j0 + 18)
    c = eng6.survivors_j(j0, j0 + 18)
    if a != c or not a:
        return False, (f"G15 FAIL: {len(a)} survivors in one launch vs "
                       f"{len(c)} in six")
    folds = 0
    for base_m in (10 ** 12, 1 << 64, 10 ** 24, 3 * 10 ** 24):
        eng = GpuEngine(n, b, p1=p1, q2=q2, per_launch=4)
        j = base_m // eng.W
        lo, hi = j * eng.W, (j + 4) * eng.W
        if hi > k_ceil(n, b):
            continue
        got = eng.survivors_j(j, j + 4)
        cpu = CpuEngine(n, b, q2=q2)
        want = []
        for chunk in cpu.survivors(max(lo, m_floor(q2) + 1), hi):
            want.extend(int(x) for x in chunk)
        if got != want:
            return False, (f"G15 FAIL: base {base_m:.3g}: {len(got)} GPU vs "
                           f"{len(want)} CPU")
        folds += len(want)
    return True, (f"G15 ok: the survivor stream is invariant under the "
                  f"launch split (18 periods, 1 launch vs 6), and the base "
                  f"fold is exact at m = 1e12, 2^64, 1e24 and 3e24 "
                  f"({folds} survivors) -- so nothing on the device is "
                  f"bounded by a machine word")


def g16_v2_mechanisms():
    """The v2 mechanisms, each checked against something independent.

    1. THE BIT PLANES.  A plane says a period index survives a group of
       primes; divisibility says whether m = j*W + r does.  They must agree
       for every (residue, period) pair sampled -- BOTH ways, because a
       plane that killed too much would silently lose survivors and a
       sparse parity window could miss it.
    2. THE SCHEDULES ARE FRACTIONS.  The round boundaries come out of the
       survival curve, so the same target must produce DIFFERENT depths at
       two configurations whose curves differ.  A count carried between
       configurations is the bug this checks for, and it is the one
       square-ladders paid 22% for.
    3. THE FOUR OVERFLOW PATHS.  Every queue capacity is a tuning constant,
       never a correctness bound: an item that does not fit finishes on the
       spot with the same arithmetic.  All four are forced to a token size
       and the stream must be identical.
    4. THE ADAPTIVE TILE.  A launch too short to fill a block's word tile
       must spread the block over residues instead, and give the same
       stream as a launch wide enough not to.
    5. THE PLANE SHIFT IS COMPUTED, NOT STORED.  The kernel derives
       cr_g(r) = (W^-1 mod Q_g) * r mod Q_g in the block prologue instead
       of reading a table of R * NG u32.  `plane_shifts` -- the slow CRT
       reconstruction -- stays as the reference, and BOTH halves of what
       replaced it are checked against it: the identity, over every residue
       of several wheels on both bases, and the CONSTANT the generated
       kernel actually carries.  A right formula with a wrong literal is
       the failure this second half exists to catch.
    6. THE KEY ENCODE MATCHES THE KEY DECODE.  Generation packs
       (rl, wrd, bit) as `idx << 5`; the rounds unpack it with
       `key >> (logw + 5)` and `key & ymask`.  The collapse is only valid
       because wact = 1 << logw, so it is checked over every tile shape the
       engine can pick rather than argued.
    """
    # 1 -- planes against divisibility, both directions
    n, b, p1, p2 = 12, 4, 13, 47
    W, res = wheel(n, b, p1)
    planes = build_planes(n, b, p1, p2, 1024)
    crs = plane_shifts(res, planes, W)
    pprimes = [q for g in planes for q in g["primes"]]
    ktab = {q: set(killed_residues(q, n, b)) for q in pprimes}
    seen = [0, 0]
    for i in range(0, res.size, max(1, res.size // 97)):
        r = int(res[i])
        for j in range(400, 460):
            alive_plane = True
            for gi, g in enumerate(planes):
                z = (int(crs[gi][i]) + j) % g["Q"]
                if not ((int(g["words"][z >> 5]) >> (z & 31)) & 1):
                    alive_plane = False
                    break
            m = j * W + r
            alive_true = all(m % q not in ktab[q] for q in pprimes)
            if alive_plane != alive_true:
                return False, (f"G16 FAIL: the plane says {alive_plane} for "
                               f"m={m} (r={r}, j={j}); divisibility says "
                               f"{alive_true}")
            seen[int(alive_true)] += 1
    if not seen[0] or not seen[1]:
        return False, (f"G16 FAIL: the plane check was one-sided "
                       f"({seen[0]} killed, {seen[1]} kept)")

    # 2 -- the schedule is a fraction, not a count
    units = test_units(47, 65536, UNIT_Q_MAX)
    sa = schedule(survival(19, 4, units), len(units), ROUND_RATIO, TAIL_SURV)
    sb = schedule(survival(10, 4, units), len(units), ROUND_RATIO, TAIL_SURV)
    if sa == sb:
        return False, ("G16 FAIL: the round schedule is identical at n = 19 "
                       "and n = 10, so it is a count and not a fraction")

    # 3 -- every overflow path, forced, stream unchanged
    n, b, p1, q2 = 12, 4, 13, 128
    lo, span = 3_000_000, 2_000_000
    ref = GpuEngine(n, b, p1=p1, q2=q2).survivors_m(lo, lo + span)
    if len(ref) < 32:
        return False, f"G16 FAIL: the overflow window holds only {len(ref)}"
    tiny = GpuEngine(n, b, p1=p1, q2=q2,
                     force_caps={"q1cap": 32, "q2cap": 32, "q3cap": 4096,
                                 "tcap": 32})
    if tiny.survivors_m(lo, lo + span) != ref:
        return False, ("G16 FAIL: with every queue forced tiny the stream "
                       "changed")

    # 4 -- the adaptive tile: a launch shorter than one block tile
    narrow = GpuEngine(n, b, p1=p1, q2=q2, per_launch=64)
    if narrow._tile(64)[1] <= 1:
        return False, ("G16 FAIL: a 64-period launch did not spread the "
                       "block over residues -- rpb stayed 1")
    if narrow.survivors_m(lo, lo + span) != ref:
        return False, "G16 FAIL: the narrow-launch tile changed the stream"

    # 5 -- the computed plane shift == plane_shifts, and the baked constant
    shifts = 0
    for nn, bb, pp1, pp2 in ((12, 4, 13, 47), (19, 4, 17, 79),
                             (9, 2, 11, 53), (17, 2, 13, 71)):
        WW, rr = wheel(nn, bb, pp1)
        pls = build_planes(nn, bb, pp1, pp2, 1024)
        for g, cr in zip(pls, plane_shifts(rr, pls, WW)):
            Q, binv = g["Q"], pow(WW, -1, g["Q"])
            got = (binv * rr.astype(object)) % Q
            if not all(int(x) == int(y) for x, y in zip(got, cr)):
                return False, (f"G16 FAIL: b={bb} n={nn} Q={Q}: "
                               f"(W^-1 mod Q)*r mod Q != plane_shifts")
            shifts += int(rr.size)
    baked = 0
    for nn, bb in ((12, 4), (9, 2)):
        e = GpuEngine(nn, bb, p1=13, q2=128)
        for gi, g in enumerate(e.planes):
            want = pow(e.W, -1, g["Q"])
            if e.winv[gi] != want:
                return False, (f"G16 FAIL: baked W^-1 mod {g['Q']} is "
                               f"{e.winv[gi]}, should be {want}")
            if (f"* {want}ULL % {g['Q']}ULL" not in e.src
                    or "crv" in e.src):
                return False, (f"G16 FAIL: the generated kernel does not "
                               f"carry W^-1 mod {g['Q']} = {want}, or still "
                               f"reads a crv table")
            baked += 1

    # 6 -- key encode == key decode, at every tile shape the engine picks
    keys = 0
    for logw in range(0, 11):
        wact, ymask = 1 << logw, (1 << logw << 5) - 1
        for idx in (0, 1, wact - 1, wact, 2 * wact + 3, 1023):
            for bit in (0, 5, 31):
                key = (idx << 5) + bit
                if (key >> (logw + 5) != idx >> logw
                        or key & ymask != ((idx & (wact - 1)) << 5) + bit):
                    return False, (f"G16 FAIL: key encode/decode disagree "
                                   f"at logw={logw} idx={idx} bit={bit}")
                keys += 1
    return True, (f"G16 ok: bit planes == divisibility BOTH ways on "
                  f"{sum(seen)} (residue, period) pairs ({seen[0]} killed, "
                  f"{seen[1]} kept); the round schedule is a survival "
                  f"FRACTION (depths {sa} at n=19 vs {sb} at n=10); all four "
                  f"queues forced to token size leave the stream identical "
                  f"({len(ref)} survivors); a launch shorter than one "
                  f"block tile spreads over residues with the same stream; "
                  f"the COMPUTED plane shift (W^-1 mod Q)*r mod Q equals "
                  f"plane_shifts on {shifts} residues across 4 wheels and "
                  f"both bases, with all {baked} baked constants present in "
                  f"the generated kernel and no crv table left in it; and "
                  f"key encode == key decode on {keys} cases over every "
                  f"tile shape logw = 0..10")


GATES = [g7_wheel_matches_oracle, g8_wheel_is_exactly_the_product,
         g9_gpu_matches_cpu, g15_stream_is_invariant_under_the_base,
         g16_v2_mechanisms]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
