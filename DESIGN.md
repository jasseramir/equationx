# Design Document — EquationX

This document explains the internal design of EquationX: how the pieces fit
together, why certain decisions were made, and what trade-offs they involve.
For setup/usage instructions, see `README.md`.

## Goals

- Solve linear equations, quadratic equations, and systems of linear
  equations from raw string input (e.g. `"2x+3=7"`), without a full math
  parser/AST — the project intentionally favors light string-processing
  heuristics over a formal parser.
- Handle edge cases gracefully: no solution, infinite solutions, complex
  roots, and equations that only *look* like one type but are secretly
  another (e.g. a quadratic whose `x^2` terms cancel out).
- Keep the backend a thin, stateless JSON API; all state lives in the
  browser session (the current set of equation input fields).

## High-Level Architecture

```
Browser (templates/index.html + static/main.js)
        │  POST /solve  { "equations": [...] }
        ▼
Flask app (app.py)
        │
        ▼
Equation (solver/equation.py)   ── classifies + simplifies
        │
        ├── LinearEquation        (solver/linear.py)
        ├── QuadraticEquation     (solver/quadratic.py)
        └── SystemOfEquations     (solver/system_of_eqs.py)
                │
                ▼
        shared helpers (solver/utils.py)
```

The backend has a single responsibility split into two stages:

1. **Classify** — figure out what kind of equation(s) this is.
2. **Solve** — dispatch to the solver that knows how to handle that type.

This separation means each solver class (`LinearEquation`,
`QuadraticEquation`, `SystemOfEquations`) doesn't need to know *how* it was
determined to be linear/quadratic/a system — it just receives an
already-simplified equation string and solves it. `Equation` is the only
place that needs to reason about ambiguity.

## Why String Parsing Instead of a Math Library

The parsing here is hand-rolled (split on `+`/`-`, detect the variable,
extract coefficients) instead of using something like `sympy`. This keeps
the project dependency-free (only Flask is required — see
`requirements.txt`) and keeps solving logic fully transparent and
debuggable. The trade-off is that the parser is deliberately narrow:

- Only single-letter variable names are supported.
- Exactly one `=` per equation.
- Implicit multiplication only (`2x`, not `2*x`).

These constraints are intentional scope limits, not oversights — they keep
the term-parsing logic (`parseTerm`/`parseSide`) simple and predictable
rather than needing a proper tokenizer/grammar.

## Classification (`Equation.getType`)

Classification happens by:

1. Extracting the variable(s) present.
2. Running `simplify_power_eq`, which normalizes exponent expressions (e.g.
   collapsing `x^2^1` style chains via `power()`, and stripping `x^0` /
   `x^1` down to their coefficient).
3. Counting the remaining degree(s) of the variable in the simplified
   equation:
   - No variable left → the equation already collapsed to a numeric
     comparison (e.g. `"1=2"`). This is resolved immediately as an
     **Identity** (infinite solutions) or **Contradiction** (no solution) —
     there's no reason to hand a fully-numeric equation to a solver class.
   - All degrees are `1` → **LINEAR**.
   - All degrees are `2` → **QUADRATIC**.
   - Mixed degrees → **UNKNOWN** (unsupported; e.g. cubic terms).

For a **list** of equations, every equation must individually classify as
linear for the whole set to be treated as a **SYSTEM**. Systems only
support linear equations — this is a deliberate scope decision, since
solving nonlinear systems generally requires numerical methods
(Newton's method, etc.) that are out of scope for this project.

### The "false quadratic" problem

An equation like `x^2+3x-x^2=5` contains an `x^2` term but is really linear,
because the quadratic terms cancel. `fix_false_quadratic` detects this by
summing the coefficients of every `var^2` term on each side and checking if
the net coefficient is zero. If so, `^2` is stripped from those terms before
classification continues. This runs *after* `simplify_power_eq`, since it
depends on every `var^2` term already having an explicit numeric coefficient
(`x^2` → `1x^2`) to sum correctly.

## Solving

All three solver classes follow the same shape:

1. `parseTerm(term, is_right_side)` — interpret a single term (e.g. `"-1x^2"`,
   `"7"`), sign-flipping if it's on the right-hand side (since solving means
   moving everything to one side).
2. `parseSide(side, is_right_side)` — split a side of the equation into
   terms by scanning for `+`/`-`, while carefully *not* splitting on:
   - a leading sign (`i == 0`)
   - a sign inside scientific notation (`2e-5`)
   - a sign directly after `^` in an exponent (`x^-2`, quadratic solver only)
3. `parse()` — apply both sides, populate `self.ref`.
4. `solve()` — reduce `self.ref` into coefficients and apply the
   corresponding formula.

### Linear

Coefficients of the variable are summed into `a`, constants into `b`, and
the equation reduces to `ax = b`. `a == 0` branches into "no solution" (if
`b != 0`) or "infinite solutions" (if `b == 0`) before ever dividing.

### Quadratic

Coefficients are bucketed by degree (`2`, `1`, `0`) into `a`, `b`, `c`, then
solved with the quadratic formula. The discriminant's sign determines the
result shape:

- `> 0` → two distinct real roots (`x1`, `x2`)
- `== 0` → one real root (`x`)
- `< 0` → a complex conjugate pair, represented with the `ComplexNumber`
  helper class (`solver/utils.py`) so the API can return a clean
  `real ± imaginary·i` string instead of raw tuples.

Degenerate cases (`a == 0`) fall back to "no solution" / "infinite
solutions" / "can't solve" rather than silently treating the equation as
linear — that reclassification already happened upstream in
`Equation._classify_single` / `fix_false_quadratic`, so reaching `a == 0`
here means something didn't fully cancel and is treated conservatively.

### Systems

Solved with straightforward **Gaussian elimination**: build an augmented
matrix from the parsed equations, forward-eliminate with partial pivoting
(swap in a nonzero pivot row when needed), then back-substitute. This is a
standard, well-understood algorithm that's easy to verify by hand, which
matters more here than performance — the system sizes involved (a handful
of user-entered equations) are far too small for elimination's O(n³) cost
to matter.

A row that reduces to all-zero coefficients with a nonzero constant means
"no solution"; all-zero including the constant means "infinite solutions"
(at least one equation was redundant).

## Shared Utilities (`solver/utils.py`)

- **`clean(num)`** — snaps floating-point results that are extremely close
  to an integer (or to zero) back to that exact value. This exists purely
  to hide floating-point noise (e.g. `2.9999999999` → `3`) from the user;
  without it, results would occasionally show ugly near-integers instead of
  the exact answer.
- **`power(num)`** — evaluates literal exponent chains like `"2^3"` by
  recursively resolving left-to-right, used when simplifying numeric
  exponents that show up during term simplification.
- **`ComplexNumber`** — a minimal value type whose only job is
  `__str__`/`__repr__` formatting (e.g. `"2 + 3i"`, `"-1i"`, `"0"`), so the
  frontend/JSON layer never has to special-case complex-number formatting
  itself.

## Frontend

The frontend (`static/main.js`) is intentionally dumb: it collects the
current input fields, POSTs them as JSON to `/solve`, and renders whatever
comes back. All math intelligence lives server-side. Results are rendered
with [KaTeX](https://katex.org) rather than plain text so multi-variable
systems, exponents, and complex numbers display as proper math notation.
The JS builds a LaTeX string from the JSON response (turning `x1` into
`x_{1}`, joining multiple variables with `\begin{aligned}`) and hands it to
KaTeX to render — no equation-solving logic exists on the client.

## Known Limitations / Non-Goals

- No support for multi-character variable names or explicit multiplication
  operators (`*`).
- No support for nonlinear systems (e.g. a system mixing linear and
  quadratic equations).
- No persistence — nothing is saved between requests; each `/solve` call is
  independent and stateless.
- Input validation is minimal; malformed equations (e.g. more than one `=`,
  unsupported degrees) raise a `ValueError`, which the frontend currently
  surfaces as a generic "Can't Solve" rather than a specific error message.

