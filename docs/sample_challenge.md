# Enigma Challenge

## Background

The *Enigma machine* is a rotor-based electromechanical cipher device used by Nazi Germany during World War II. Its security rested not on a secret algorithm, but on a *secret key*: the daily configuration of rotors, ring settings, starting positions, and plugboard connections.

You are provided with a Python implementation of the Enigma machine (`enigma.py`) and an intercepted ciphertext. Your task is to *recover the plaintext* by finding the unknown parts of the key configuration.

This is not a brute-force exercise. The combined key space is far too large for exhaustive search. You must apply cryptanalytic techniques to decompose the problem into tractable sub-problems and solve them in sequence.

## Known machine settings

| Parameter               | Value                                      |
| ----------------------- | ------------------------------------------ |
| Rotor selection & order | `I` (left) · `IV` (middle) · `III` (right) |
| Reflector               | `B`                                        |

## Unknown parameters

| Parameter                    | Notes                |
| ---------------------------- | -------------------- |
| Initial rotor positions      | 3 letters (A–Z each) |
| Ring settings (Ringstellung) | 3 letters (A–Z each) |
| Plugboard pairs              | Exactly 7 pairs      |

> Important: Ring settings are *not* trivially AAA. Positions and ring settings interact: you must account for this in your analysis.

## Intercepted ciphertext

```
VVNAMHJ QCZHTK UTF QVV LQSXA NXDWYXHO GLWTHY HUOFB KPEIBBK OGXOC
KJQSSDAZJM BH JQM YOUD QAYGP WKM IBNCH HWV YAQPOSJ MBJHDBXTDO XWQN
QEKCG JFKREX YWSSX XAGC MZR SIDSKYWIF XVFQ NCY PLQAU PDY ZLRTICO PSBA
DLDZBV UDMOBR RUMTKYFAQYS KWX CWTTDC SUVWMUYA GI MYBTWQZ ZXJUCCVJF EZ
PUONV TZAZUUK
```

Spaces reflect original word boundaries and are not encrypted.

## Structural Hint (Crib)

The **first** word of the plaintext is **`WEATHER`**.

This crib is at a known position (the very beginning of the message).
Use it carefully: Enigma never encrypts a letter to itself.

## The plaintext

The intercepted message is written in **English**. It contains no digits or punctuation, only letters and the spaces visible above. The content is a routine military communication; it does not concern cryptography or the Enigma machine itself.

## What you may use

* The provided `enigma.py`: import and use it directly in your attack script (`from enigma import EnigmaMachine`)
* Any Python standard-library module
* Third-party packages (`numpy`, `scipy`, etc.) are permitted as utilities

*The original Enigma was not broken by computing power alone. It was broken by careful reasoning about the machine structural weaknesses. Your approach should reflect the same principle.*
