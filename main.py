"""
Smart Lock DFA: Keypad Lock Modeled as a Deterministic Finite Automaton
Formal Languages and Automata Theory (FLAT) Project

A digital lock must open as soon as the trailing sequence of entered keys
matches the secret code, even if incorrect keys were typed previously.
This script constructs a DFA that correctly tracks partial matches via
suffix transitions, and compares it against a naive greedy reset lock.

Usage:
  python main.py                       # Run default demonstration
  python main.py --code 1213 --keys 121213
  python main.py --interactive         # Live terminal keypad input
"""

import argparse
import sys

# Input alphabet for digital keypad
ALPHABET = "0123456789"


def build_dfa(code):
    """
    Constructs the transition table for the pattern-matching DFA.

    Formal 5-tuple M = (Q, Sigma, delta, q0, F):
      - Q     = {0, 1, ..., k} where k = len(code).
                State i represents: "the longest suffix of keys typed matching
                a prefix of the code has length i".
      - Sigma = {'0', ..., '9'}.
      - delta(state, key) = length of the longest prefix of `code` that is
                also a suffix of (code[:state] + key).
      - q0    = 0 (no digits matched yet).
      - F     = {k} (full code matched -> lock opens).
    """
    k = len(code)
    table = []

    for state in range(k + 1):
        row = {}
        for key in ALPHABET:
            # If already in the accept state, shift window to continue matching
            if state == k:
                typed = code[1:] + key
            else:
                typed = code[:state] + key

            # Find longest prefix of `code` that matches a suffix of `typed`
            next_state = min(len(typed), k)
            while next_state > 0 and not typed.endswith(code[:next_state]):
                next_state -= 1

            row[key] = next_state
        table.append(row)

    return table


def run_dfa(table, code, keys):
    """
    Simulates the DFA on a sequence of key presses.
    Returns: (list of visited states, boolean indicating if the lock opened).
    """
    state = 0
    path = [0]
    opened = False

    for key in keys:
        if key in table[state]:
            state = table[state][key]
        else:
            state = 0
        path.append(state)
        if state == len(code):
            opened = True

    return path, opened


def run_naive(code, keys):
    """
    Simulates a naive greedy pattern matcher.
    On a matching key, it increments state; on a mismatch, it resets to state 0
    (or state 1 if the mismatching key equals code[0]).

    Flaw: It discards overlapping partial matches. For code '1213' and input
    '121213', mismatching on the fourth key resets state to 0 and misses the lock.
    """
    state = 0
    path = [0]
    opened = False
    k = len(code)

    for key in keys:
        if state < k and key == code[state]:
            state += 1
        else:
            state = 1 if key == code[0] else 0

        path.append(state)
        if state == k:
            opened = True
            state = 0

    return path, opened


# Alias for backward compatibility
run_lazy = run_naive


def ends_with_code(code, keys):
    """Ground truth check: returns True if code appears in keys."""
    return code in keys


def print_table(table, code):
    """Displays the DFA transition table formatted in ASCII."""
    used_keys = sorted(set(code))
    other_keys = [k for k in ALPHABET if k not in code]
    other_key = other_keys[0] if other_keys else None

    header = "  state  meaning          " + "".join(f"key {d}  " for d in used_keys)
    if other_key:
        header += "other key"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for state, row in enumerate(table):
        meaning = f"matched '{code[:state]}'" if state > 0 else "start (0)"
        mark = "[F]" if state == len(code) else "   "
        line = f"  {mark}{state:>2}  {meaning:<15}  "
        line += "".join(f"{row[d]:>5}  " for d in used_keys)
        if other_key:
            line += f"{row[other_key]:>7}"
        print(line)
    print("  ([F] = accepting state: lock opens)")


def print_comparison(table, code, test_cases):
    """Prints side-by-side comparison between naive lock and DFA lock."""
    print(f"  {'Keys Pressed':<16}{'Expected':<12}{'Naive Lock':<14}{'DFA Lock':<12}Status")
    print("  " + "-" * 62)

    for keys in test_cases:
        expected = ends_with_code(code, keys)
        _, naive_open = run_naive(code, keys)
        _, dfa_open = run_dfa(table, code, keys)

        exp_text = "opens" if expected else "stays shut"
        naive_text = "opens" if naive_open else "stays shut"
        dfa_text = "opens" if dfa_open else "stays shut"

        status = ""
        if naive_open != expected:
            status = "<- Naive lock failed (bug)"
        else:
            status = "Matches expected"

        print(f"  {keys:<16}{exp_text:<12}{naive_text:<14}{dfa_text:<12}{status}")


def run_interactive(code):
    """Interactive CLI keypad loop."""
    table = build_dfa(code)
    print(f"\n--- Interactive Keypad Mode (Secret Code: {code}) ---")
    print("Type numeric digits to press keys. Commands: 'c' to clear, 'q' to quit.")

    buffer = ""
    while True:
        try:
            user_input = input(f"\n[Buffer: '{buffer}'] Enter key: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue
        if user_input.lower() == 'q':
            print("Exiting interactive mode.")
            break
        if user_input.lower() == 'c':
            buffer = ""
            print("Buffer cleared.")
            continue

        for ch in user_input:
            if ch in ALPHABET:
                buffer += ch

        dfa_path, dfa_open = run_dfa(table, code, buffer)
        naive_path, naive_open = run_naive(code, buffer)
        expected = ends_with_code(code, buffer)

        print(f"  Buffer       : {buffer}")
        print(f"  DFA trace    : {' -> '.join(map(str, dfa_path))} (Current state: {dfa_path[-1]})")
        print(f"  Naive trace  : {' -> '.join(map(str, naive_path))} (Current state: {naive_path[-1]})")
        print(f"  DFA Lock     : {'OPEN' if dfa_open else 'SHUT'}")
        print(f"  Naive Lock   : {'OPEN' if naive_open else 'SHUT'}")
        if expected and not naive_open:
            print("  Alert: Naive lock failed due to greedy state reset!")


def main():
    parser = argparse.ArgumentParser(
        description="Smart Lock DFA: Keypad lock modeled as a Deterministic Finite Automaton."
    )
    parser.add_argument("--code", type=str, default="1213", help="Secret passcode (default: 1213)")
    parser.add_argument("--keys", type=str, default=None, help="Key sequence to evaluate")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive keypad loop")
    args = parser.parse_args()

    code = args.code
    if not code.isdigit():
        print("Error: code must contain only numeric digits.")
        sys.exit(1)

    table = build_dfa(code)

    if args.interactive:
        run_interactive(code)
        return

    if args.keys is not None:
        keys = args.keys
        expected = ends_with_code(code, keys)
        dfa_path, dfa_open = run_dfa(table, code, keys)
        naive_path, naive_open = run_naive(code, keys)

        print("=" * 64)
        print(f"Evaluation for Code '{code}' and Input '{keys}'")
        print("=" * 64)
        print(f"  DFA States   : {' -> '.join(map(str, dfa_path))}")
        print(f"  Naive States : {' -> '.join(map(str, naive_path))}")
        print(f"  DFA Lock     : {'OPEN' if dfa_open else 'SHUT'}")
        print(f"  Naive Lock   : {'OPEN' if naive_open else 'SHUT'}")
        print(f"  Expected     : {'OPEN' if expected else 'SHUT'}")
        if expected and not naive_open:
            print("  Result       : Naive lock failed; DFA lock succeeded via suffix fallback.")
        return

    # Default demonstration
    print("=" * 64)
    print(f"Smart Lock DFA: Transition Table for Code {code}")
    print("=" * 64)
    print_table(table, code)

    print("\n" + "=" * 64)
    print("Comparative Evaluation: DFA Lock vs Naive Lock")
    print("=" * 64)
    tests = ["1213", "991213", "121213", "112131213", "1212", "4213"]
    print_comparison(table, code, tests)

    sample = "121213"
    print(f"\nStep-by-step trace for '{sample}':")
    dfa_path, _ = run_dfa(table, code, sample)
    naive_path, _ = run_naive(code, sample)
    print(f"  DFA states   : {' -> '.join(map(str, dfa_path))}")
    print(f"  Naive states : {' -> '.join(map(str, naive_path))}")
    print("  Explanation  : After typing '1 2 1 2', the fourth key ('2') is a mismatch")
    print("  for state 3 ('121'). The naive lock resets completely to state 0.")
    print("  The DFA falls back to state 2, recognizing that trailing '1 2' is already")
    print("  a valid prefix of the code. The subsequent '1 3' then unlocks the DFA.")
    print("\nTo start the web dashboard, run:  python app.py")
    print("To test interactive keypad, run: python main.py --interactive")


if __name__ == "__main__":
    main()
