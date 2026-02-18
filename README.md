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