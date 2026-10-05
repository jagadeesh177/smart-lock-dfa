# Smart Lock DFA (Formal Languages and Automata Theory)

**Subject:** Formal Languages and Automata Theory (FLAT)  
**Topics:** Deterministic Finite Automata (DFA), Pattern Matching, Suffix Transitions  

---

## Problem Statement

A digital keypad lock must open as soon as the **trailing sequence of entered keys matches the secret code**, even if incorrect keys were pressed earlier.

A common naive implementation increments a match counter on each correct key and **restarts from state 0 on any wrong key**. While this appears functional on simple inputs, it contains a critical flaw when handling overlapping patterns.

For example, with secret code **1213**, typing **1 2 1 2 1 3** ends with the target sequence `1213`, so the lock should open. However, the naive lock **stays shut**:
1. Keys `1, 2, 1` reach state 3 (matching `121`).
2. The fourth key (`2`) mismatches the expected digit `3`.
3. The naive lock resets to state 0, discarding the fact that the trailing `1 2` is already a valid beginning of the code.

**Objective:** Build the keypad lock as a **Deterministic Finite Automaton (DFA)** that tracks partial prefix matches via suffix preservation and always opens at the earliest valid moment.

---

## DFA Specification

The lock is formally defined as a 5-tuple $M = (Q, \Sigma, \delta, q_0, F)$:

| Component | Description |
|---|---|
| **Alphabet ($\Sigma$)** | Numeric keys $\{0, 1, 2, 3, 4, 5, 6, 7, 8, 9\}$ |
| **States ($Q$)** | $\{0, 1, \dots, k\}$, where $k = \text{len}(\text{code})$. State $i$ represents: "the longest suffix of keys typed matching a prefix of the code has length $i$" |
| **Start State ($q_0$)** | $0$ (no matching prefix) |
| **Accepting State ($F$)** | $\{k\}$ (full passcode recognized -> lock opens) |
| **Transition Function ($\delta$)** | $\delta(q, a)$ takes prefix $P[0:q] \cdot a$ and transitions to the length of the longest prefix of $P$ that is also a suffix of $P[0:q] \cdot a$ |

### Transition Table for Code `1213`

| State | Meaning | Key 1 | Key 2 | Key 3 | Other Key |
|:---:|:---|:---:|:---:|:---:|:---:|
| 0 | start (0) | 1 | 0 | 0 | 0 |
| 1 | matched '1' | 1 | 2 | 0 | 0 |
| 2 | matched '12' | 3 | 0 | 0 | 0 |
| 3 | matched '121' | 1 | **2** | 4 | 0 |
| [F] 4 | matched '1213' (OPEN) | 1 | 0 | 0 | 0 |

*Note:* In state 3 (`121`), an input of `2` does not reset to 0. It falls back to state 2 because the trailing sequence `12` is a valid prefix of the code. State 4 is the accepting state (`[F]`).

---

## Experimental Results

Output comparison from `python main.py`:

| Keys Pressed | Should Open? | Naive Lock | DFA Lock | Status |
|:---|:---:|:---:|:---:|:---|
| 1213 | Yes | Opens | Opens | Matches expected |
| 991213 | Yes | Opens | Opens | Matches expected |
| **121213** | **Yes** | **Stays shut** | **Opens** | **Naive lock failed (bug)** |
| 112131213 | Yes | Opens | Opens | Matches expected |
| 1212 | No | Stays shut | Stays shut | Matches expected |
| 4213 | No | Stays shut | Stays shut | Matches expected |

### State Transition Trace for `121213`:
```
DFA states  : 0 -> 1 -> 2 -> 3 -> 2 -> 3 -> 4  (Opens successfully)
Naive states: 0 -> 1 -> 2 -> 3 -> 0 -> 1 -> 0  (Misses match due to greedy reset)
```

---

## How to Run

The project requires Python 3 with no third-party dependencies (standard library only).

### 1. Web Dashboard
Start the local HTTP server:
```bash
python app.py
```
Open your browser at **http://localhost:8002**.
* Interactive on-screen keypad and keyboard shortcuts (0-9, Backspace, Escape).
* Dynamic SVG state transition diagram highlighting the current state.
* Real-time side-by-side execution trace for both locks.
* "Simulate Overlapping Sequence" button to test the `121213` scenario.

Optional arguments:
```bash
python app.py --port 8080
```

### 2. Terminal Mode
Run the default verification and demonstration:
```bash
python main.py
```

Evaluate a specific code and input sequence:
```bash
python main.py --code 1213 --keys 121213
```

Launch the interactive keypad in the terminal:
```bash
python main.py --interactive
```

---

## Project Structure

| File | Description |
|---|---|
| `main.py` | DFA construction, execution simulation, naive lock comparison, and CLI |
| `app.py` | Built-in HTTP server exposing REST endpoints for the web interface |
| `index.html` | Web interface featuring keypad, SVG state diagram, and dual lock comparison |
| `PROJECT_REPORT.md` | Formal academic project report covering theory, derivations, and analysis |
| `README.md` | Project overview, setup, and usage documentation |
