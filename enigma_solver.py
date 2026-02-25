"""
enigma_solver.py  —  Crib attack on Enigma
==============================================================================
Skeleton for the cryptanalysis workshop. The code runs and reaches the first
real TODO. Your mission: implement the parts marked with TODO and watch the
solver gradually recover the key, step by step.

Algorithm:
  PHASE 0 — Pre-compute the 17,576 rotor cores (no plugboard)
  PHASE 1 — For each offset triple, solve the crib equations
             via backtracking  ->  candidates with partial plugboard
  PHASE 2 — Filter survivors: does the decrypted prefix look like English?
  PHASE 3 — Complete the plugboard and score with n-grams

Dependencies:
  Only enigma.py from this repository is needed (no extra installation).
  Keep enigma.py in the same directory as this file.

Usage:
  python enigma_solver.py
"""

import sys
from itertools import product
from enigma import EnigmaMachine, ALPHABET

# ── Problem configuration ─────────────────────────────────────────────────────

ROTORS    = ["I", "IV", "III"]     # order: left · middle · right
REFLECTOR = "B"
CRIB      = "WEATHER"              # known plaintext (first word)

# The intercepted ciphertext from docs/sample_challenge.md.
# Spaces mark original word boundaries and are not encrypted.
# Remove spaces before processing — only the letters matter for the attack.
CIPHERTEXT_RAW = (
    "VVNAMHJ QCZHTK UTF QVV LQSXA NXDWYXHO GLWTHY HUOFB KPEIBBK OGXOC "
    "KJQSSDAZJM BH JQM YOUD QAYGP WKM IBNCH HWV YAQPOSJ MBJHDBXTDO XWQN "
    "QEKCG JFKREX YWSSX XAGC MZR SIDSKYWIF XVFQ NCY PLQAU PDY ZLRTICO PSBA "
    "DLDZV UDMOBR RUMTKYFAQYS KWX CWTTDC SUVWMUYA GI MYBTWQZ ZXJUCCVJF EZ "
    "PUONV TZAZUUK"
)
CIPHERTEXT = CIPHERTEXT_RAW.replace(" ", "")

NUM_PAIRS = 7    # number of plugboard pairs

# Frequent English words for the Phase 2 filter
COMMON_WORDS = {
    "WEATHER", "REPORT", "FIELD", "COMMAND", "FORWARD", "ATTACK",
    "SECTOR", "NORTH", "SOUTH", "EAST", "WEST", "STOP", "FROM",
    "THE", "AND", "TO", "OF", "IN", "IS", "AT", "NO", "ORDER",
    "UNIT", "MESSAGE", "ALL", "ARE", "NOT", "FOR", "WITH",
}


# ── Utilities ─────────────────────────────────────────────────────────────────

def idx(c: str) -> int:
    """'A' -> 0, 'B' -> 1 ... 'Z' -> 25"""
    return ord(c.upper()) - ord('A')

def char(i: int) -> str:
    """0 -> 'A', 1 -> 'B' ... 25 -> 'Z'"""
    return ALPHABET[i % 26]


# ── PHASE 0 — Pre-compute the core table ──────────────────────────────────────

def core_mapping(pos_l: str, pos_m: str, pos_r: str) -> list:
    """
    Returns the rotor-core permutation for a given position,
    WITHOUT plugboard and with ring_settings = AAA.

    The core encrypts each letter through the full circuit
    (rotors -> reflector -> inverse rotors) once, without stepping.

    How it works: we build a plugboard-free machine, set it to the given
    position, and 'trick' it by encrypting each letter individually,
    resetting the position before each one (so the rotors do not advance
    between calls).

    Parameters
    ----------
    pos_l, pos_m, pos_r : str   position letters ('A'...'Z')

    Returns
    -------
    mapping : list[int] of length 26
        mapping[i] = j  means letter i enters and exits as j
    """
    machine = EnigmaMachine(
        rotor_names   = ROTORS,
        positions     = [pos_l, pos_m, pos_r],
        ring_settings = ['A', 'A', 'A'],
        plugboard     = [],
        reflector     = REFLECTOR,
    )
    mapping = []
    for i in range(26):
        # Reset before each letter so the rotors never advance
        machine.reset([pos_l, pos_m, pos_r])
        out = machine.encrypt(char(i))
        mapping.append(idx(out))
    return mapping


def build_core_table() -> list:
    """
    Pre-computes all 26^3 = 17,576 cores and stores them in a list.
    Access index: o_l * 676 + o_m * 26 + o_r

    Note: ring settings are ignored here (treated as AAA).

    TODO  -- Improvement --------------------------------------------------
    With real ring settings, each rotor's effective offset is:
        effective_offset = (position - ring_setting) % 26
    Right now we only explore positions with ring=AAA.
    How would you modify build_core_table() to also cover arbitrary ring
    settings?  How many entries would the table have?
    -----------------------------------------------------------------------
    """
    print("[Phase 0] Pre-computing 17,576 rotor cores...")
    table = []
    for o_l, o_m, o_r in product(range(26), repeat=3):
        table.append(core_mapping(char(o_l), char(o_m), char(o_r)))
    print(f"          -> {len(table)} cores computed.\n")
    return table


# ── PHASE 1 — Plugboard backtracking ──────────────────────────────────────────

def solve_plugboard(plain_idx_list, cipher_idx_list, core_maps):
    """
    Tries to find a plugboard (stecker) consistent with the crib equations.

    Equation for position k of the crib:
        stecker[ cipher_idx_list[k] ]  ==  core_maps[k][ stecker[ plain_idx_list[k] ] ]

    Parameters
    ----------
    plain_idx_list  : indices of the plaintext  (WEATHER -> [22,4,0,19,7,4,17])
    cipher_idx_list : indices of the ciphertext (first 7 letters of CIPHERTEXT)
    core_maps       : list of 26-permutations, one per crib position

    Returns
    -------
    stecker : list[int] of length 26   (stecker[i]=j means i is wired to j)
               -1 = not yet assigned
    None    : if no plugboard is consistent with all equations
    """
    stecker = [-1] * 26    # -1 means "unassigned"

    def assign(a, b):
        """
        Tries to wire a <-> b in the plugboard.
        The plugboard is an involution: if a -> b then b -> a.
        Returns True if consistent, False if there is a conflict.

        TODO -- Implement this function -----------------------------------
        Hint: before assigning, check whether stecker[a] or stecker[b]
        already hold a different value from what we want to set.
        Cases to handle:
          - stecker[a] == -1  and  stecker[b] == -1  -> assign freely
          - stecker[a] == b   and  stecker[b] == a   -> already set, consistent
          - any other case                            -> conflict, return False
        ------------------------------------------------------------------
        """
        raise NotImplementedError("TODO: implement assign(a, b)")

    def backtrack(k):
        """Satisfy the crib equations from position k onwards."""
        if k == len(plain_idx_list):
            return True     # all equations satisfied!

        p = plain_idx_list[k]
        c = cipher_idx_list[k]

        # If p has no stecker assigned yet, use p itself as a proxy
        # (equivalent to assuming p is not connected in the plugboard)
        sp = stecker[p] if stecker[p] != -1 else p

        # The equation tells us the required value for stecker[c]
        required = core_maps[k][sp]

        if assign(c, required):
            if backtrack(k + 1):
                return True
            # Undo the assignment
            stecker[c]        = -1
            stecker[required] = -1

        return False

    # TODO -- Think about this -------------------------------------------
    # The current backtrack is a simplification: when p has no stecker
    # assigned we assume sp = p (identity).
    # What would improve if instead we iterated over all 26 possible
    # values of stecker[p] and propagated the constraints?
    # -------------------------------------------------------------------

    if backtrack(0):
        return stecker
    return None


def phase1(core_table):
    """
    Phase 1: iterate over all 17,576 offset triples and apply backtracking.

    Returns a list of candidates:
        [{ 'offsets': (o_l, o_m, o_r), 'stecker': list[int] }, ...]
    """
    plain_indices  = [idx(c) for c in CRIB]
    cipher_indices = [idx(c) for c in CIPHERTEXT[:len(CRIB)]]

    candidates = []
    total = 26 ** 3
    print(f"[Phase 1] Exploring {total} offset triples...")

    for table_idx, (o_l, o_m, o_r) in enumerate(product(range(26), repeat=3)):

        # We use the same core for all crib positions.
        # This ignores rotor stepping within the crib itself.
        #
        # TODO -- Improvement: correct stepping ----------------------------
        # The rotors advance with every letter. For a crib of length n,
        # the offset triple changes at each position.
        # Hint: simulate the advance by incrementing o_r and carrying over
        # to o_m and o_l according to each rotor's notch letter.
        # -----------------------------------------------------------------
        core_maps = [core_table[table_idx]] * len(CRIB)

        stecker = solve_plugboard(plain_indices, cipher_indices, core_maps)

        if stecker is not None:
            candidates.append({
                "offsets" : (o_l, o_m, o_r),
                "stecker" : stecker,
            })

    print(f"          -> {len(candidates)} surviving candidates.\n")
    return candidates


# ── PHASE 2 — Prefix filter ───────────────────────────────────────────────────

def build_plugboard_pairs(stecker):
    """
    Converts the internal stecker list into letter-pair tuples for EnigmaMachine.
    Only returns real pairs (a != b), without duplicates.
    """
    pairs = []
    seen  = set()
    for i, j in enumerate(stecker):
        if j != -1 and j != i and i not in seen:
            pairs.append((char(i), char(j)))
            seen.update([i, j])
    return pairs


def decrypt_prefix(offsets, stecker, length=14):
    """
    Decrypts the first `length` characters of the message with the given settings.

    Note: stecker entries with value -1 are treated as identity
    (the letter passes through the plugboard unchanged).
    """
    o_l, o_m, o_r = offsets
    pairs = build_plugboard_pairs(stecker)

    machine = EnigmaMachine(
        rotor_names   = ROTORS,
        positions     = [char(o_l), char(o_m), char(o_r)],
        ring_settings = ['A', 'A', 'A'],
        plugboard     = pairs,
        reflector     = REFLECTOR,
    )
    return machine.encrypt(CIPHERTEXT[:length])


def looks_like_english(text, threshold=0.4):
    """
    Simple heuristic: are at least `threshold` fraction of the words
    in the text present in our dictionary?

    TODO -- Possible improvements -------------------------------------
    - Load a larger dictionary from an external .txt file
    - Check bigrams or trigrams of frequent English letters
    - Penalise impossible consonant clusters (sequences like QXZ)
    ------------------------------------------------------------------
    """
    words = text.split()
    if not words:
        return False
    found = sum(1 for w in words if w in COMMON_WORDS)
    return (found / len(words)) >= threshold


def phase2(candidates):
    """
    Phase 2: decrypt the prefix of each candidate and filter out
    those that do not look like English.
    """
    survivors = []
    print(f"[Phase 2] Filtering {len(candidates)} candidates by prefix...")

    for cand in candidates:
        prefix = decrypt_prefix(cand["offsets"], cand["stecker"])
        if looks_like_english(prefix):
            cand["prefix"] = prefix
            survivors.append(cand)

    print(f"          -> {len(survivors)} survivors after the filter.\n")
    return survivors


# ── PHASE 3 — Complete plugboard and score ────────────────────────────────────

def ngram_score(text, n=4):
    """
    Scores the text by counting frequent English n-grams.
    Higher score = more likely to be real English.

    Minimal implementation: a whitelist of common tetragrams.

    TODO -- Improvement -----------------------------------------------
    Download real n-gram log-probability tables from:
    http://practicalcryptography.com/cryptanalysis/letter-frequencies-and-word-lists/
    and use the formula:
        score = sum( log10( P(ngram) ) for ngram in text )
    This lets you rank candidates even when no complete dictionary
    word appears in the decrypted text.
    ------------------------------------------------------------------
    """
    COMMON = {
        "WEAT", "EATH", "ATHI", "THER", "REPO", "EPOR", "PORT",
        "TION", "WITH", "THAT", "MENT", "HAVE", "FROM",
        "IELD", "COMM", "OMMA", "MMAN", "MAND", "ORDE", "RDER",
    }
    return float(sum(1 for i in range(len(text) - n + 1) if text[i:i+n] in COMMON))


def complete_plugboard(stecker):
    """
    Fills unresolved plugboard entries (value -1) with identity.

    TODO -- Possible improvements -------------------------------------
    - If <= 2 pairs remain: enumerate all combinations and choose
      the one with the highest ngram_score.
    - If more remain: hill-climbing — propose random swaps between
      free letters and accept those that increase the score.
    ------------------------------------------------------------------
    """
    full = list(stecker)
    for i in range(26):
        if full[i] == -1:
            full[i] = i    # provisional identity
    return full


def decrypt_full(offsets, stecker):
    """Decrypts the entire message with the given settings."""
    return decrypt_prefix(offsets, stecker, length=len(CIPHERTEXT))


def phase3(survivors):
    """
    Phase 3: complete the plugboard, decrypt, and score each survivor.
    Returns the list sorted from highest to lowest score.
    """
    print(f"[Phase 3] Completing plugboard and scoring {len(survivors)} candidates...")

    for cand in survivors:
        full  = complete_plugboard(cand["stecker"])
        plain = decrypt_full(cand["offsets"], full)
        score = ngram_score(plain)
        cand.update({"full_stecker": full, "plaintext": plain, "score": score})

    survivors.sort(key=lambda c: c["score"], reverse=True)
    print(f"          -> Ranking complete.\n")
    return survivors


# ── Final output ──────────────────────────────────────────────────────────────

def print_results(results, top=5):
    sep = "-" * 60
    print(sep)
    print(f"  TOP {top} CANDIDATES")
    print(sep)
    for i, cand in enumerate(results[:top], 1):
        o_l, o_m, o_r = cand["offsets"]
        pos = char(o_l) + char(o_m) + char(o_r)
        plaintext = cand.get("plaintext", cand.get("prefix", "???"))
        print(f"\n  #{i}  Position : {pos}   Score : {cand.get('score', '?'):.1f}")
        print(f"      Text     : {plaintext[:40]}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  ENIGMA CRIB ATTACK — Cryptanalysis Workshop")
    print("=" * 60)
    print(f"  Rotors     : {' - '.join(ROTORS)}")
    print(f"  Reflector  : {REFLECTOR}")
    print(f"  Crib       : {CRIB}")
    print(f"  Ciphertext : {CIPHERTEXT[:20]}... ({len(CIPHERTEXT)} letters)")
    print()

    # Phase 0
    core_table = build_core_table()

    # Phase 1
    candidates = phase1(core_table)

    if not candidates:
        print("No candidates found. Check solve_plugboard() -> assign().")
        sys.exit(1)

    # Phase 2
    survivors = phase2(candidates)

    if not survivors:
        print("No survivors after prefix filter.")
        print("Try lowering the threshold in looks_like_english() or expanding COMMON_WORDS.")
        print("Continuing with all candidates for debugging...")
        survivors = candidates

    # Phase 3
    results = phase3(survivors)
    print_results(results)

    print("Good luck with the improvements!\n")


if __name__ == "__main__":
    main()