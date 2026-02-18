# Automata Playground — Interactive Automata Simulator

An interactive **Python GUI application** for visualizing and simulating fundamental models of computation: **DFA, NFA, ε-NFA, PDA, and Turing Machines**.

This tool provides a visual state diagram + execution trace to help understand how automata process an input string and decide **ACCEPT / REJECT**.

---

## Features

- Tkinter-based GUI (clean layout + responsive canvas)
- Machine selector + input box + sample inputs
- Transition table view for the selected machine
- Detailed step-by-step execution trace
- Visual diagram with highlighted final/active states
- “Maximize Diagram” full-view popup

---

## Supported Machines

### 1) DFA — Even number of `0`s
- Alphabet: `{0, 1}`
- Accepts strings with an even count of `0`

### 2) NFA — Ends with `ab`
- Alphabet: `{a, b}`
- Accepts strings that end with `ab`

### 3) ε-NFA — `(a|b)*abb`
- Alphabet: `{a, b}` with epsilon transitions
- Shows ε-closure logic

### 4) PDA — `a^n b^n`
- Alphabet: `{a, b}`
- Pushes for each `a`, pops for each `b`

### 5) TM — `a^n b^n c^n`
- Alphabet: `{a, b, c}` (with marked symbols + blank)
- Uses tape marking and head movement to validate equal counts

---

## Requirements

- Python 3.x
- Tkinter (usually included with Python on Windows)

> If you see `ModuleNotFoundError: No module named 'tkinter'`, reinstall Python and enable **tcl/tk and IDLE** during setup.

---

## How to Run

### Option A: Run locally (recommended)

```bash
git clone https://github.com/SaiPriyaRamini/Computation.git
cd Computation
python computation.py
