"""
enigma.py — A didactic implementation of the Enigma machine
============================================================
Purpose : Understand the internals of Enigma.

Historical note:
    The Enigma machine was used by Nazi Germany during WWII.
    It was broken by Polish mathematicians (Rejewski, Różycki, Zygalski)
    and later by Alan Turing's team at Bletchley Park.

Machine architecture (simplified, 3-rotor Wehrmacht/Luftwaffe model):
    Keyboard → Plugboard → Rotor III → Rotor II → Rotor I → Reflector
                                                               ↓
    Lamp     ← Plugboard ← Rotor III ← Rotor II ← Rotor I ←────┘

Key insight: the circuit is SYMMETRIC — encrypting twice gives back the original.
    encrypt(encrypt(plaintext, key), key) == plaintext

Key space (why brute force is infeasible):
    Rotor selection (5 rotors, choose 3, ordered)  :   60
    Rotor starting positions                       :   $$26^3 = 17 576$$
    Ring settings (Ringstellung)                   :   $$26^3 = 17 576$$
    Plugboard (10 pairs from 26 letters)           :   $$≈ 1.5 × 10^{14}$$
    ─────────────────────────────────────────────────────────────────────
    Total                                          :   $$≈ 10^{18}$ combinations
"""

# ---------------------------------------------------------------------------
# Historical rotor wirings (Wehrmacht/Luftwaffe Enigma I)
# Each string represents the substitution wiring from A–Z.
# E.g., ROTOR_I[0] = 'E' means signal at position A exits at E.
# The second element is the turnover notch letter.
# ---------------------------------------------------------------------------

ROTOR_WIRINGS = {
    "I":   ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II":  ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV":  ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V":   ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
}

REFLECTORS = {
    "B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",  # Reflector B (most common)
    "C": "FVPJIAOYEDRZXWGCTKUQSBNMHL",  # Reflector C
}

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def char_to_idx(c: str) -> int:
    return ord(c.upper()) - ord('A')

def idx_to_char(i: int) -> str:
    return ALPHABET[i % 26]


# ---------------------------------------------------------------------------
# Plugboard (Steckerbrett)
# ---------------------------------------------------------------------------

class Plugboard:
    """
    Swaps pairs of letters before and after the rotor assembly.
    Example: pairs = [('A','Z'), ('B','Y')] swaps A<->Z and B<->Y.
    Historically, operators used 10 pairs. More pairs = vastly larger key space.
    Letters not in any pair pass through unchanged (identity).
    """

    def __init__(self, pairs: list[tuple[str, str]] = None):
        self.wiring = list(ALPHABET)          # identity mapping by default
        if pairs:
            used = set()
            for a, b in pairs:
                a, b = a.upper(), b.upper()
                if a == b:
                    raise ValueError(f"Cannot connect a letter to itself: {a}")
                if a in used or b in used:
                    raise ValueError(f"Letter already used in plugboard: {a} or {b}")
                used.update([a, b])
                self.wiring[char_to_idx(a)] = b
                self.wiring[char_to_idx(b)] = a

    def forward(self, c: str) -> str:
        return self.wiring[char_to_idx(c)]


# ---------------------------------------------------------------------------
# Rotor
# ---------------------------------------------------------------------------

class Rotor:
    """
    A single Enigma rotor.

    Attributes:
        wiring   : substitution alphabet (right-to-left direction)
        notch    : position letter that triggers the NEXT rotor to step
        position : current letter shown in the window (0 = A ... 25 = Z)
        ring     : Ringstellung offset -- shifts the wiring relative to the
                   alphabet without changing the visible window letter.
                   This adds 26 extra values per rotor to the key space.
    """

    def __init__(self, name: str, position: str = 'A', ring: str = 'A'):
        wiring, notch = ROTOR_WIRINGS[name]
        self.name     = name
        self.wiring   = wiring
        self.reverse  = self._invert(wiring)
        self.notch    = notch
        self.position = char_to_idx(position)
        self.ring     = char_to_idx(ring)

    @staticmethod
    def _invert(wiring: str) -> str:
        """Compute the inverse of a substitution wiring."""
        inv = [''] * 26
        for i, c in enumerate(wiring):
            inv[char_to_idx(c)] = ALPHABET[i]
        return ''.join(inv)

    def is_at_notch(self) -> bool:
        """True when this rotor notch is active -- triggers the next rotor to step."""
        return ALPHABET[self.position] == self.notch

    def step(self):
        """Advance this rotor by one position."""
        self.position = (self.position + 1) % 26

    def _encode(self, wiring: str, signal: int) -> int:
        """
        Pass an electrical signal through the wiring.
        The offset = (position - ring) accounts for the rotor's current orientation.
        """
        offset      = self.position - self.ring
        shifted_in  = (signal + offset) % 26
        output_char = wiring[shifted_in]
        shifted_out = (char_to_idx(output_char) - offset) % 26
        return shifted_out

    def forward(self, signal: int) -> int:
        """Signal entering from the right (keyboard side)."""
        return self._encode(self.wiring, signal)

    def backward(self, signal: int) -> int:
        """Signal returning from the left (reflector side)."""
        return self._encode(self.reverse, signal)


# ---------------------------------------------------------------------------
# Reflector (Umkehrwalze)
# ---------------------------------------------------------------------------

class Reflector:
    """
    Reflects the signal back through the rotors.
    Fixed, self-reciprocal wiring -- no stepping mechanism.

    This component has two important consequences:
      1. The machine is symmetric: decryption == encryption.
      2. A letter can NEVER encrypt to itself -- a structural weakness
         that cryptanalysts exploited to break the machine.
    """

    def __init__(self, name: str = "B"):
        self.wiring = REFLECTORS[name]

    def reflect(self, signal: int) -> int:
        return char_to_idx(self.wiring[signal])


# ---------------------------------------------------------------------------
# The Enigma Machine
# ---------------------------------------------------------------------------

class EnigmaMachine:
    """
    Assembles all components into a working Enigma machine.

    Parameters
    ----------
    rotor_names   : list of 3 rotor IDs in LEFT -> RIGHT order, e.g. ["I","II","III"]
    positions     : initial window letters, one per rotor, e.g. ['A','B','C']
    ring_settings : Ringstellung letters, one per rotor, e.g. ['A','A','A']
    plugboard     : list of letter-pair tuples, e.g. [('A','Z'), ('B','Y')]
    reflector     : reflector name, 'B' or 'C'

    Example
    -------
        enigma = EnigmaMachine(
            rotor_names   = ["I", "II", "III"],
            positions     = ['A', 'B', 'C'],
            ring_settings = ['D', 'F', 'G'],
            plugboard     = [('A','Z'), ('B','Y'), ('C','X')],
            reflector     = "B",
        )
        ciphertext = enigma.encrypt("HELLO WORLD")
    """

    def __init__(
        self,
        rotor_names   : list[str]              = ["I", "II", "III"],
        positions     : list[str]              = ['A', 'A', 'A'],
        ring_settings : list[str]              = ['A', 'A', 'A'],
        plugboard     : list[tuple[str, str]]  = None,
        reflector     : str                    = "B",
    ):
        if len(rotor_names) != 3:
            raise ValueError("Exactly 3 rotors are required.")
        self.rotors    = [Rotor(n, p, r)
                          for n, p, r in zip(rotor_names, positions, ring_settings)]
        self.plugboard = Plugboard(plugboard or [])
        self.reflector = Reflector(reflector)

    def _step_rotors(self):
        """
        Implement the double-stepping anomaly of the Enigma mechanism.

        Normal stepping:
            - The rightmost rotor steps on EVERY keypress.
            - The middle rotor steps when the right rotor is at its notch.
            - The left   rotor steps when the middle rotor is at its notch.

        Double-stepping anomaly:
            If the middle rotor is already at its own notch, it steps AGAIN
            on the next keypress (together with the left rotor). This is a
            mechanical quirk of the ratchet-and-pawl system absent in
            most simplified implementations.
        """
        left, mid, right = self.rotors

        if mid.is_at_notch():       # double-step: mid and left both advance
            mid.step()
            left.step()
        elif right.is_at_notch():   # normal: only mid advances
            mid.step()

        right.step()                # rightmost always steps

    def _encrypt_char(self, c: str) -> str:
        """Encrypt a single character through the full Enigma circuit."""
        # 1. Step rotors BEFORE encoding (the keypress triggers the mechanism)
        self._step_rotors()

        # 2. Plugboard -- forward
        signal = char_to_idx(self.plugboard.forward(c))

        # 3. Rotors -- right to left
        for rotor in reversed(self.rotors):
            signal = rotor.forward(signal)

        # 4. Reflector
        signal = self.reflector.reflect(signal)

        # 5. Rotors -- left to right (inverse direction)
        for rotor in self.rotors:
            signal = rotor.backward(signal)

        # 6. Plugboard -- backward (symmetric: same swap table)
        return self.plugboard.forward(idx_to_char(signal))

    def encrypt(self, text: str) -> str:
        """
        Encrypt (or decrypt -- it is the same operation!) a string.
        Non-alphabetic characters are preserved unchanged.
        """
        result = []
        for char in text.upper():
            if char.isalpha():
                result.append(self._encrypt_char(char))
            else:
                result.append(char)
        return ''.join(result)

    def reset(self, positions: list[str]):
        """Reset rotor positions to new window letters, keeping all other settings."""
        for rotor, pos in zip(self.rotors, positions):
            rotor.position = char_to_idx(pos)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # Full key: rotor selection, positions, ring settings, and plugboard
    # are all part of the secret configuration.
    SETTINGS = dict(
        rotor_names   = ["III", "IV", "II"],
        positions     = ['G', 'T', 'N'],
        ring_settings = ['C', 'H', 'F'],
        plugboard     = [
            ('A', 'Z'), ('B', 'X'), ('C', 'W'),
            ('D', 'V'), ('E', 'U'), ('F', 'T'),
            ('G', 'S'), ('H', 'R'), ('I', 'Q'),
            ('J', 'P'),
        ],  # 10 pairs -> ~1.5 x 10^14 plugboard configurations alone
        reflector     = "B",
    )

    plaintext  = "ATTACK AT DAWN"
    start_pos  = ['G', 'T', 'N']

    enigma = EnigmaMachine(**SETTINGS)
    ciphertext = enigma.encrypt(plaintext)

    # Reset to the same starting position and decrypt
    enigma.reset(start_pos)
    decrypted = enigma.encrypt(ciphertext)

    print("=" * 50)
    print(f"  Plaintext  : {plaintext}")
    print(f"  Ciphertext : {ciphertext}")
    print(f"  Decrypted  : {decrypted}")
    print("=" * 50)
