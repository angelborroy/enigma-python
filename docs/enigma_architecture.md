# Enigma Machine — Architecture Deep-Dive

This document explains how the Enigma machine works at the component level, how the Python implementation models each part, and what the key cryptographic properties are.

## 1. Physical overview

The Enigma machine is an electromechanical substitution cipher. When an operator presses a key, a small electrical current flows from the battery through a fixed path:

```
Battery → Keyboard → Plugboard → Entry wheel → Rotor R → Rotor M → Rotor L
       → Reflector → Rotor L (reverse) → Rotor M (reverse) → Rotor R (reverse)
       → Entry wheel (reverse) → Plugboard (reverse) → Lamp panel
```

The lamp that lights up shows the encrypted letter. Because the circuit is built symmetrically, running it backwards (i.e., starting with the ciphertext letter) produces the plaintext letter. Encryption and decryption are the same operation, provided the machine is set to the same starting position.

## 2. Components

### 2.1 Plugboard (*Steckerbrett*)

The plugboard sits between the keyboard/lamp panel and the entry wheel. It contains 26 sockets, one per letter. Short cables connect pairs of sockets, swapping those letters before and after the rotor assembly.

- Historically, 10 pairs were connected; some settings used fewer
- Letters not connected to any cable pass through unchanged (identity)
- The same swap is applied on both the forward and backward passes

Key space contribution:
The number of ways to choose `k` unordered pairs from 26 letters for k = 10 is 1.5 * $$10^{14}$$. This is the dominant factor in Enigma key space.

In the code `class Plugboard` is the wiring that is stored as a list of 26 characters. `forward(c)` performs the swap in O(1).

### 2.2 Rotors (*Walzen*)

Each rotor is a disc with 26 electrical contacts on each face, connected by internal wiring in a fixed permutation. The rotor substitutes each input letter with a different output letter, and steps forward (rotating one position) before each keypress.

Five rotors were available for Wehrmacht/Luftwaffe Enigma (designated I–V), of which three were chosen and ordered for each message.

Wiring direction: The rotor is traversed twice per keypress: right-to-left on the forward pass, left-to-right on the return. These are inverse permutations of each other.

Offset encoding: When a rotor has stepped, its wiring shifts relative to the alphabet. If a rotor is at position `p` and has ring setting `r`, the effective offset is `(p − r) mod 26`. The signal enters at position `(signal + offset) mod 26`, exits through the wiring, and is shifted back by *−offset*. This is implemented in `Rotor._encode()`.

Turnover notch: Each rotor has a single notch position. When the rotor reaches this position, it triggers the rotor to its left to step on the next keypress (via the pawl-and-ratchet mechanism).

In the code: `class Rotor` stores wiring as a string; inverse computed at initialisation. `forward()` and `backward()` handle the two traversal directions.

### 2.3 Ring settings (*Ringstellung*)

The ring setting shifts the wiring of a rotor relative to its alphabet window without changing the visible position indicator. It adds an additional 26 values per rotor to the key space. With ring settings at A (= 0 offset), positions and ring settings are equivalent.

Key space contribution: $$26^3 = 17 576$$ (combined with starting positions, $$26^6 = 308 915 776$$, but note that only the difference *position − ring* matters, so effectively $$26^3$$ independent values).

### 2.4 Reflector (*Umkehrwalze*)

The reflector is a non-stepping rotor at the left end of the assembly. It uses a *self-reciprocal* permutation: every letter maps to a different letter, and the mapping is its own inverse. This guarantees:

1. The signal always returns through the rotors. There is no way for the current to loop back through the keyboard
2. The full circuit is symmetric: encrypting a ciphertext gives back the plaintext

Critical weakness: Because the reflector wiring contains no fixed points (no letter maps to itself), and the circuit is reversible, *a letter can never encrypt to itself*. This property was exploited in every successful attack on Enigma:

- The Polish *Bomba* used known cribs to infer rotor settings
- Turing *Bombe* used chains of crib-based logical constraints to eliminate plugboard settings
- The no-self-encryption rule allows immediate elimination of any (key, crib offset) pair where `ciphertext[i] == crib[i]`

In the code: `class Reflector` is a fixed 26-character string representing the wiring.

## 3. Stepping mechanism

### 3.1 Normal stepping

Rotors step like an odometer, but triggered by the mechanical movement of the previous rotor pawl catching the next ratchet:

- The rightmost rotor steps on every keypress
- The middle rotor steps when the right rotor moves through its notch position
- The left rotor steps when the middle rotor moves through its notch position

### 3.2 Double-stepping anomaly

A quirk of the ratchet-and-pawl mechanism causes an anomaly: if the *middle rotor is already at its notch position*, pressing a key causes it to step *again* (along with the left rotor). This means the middle rotor steps on two consecutive keypresses when passing through its notch, whereas a pure odometer would step only once.

This is implemented in `EnigmaMachine._step_rotors()`:

```python
if mid.is_at_notch():       # middle at notch : mid AND left step
    mid.step()
    left.step()
elif right.is_at_notch():   # right at notch : mid steps only
    mid.step()
right.step()                # right always steps
```

The double-stepping anomaly is absent from many simplified implementations. It is historically significant because it slightly reduces the effective period of the middle rotor cycle, which was noticed and exploited by cryptanalysts.

## 4. Signal path — worked example

Settings: Rotors I II III, positions AAA, rings AAA, no plugboard, Reflector B.  
Input letter: `A` (index 0).

```
Step 1: Rotors step → right rotor moves from A(0) to B(1)

Step 2: Plugboard forward → A unchanged (no plugboard)

Step 3: Right rotor (Rotor III, position B=1, ring A=0)
    offset    = 1 - 0 = 1
    shifted_in = (0 + 1) % 26 = 1  → look up wiring[1]
    Rotor III wiring: BDFHJLCPRTXVZNYEIWGAKMUSQO
    wiring[1] = 'D' → index 3
    shifted_out = (3 - 1) % 26 = 2  → signal = 2 (C)

Step 4: Middle rotor (Rotor II, position A=0, ring A=0)
    offset = 0; shifted_in = 2
    Rotor II wiring: AJDKSIRUXBLHWTMCQGZNPYFVOE
    wiring[2] = 'D' → index 3
    shifted_out = 3  → signal = 3 (D)

Step 5: Left rotor (Rotor I, position A=0, ring A=0)
    offset = 0; shifted_in = 3
    Rotor I wiring: EKMFLGDQVZNTOWYHXUSPAIBRCJ
    wiring[3] = 'F' → index 5
    shifted_out = 5  → signal = 5 (F)

Step 6: Reflector B: YRUHQSLDPXNGOKMIEBFZCWVJAT
    wiring[5] = 'S' → index 18  → signal = 18 (S)

Step 7–9: Return through rotors (backward direction, inverse wiring)
    ... (computed by Rotor.backward())

Step 10: Plugboard backward → identity

Output: B  (A encrypts to B for this specific step)
```

## 5. Key space summary

| Parameter | Options | Combinations |
|---|---|---|
| Rotor selection & order (choose 3 from 5) | — | 60 |
| Starting positions | A–Z per rotor | $$26^3 = 17 576$$ |
| Ring settings | A–Z per rotor | $$26^3 = 17 576$$ |
| Plugboard (10 pairs) | — | $$≈ 1.5 × 10^{14}$$ |
| Reflector choice | B or C | 2 |
| **Total** | | **$$≈ 10^{18}$$** |

## 6. Known cryptanalytic attacks

| Attack | Who | What it exploits |
|---|---|---|
| Characteristic method | Rejewski (1932) | Repeated message indicator structure |
| Cyclometer / card catalogue | Rejewski (1938) | Rotor wiring recovery from known-plaintext |
| Bombe (Polish) | Rejewski (1938) | Permutation cycles from cribs |
| Bombe (British) | Turing & Welchman (1940) | Crib chaining + diagonal board eliminates plugboard |
| Crib-dragging | General | No-self-encryption eliminates (crib, offset) pairs |
| Index of Coincidence | General | Distinguishes correct from incorrect rotor positions |
| Hill-climbing plugboard | Practical | Greedy/local search over pair swaps |

## 7. Further reading

- Turing, A. (c. 1940). *Treatise on the Enigma* (the "Prof's Book"). Available from the GCHQ declassification, National Archives UK.
- Rejewski, M. (1981). *How Polish Mathematicians Deciphered the Enigma*. Annals of the History of Computing, 3(3).
- Singh, S. (1999). *The Code Book*. Fourth Estate. Chapter 4.
- Bauer, F. L. (2007). *Decrypted Secrets: Methods and Maxims of Cryptology*. Springer. Chapter 13.
- [Crypto Museum — Enigma](https://www.cryptomuseum.com/crypto/enigma/)
- [Bletchley Park Trust](https://bletchleypark.org.uk/)
