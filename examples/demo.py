"""
examples/demo.py — Usage examples for the Enigma machine implementation
========================================================================
Run this file directly to see each example in action:

    python examples/demo.py

Sections:
    1. Basic encryption and decryption
    2. Symmetry property
    3. Effect of rotor stepping (same key, different starting positions)
    4. Plugboard impact
    5. Double-stepping anomaly demonstration
    6. Historical key format parsing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from enigma import EnigmaMachine, ALPHABET


def separator(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


# ---------------------------------------------------------------------------
# 1. Basic encryption and decryption
# ---------------------------------------------------------------------------

separator("1. Basic encryption and decryption")

enigma = EnigmaMachine(
    rotor_names   = ["I", "II", "III"],
    positions     = ['A', 'A', 'A'],
    ring_settings = ['A', 'A', 'A'],
    plugboard     = [],
    reflector     = "B",
)

plaintext  = "HELLO WORLD"
ciphertext = enigma.encrypt(plaintext)

# Decryption: reset to the same position and encrypt again
enigma.reset(['A', 'A', 'A'])
decrypted = enigma.encrypt(ciphertext)

print(f"  Plaintext  : {plaintext}")
print(f"  Ciphertext : {ciphertext}")
print(f"  Decrypted  : {decrypted}")
print(f"  Round-trip : {'OK' if decrypted.replace(' ','') == plaintext.replace(' ','') else 'FAIL'}")


# ---------------------------------------------------------------------------
# 2. Symmetry property
# ---------------------------------------------------------------------------

separator("2. Symmetry — encrypt(encrypt(m)) == m")

enigma = EnigmaMachine(
    rotor_names   = ["I", "II", "III"],
    positions     = ['D', 'E', 'F'],
    ring_settings = ['A', 'A', 'A'],
    plugboard     = [('A', 'Z'), ('B', 'Y')],
    reflector     = "B",
)

msg = "THEQUICKBROWNFOX"
ct  = enigma.encrypt(msg)
enigma.reset(['D', 'E', 'F'])
rt  = enigma.encrypt(ct)

print(f"  Original   : {msg}")
print(f"  Encrypted  : {ct}")
print(f"  Re-encrypted (== original?) : {rt}  → {'YES' if rt == msg else 'NO'}")


# ---------------------------------------------------------------------------
# 3. Starting position matters — same key, different window settings
# ---------------------------------------------------------------------------

separator("3. Starting position changes everything")

msg = "ATTACK"
for pos in [['A', 'A', 'A'], ['A', 'A', 'B'], ['B', 'A', 'A'], ['Z', 'Z', 'Z']]:
    enigma = EnigmaMachine(
        rotor_names = ["I", "II", "III"],
        positions   = pos,
        ring_settings = ['A', 'A', 'A'],
        plugboard   = [],
        reflector   = "B",
    )
    ct = enigma.encrypt(msg)
    print(f"  Position {''.join(pos)} → {ct}")


# ---------------------------------------------------------------------------
# 4. Plugboard impact
# ---------------------------------------------------------------------------

separator("4. Plugboard — each pair swaps two letters end-to-end")

msg = "ENIGMA"
for pairs in [[], [('E', 'X')], [('E', 'X'), ('N', 'A')], [('E', 'X'), ('N', 'A'), ('I', 'G')]]:
    enigma = EnigmaMachine(
        rotor_names   = ["I", "II", "III"],
        positions     = ['A', 'A', 'A'],
        ring_settings = ['A', 'A', 'A'],
        plugboard     = pairs,
        reflector     = "B",
    )
    ct = enigma.encrypt(msg)
    pair_str = ', '.join(f"{a}<->{b}" for a, b in pairs) if pairs else "(none)"
    print(f"  Plugboard {pair_str:<30} → {ct}")


# ---------------------------------------------------------------------------
# 5. No-self-encryption property
# ---------------------------------------------------------------------------

separator("5. No-self-encryption — a letter NEVER maps to itself")

enigma = EnigmaMachine(
    rotor_names   = ["I", "II", "III"],
    positions     = ['A', 'A', 'A'],
    ring_settings = ['A', 'A', 'A'],
    plugboard     = [],
    reflector     = "B",
)

# Encrypt the full alphabet 10 times and check for self-encryption
msg    = ALPHABET * 10
ct     = enigma.encrypt(msg)
clashes = sum(1 for p, c in zip(msg, ct) if p == c)

print(f"  Encrypted '{ALPHABET}' × 10 ({len(msg)} chars)")
print(f"  Self-encryptions found : {clashes}  (must always be 0)")
print(f"  Property holds         : {'YES' if clashes == 0 else 'NO'}")


# ---------------------------------------------------------------------------
# 6. Double-stepping anomaly
# ---------------------------------------------------------------------------

separator("6. Double-stepping anomaly")

# Rotor I notch at Q, Rotor II notch at E, Rotor III notch at V
# Set up so the middle rotor is one step before its notch (D → E triggers)
enigma = EnigmaMachine(
    rotor_names   = ["I", "II", "III"],
    positions     = ['A', 'D', 'U'],   # middle at D, right at U (one before V notch)
    ring_settings = ['A', 'A', 'A'],
    plugboard     = [],
    reflector     = "B",
)

print("  Rotor windows as keys are pressed (L M R):")
print(f"  Initial  : A D U")
for i in range(4):
    enigma.encrypt("A")   # each encrypt call steps the rotors
    l, m, r = [ALPHABET[rot.position] for rot in enigma.rotors]
    note = ""
    if i == 1:
        note = "  ← double-step: M steps again along with L"
    print(f"  Press {i+1}  : {l} {m} {r}{note}")

print()
print("  Expected sequence: ADV → ADW → AEX → BFY")
print("  (Middle rotor steps twice in a row due to the double-step anomaly)")


# ---------------------------------------------------------------------------
# 7. Ring setting (Ringstellung) effect
# ---------------------------------------------------------------------------

separator("7. Ring settings shift the wiring offset")

msg = "RINGSTELLUNG"
for ring in [['A','A','A'], ['B','A','A'], ['A','B','A'], ['C','C','C']]:
    enigma = EnigmaMachine(
        rotor_names   = ["I", "II", "III"],
        positions     = ['A', 'A', 'A'],
        ring_settings = ring,
        plugboard     = [],
        reflector     = "B",
    )
    ct = enigma.encrypt(msg)
    print(f"  Ring {''.join(ring)} → {ct}")
