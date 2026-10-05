# Project Report: Design and Verification of a Smart Keypad Lock Using Deterministic Finite Automata

**Course:** Formal Languages and Automata Theory (FLAT)  
**Topic:** Deterministic Finite Automata (DFA) Construction and String Matching  
**Student/Author:** jagadeesh177  

---

## 1. Abstract

This project investigates the modeling and implementation of an electronic digital keypad lock using Deterministic Finite Automata (DFA). Digital locks must disengage whenever the trailing sequence of entered keys matches a preset secret passcode. A common naive design that resets to state 0 on any mismatched key suffers from a critical vulnerability: it fails on overlapping subpatterns (such as input `121213` for secret code `1213`). By formalizing pattern matching as a Deterministic Finite Automaton $M = (Q, \Sigma, \delta, q_0, F)$ over the alphabet of numeric digits, we derive a transition function that preserves the longest matching prefix of the passcode present in the trailing input stream. We verify the automaton through both a terminal command-line interface and a lightweight web dashboard built with Python's standard library, confirming correct state transitions across all valid and invalid sequences without third-party dependencies.

---

## 2. Introduction & Problem Statement

Electronic keypad locks are common embedded systems found in security access control, safes, and digital doors. The operational requirement for such locks is **continuous sliding-window pattern recognition**:
* The user may press any sequence of keys.
* At the moment the trailing $k$ keys match the secret passcode of length $k$, the lock must open.
* Erroneous key presses entered prior to the passcode must not prevent the lock from opening once the correct sequence is completed.

### 2.1 The Greedy Memoryless Reset Flaw

A straightforward software implementation tracks how many consecutive correct digits have been entered:
1. Initialize matched count $s = 0$.
2. For each key press $x$:
   * If $x$ matches the next character of the code, increment $s \leftarrow s + 1$.
   * If $x$ mismatches, reset $s \leftarrow 0$ (or $1$ if $x$ matches the first character).
3. Open the lock when $s = k$.

Although this logic works for isolated attempts, it fails when an input sequence contains overlapping prefixes. Consider target code $P = 1213$ and key sequence $W = 121213$:
* Keystrokes $1, 2, 1$ advance state to $3$ (matching prefix `121`).
* The fourth key is $2$, which does not match the expected next digit $P[3] = 3$.
* The naive algorithm resets to state $0$.
* The final keys $1, 3$ advance state to $2$. The lock remains shut.

However, the trailing 4 digits of $W$ are $1213$, exactly matching the secret code. The naive implementation failed because it discarded the fact that the trailing substring `12` was already a valid prefix of $P$.

---

## 3. Formal Automata Formulation

To resolve this issue, the lock is modeled as a Deterministic Finite Automaton:
$$M = (Q, \Sigma, \delta, q_0, F)$$

### 3.1 5-Tuple Definition

1. **Alphabet ($\Sigma$):**  
   $\Sigma = \{0, 1, 2, 3, 4, 5, 6, 7, 8, 9\}$ with $|\Sigma| = 10$.

2. **State Set ($Q$):**  
   For a secret code $P = p_0 p_1 \dots p_{k-1}$ of length $k$:  
   $Q = \{0, 1, 2, \dots, k\}$.  
   State $i \in Q$ represents the invariant:  
   *"The longest suffix of the keys typed so far that matches a prefix of $P$ has length $i$."*

3. **Start State ($q_0$):**  
   $q_0 = 0$, representing no matched prefix.

4. **Accepting State Set ($F$):**  
   $F = \{k\}$, representing complete recognition of the passcode.

5. **Transition Function ($\delta$):**  
   $\delta: Q \times \Sigma \to Q$ is defined by:
   $$\delta(q, a) = \max \{ j \le k \mid P[0 \dots j-1] \text{ is a suffix of } (P[0 \dots q-1] \cdot a) \}$$

---

## 4. Transition Function Derivation & Table Construction

### 4.1 Suffix Preservation Rule

For any state $q \in Q$ and input symbol $a \in \Sigma$:
1. Construct the candidate string $T = P[0 \dots q-1] \cdot a$. (If $q = k$, shift the window to $T = P[1 \dots k-1] \cdot a$ to support continuous recognition).
2. Find the largest integer $j \in \{0, \dots, k\}$ such that the prefix $P[0 \dots j-1]$ equals the suffix of $T$ of length $j$.
3. Set $\delta(q, a) = j$.

### 4.2 Transition Table for Passcode `1213`

Applying the definition to $P = 1213$ ($k = 4$):

| State ($q$) | Meaning | Key `1` | Key `2` | Key `3` | Other Key |
|:---:|:---|:---:|:---:|:---:|:---:|
| 0 | start (no match) | 1 | 0 | 0 | 0 |
| 1 | matched `1` | 1 | 2 | 0 | 0 |
| 2 | matched `12` | 3 | 0 | 0 | 0 |
| 3 | matched `121` | 1 | **2** | 4 | 0 |
| [F] 4 | matched `1213` (OPEN) | 1 | 0 | 0 | 0 |

#### Key Observation at State 3:
At state 3 (representing string `121`), on input symbol `2`:
* $T = \text{"121"} \cdot \text{"2"} = \text{"1212"}$.
* Testing prefixes of $P = \text{"1213"}$:
  * Length 4: `1213` $\ne$ `1212`
  * Length 3: `121` $\ne$ `212`
  * Length 2: `12` $=$ `12` (Match!)
* Therefore, $\delta(3, \text{'2'}) = 2$.
Rather than resetting to 0, the DFA transitions to state 2, preserving the partial match `12`.

---

## 5. Experimental Results & Comparative Evaluation

### 5.1 Verification Test Cases

The implementation was tested across standard and adversarial input sequences:

| Test Sequence | Contains `1213`? | Naive Lock | DFA Lock | Result Analysis |
|:---|:---:|:---:|:---:|:---|
| `1213` | Yes | Opens | Opens | Baseline correct sequence |
| `991213` | Yes | Opens | Opens | Leading erroneous keystrokes ignored |
| `121213` | Yes | Stays shut | Opens | Overlapping pattern; naive lock fails |
| `112131213` | Yes | Opens | Opens | Consecutive valid sequences |
| `1212` | No | Stays shut | Stays shut | Incomplete prefix correctly rejected |
| `4213` | No | Stays shut | Stays shut | Incorrect digits correctly rejected |

### 5.2 Step-by-Step Trace of the Overlapping Sequence (`121213`)

| Step | Key Pressed | DFA State Transition | DFA Matched Suffix | Naive State Transition |
|:---:|:---:|:---:|:---:|:---:|
| 0 | (start) | 0 | $\varepsilon$ | 0 |
| 1 | `1` | $0 \to 1$ | `1` | $0 \to 1$ |
| 2 | `2` | $1 \to 2$ | `12` | $1 \to 2$ |
| 3 | `1` | $2 \to 3$ | `121` | $2 \to 3$ |
| 4 | `2` | $3 \to \mathbf{2}$ | `12` (preserved!) | $3 \to \mathbf{0}$ (reset!) |
| 5 | `1` | $2 \to 3$ | `121` | $0 \to 1$ |
| 6 | `3` | $3 \to \mathbf{4}$ | `1213` (**OPEN**) | $1 \to \mathbf{0}$ (**SHUT**) |

---

## 6. System Architecture & Implementation

The project is implemented in pure Python using standard library modules only:

1. **`main.py`:**
   * `build_dfa(code)`: Constructs transition table $\delta(q, a)$.
   * `run_dfa(table, code, keys)`: Traces DFA execution and checks acceptance.
   * `run_naive(code, keys)`: Simulates the greedy reset lock for comparison.
   * Command-line interface with argument parsing (`--code`, `--keys`, `--interactive`).

2. **`app.py`:**
   * Lightweight HTTP server using `http.server.HTTPServer` and `BaseHTTPRequestHandler`.
   * Serves static HTML and JSON endpoints (`/dfa` and `/run`).

3. **`index.html`:**
   * Interactive keypad with mouse and keyboard input handling.
   * Real-time dual lock display comparing DFA and naive lock states.
   * Dynamic SVG state transition diagram highlighting active states and transitions.
   * Synchronized transition table highlighting active rows.

---

## 7. Conclusion

By modeling the digital keypad lock as a Deterministic Finite Automaton, this project demonstrates how theoretical automata concepts directly solve practical engineering bugs. The DFA provides deterministic $O(1)$ state transitions per keystroke while guaranteeing complete suffix preservation. The project demonstrates the utility of Formal Languages and Automata Theory in software reliability, verification, and embedded system design.

---

## 8. References

1. Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006). *Introduction to Automata Theory, Languages, and Computation* (3rd ed.). Pearson/Addison-Wesley.
2. Sipser, M. (2012). *Introduction to the Theory of Computation* (3rd ed.). Cengage Learning.
3. Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to Algorithms* (4th ed.). MIT Press. (Chapter 32: String Matching with Automata).
