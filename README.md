# Enigma Machine in Python

A didactic Python implementation of the **Enigma machine** for use in cryptography courses. The codebase is intentionally kept small and readable: every component maps directly to a physical part of the historical machine, and every design decision is explained in the source comments.

This repository is structured as a self-contained learning environment:

- A faithful, well-documented implementation of the Wehrmacht/Luftwaffe Enigma I
- Runnable examples showing encryption, decryption, and key configuration
- A ready-to-use cryptanalysis challenge for student assessment

## Repository layout

```
enigma-classroom/
├── enigma.py                    # Core machine implementation
├── examples/
│   └── demo.py                  # Usage examples (encrypt, decrypt, custom keys)
├── docs/
│   └── enigma_architecture.md   # Deep-dive on machine internals
│   └── sample_challenge.md      # Student cryptanalysis challenge (coursework)
├── .gitignore
├── LICENSE                      # Apache License 2.0
└── README.md
```

## Quick start

No dependencies beyond the Python standard library are required.

```bash
git clone https://github.com/angelborroy/enigma-classroom.git
cd enigma-classroom
python enigma.py            # runs the built-in demo
python examples/demo.py     # extended usage examples
```

## Machine architecture

```
Keyboard → Plugboard → Rotor R → Rotor M → Rotor L → Reflector
                                                          ↓
Lamp     ← Plugboard ← Rotor R ← Rotor M ← Rotor L ←──────┘
```

The signal travels right-to-left through three rotors, bounces off the reflector, and returns left-to-right through the same rotors. This symmetric design means that *encryption and decryption are the same operation*, provided the machine is reset to the same starting position.

### Key components

| Component | Class | Role |
|---|---|---|
| Plugboard (*Steckerbrett*) | `Plugboard` | Swaps up to 13 letter pairs before and after the rotors |
| Rotor (*Walze*) | `Rotor` | Stepping substitution cipher; advances on every keypress |
| Reflector (*Umkehrwalze*) | `Reflector` | Fixed self-reciprocal wiring; makes the circuit symmetric |
| Machine | `EnigmaMachine` | Orchestrates stepping (incl. double-step) and signal routing |

### Key space

| Parameter | Options | Combinations |
|---|---|---|
| Rotor selection & order (choose 3 from 5) | — | 60 |
| Starting positions | A–Z per rotor | $$26^3 = 17 576$$ |
| Ring settings | A–Z per rotor | $$26^3 = 17 576$$ |
| Plugboard (10 pairs) | — | $$≈ 1.5 × 10^{14}$$ |
| Reflector choice | B or C | 2 |
| **Total** | | **$$≈ 10^{18}$$** |

## Usage

### Basic encryption / decryption

```python
from enigma import EnigmaMachine

enigma = EnigmaMachine(
    rotor_names   = ["I", "II", "III"],   # left -> right
    positions     = ['A', 'B', 'C'],
    ring_settings = ['A', 'A', 'A'],
    plugboard     = [('A', 'Z'), ('B', 'Y')],
    reflector     = "B",
)

ciphertext = enigma.encrypt("HELLO WORLD")

# Reset to the same starting position and decrypt
enigma.reset(['A', 'B', 'C'])
plaintext = enigma.encrypt(ciphertext)
```

### Available rotors and reflectors

Rotors: `I`, `II`, `III`, `IV`, `V`  
Reflectors: `B`, `C`

All wiring data is taken from the historical Wehrmacht/Luftwaffe Enigma I specification.

## Cryptanalysis workshop — breaking the challenge

`enigma_solver.py` is a guided starting point for solving the cryptanalysis
challenge in [`docs/sample_challenge.md`](docs/sample_challenge.md).
It implements the three-phase crib attack that Bletchley Park pioneered,
using `enigma.py` from this repository.

### How the attack works

A **crib** is a fragment of known (or strongly guessed) plaintext.
Because the first word of the intercepted message is `WEATHER`, each
ciphertext letter at that position satisfies the equation

```
stecker[ c_i ]  =  C_i( stecker[ p_i ] )
```

where `C_i` is the rotor core at offset *i* and `stecker` is the plugboard.
Seven such equations over-constrain the plugboard enough that almost every
offset triple can be discarded in microseconds via backtracking.

| Phase | What it does | Key technique |
|-------|-------------|---------------|
| **0** | Pre-compute all 17,576 rotor cores (no plugboard, ring = AAA) | Indexed lookup table |
| **1** | For each offset triple, solve the 7 crib equations | Constraint backtracking |
| **2** | Decrypt the message prefix; keep candidates that look like English | Dictionary filter |
| **3** | Complete the plugboard; rank survivors | N-gram scoring |

### Getting started

No installation required. Copy `enigma_solver.py` into the repository root
alongside `enigma.py` and run it:

```bash
git clone https://github.com/angelborroy/enigma-python.git
cd enigma-python
python enigma_solver.py
```

The script will immediately pre-compute the core table (Phase 0) and then
stop with a `NotImplementedError` at the first function you need to write.

### Repository layout (updated)

```
enigma-python/
├── enigma.py                    # Core machine implementation
├── enigma_solver.py             # << Crib-attack skeleton (start here)
├── examples/
│   └── demo.py                  # Usage examples (encrypt, decrypt, custom keys)
├── docs/
│   ├── enigma_architecture.md   # Deep-dive on machine internals
│   └── sample_challenge.md      # Cryptanalysis challenge (the ciphertext to crack)
├── .gitignore
├── LICENSE
└── README.md
```

### What you need to implement

The skeleton runs out of the box and fails at the first incomplete function.
Work through the `TODO` markers in order:

| # | Function | Difficulty | Concept practised |
|---|----------|-----------|-------------------|
| 1 | `assign(a, b)` inside `solve_plugboard` | ★☆☆ | Plugboard as involution |
| 2 | `looks_like_english()` | ★☆☆ | Heuristic language detection |
| 3 | `build_core_table()` with real ring settings | ★★☆ | Effective offset = position − ring |
| 4 | Correct rotor stepping inside `phase1()` | ★★☆ | Double-stepping anomaly |
| 5 | `complete_plugboard()` with hill-climbing | ★★★ | Local-search optimisation |
| 6 | `ngram_score()` with real log-probabilities | ★★★ | Statistical language modelling |

> **Tip — start small.** Implement `assign()` first (10 lines).
> Once Phase 1 produces candidates, move to Phase 2, and so on.
> Each phase is independently testable.

### Verifying your solution

When the correct key is recovered, re-encrypting the recovered plaintext
must reproduce the original ciphertext exactly:

```python
from enigma import EnigmaMachine

machine = EnigmaMachine(
    rotor_names   = ["I", "IV", "III"],
    positions     = [...],        # recovered positions
    ring_settings = [...],        # recovered ring settings
    plugboard     = [...],        # recovered plugboard pairs
    reflector     = "B",
)
plaintext  = machine.encrypt(CIPHERTEXT)
machine.reset([...])              # same positions
assert machine.encrypt(plaintext) == CIPHERTEXT
print(plaintext)                  # WEATHER ...
```