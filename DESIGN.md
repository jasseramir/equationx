# Design Document | EquationX

This document explains the internal design of EquationX: how the pieces fit
together, why certain decisions were made, and what trade-offs they involve.
For setup/usage instructions, see `README.md`.

## Goals

- Solve linear equations, quadratic equations, and systems of linear
  equations from raw string input (e.g. `"2x+3=7"`), without a full math
  parser or AST. The project sticks to light string-processing heuristics
  instead of a formal parser.
- Handle edge cases gracefully: no solution, infinite solutions, complex
  roots, and equations that only look like one type but are secretly
  another (e.g. a quadratic whose `x^2` terms cancel out).
- Keep the backend a thin, stateless JSON API. All state (the current set
  of equation input fields) lives in the browser.

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

The backend splits into two stages. First it classifies: figure out what
kind of equation(s) this is. Then it solves: dispatch to whichever solver
class knows how to handle that type. Because of this split, `LinearEquation`,
`QuadraticEquation`, and `SystemOfEquations` never need to know how they
were determined to be linear, quadratic, or a system. They just get an
already-simplified equation string and solve it. `Equation` is the only
place in the codebase that has to reason about ambiguity.

## Why String Parsing Instead of a Math Library

The parsing here is hand-rolled: split on `+`/`-`, detect the variable,
extract coefficients, instead of using something like `sympy`. That keeps
the project dependency-free (only Flask is required, see
`requirements.txt`) and keeps solving logic fully visible and easy to step
through. The trade-off is a narrower parser:

- Only single-letter variable names are supported.
- Exactly one `=` per equation.
- Implicit multiplication only (`2x`, not `2*x`).

These are scope limits I chose on purpose, not things I ran out of time to
fix. They keep the term-parsing logic (`parseTerm`/`parseSide`) simple and
predictable instead of needing a proper tokenizer or grammar.

## Classification (`Equation.getType`)

Classification works like this:

1. Extract the variable(s) present.
2. Run `simplify_power_eq`, which normalizes exponent expressions, e.g.
   collapsing `x^2^1`-style chains via `power()`, and stripping `x^0` /
   `x^1` down to their coefficient.
3. Count the remaining degree(s) of the variable in the simplified
   equation:
   - No variable left: the equation already collapsed to a numeric
     comparison (e.g. `"1=2"`). This gets resolved right away as an
     Identity (infinite solutions) or a Contradiction (no solution). There's
     no reason to hand a fully numeric equation to a solver class.
   - All degrees are `1`: LINEAR.
   - All degrees are `2`: QUADRATIC.
   - Mixed degrees: UNKNOWN (unsupported, e.g. cubic terms).

For a list of equations, every equation in it has to classify as linear
individually for the whole set to count as a SYSTEM. Systems only support
linear equations here, since solving nonlinear systems generally needs
numerical methods (Newton's method and the like) that are outside the scope
of this project.

### The "false quadratic" problem

An equation like `x^2+3x-x^2=5` contains an `x^2` term but is really linear,
because the quadratic terms cancel. `fix_false_quadratic` catches this by
summing the coefficients of every `var^2` term on each side and checking
whether the net coefficient is zero. If it is, `^2` gets stripped from those
terms before classification continues. This step runs after
`simplify_power_eq`, since it needs every `var^2` term to already have an
explicit numeric coefficient (`x^2` becomes `1x^2`) in order to sum
correctly.

## Solving

All three solver classes follow the same shape:

1. `parseTerm(term, is_right_side)` interprets a single term (e.g. `"-1x^2"`,
   `"7"`), flipping its sign if it's on the right-hand side, since solving
   means moving everything to one side.
2. `parseSide(side, is_right_side)` splits a side of the equation into terms
   by scanning for `+`/`-`, but skips over:
   - a leading sign (`i == 0`)
   - a sign inside scientific notation (`2e-5`)
   - a sign directly after `^` in an exponent (`x^-2`, quadratic solver only)
3. `parse()` applies both sides and fills in `self.ref`.
4. `solve()` reduces `self.ref` into coefficients and applies the matching
   formula.

### Linear

Coefficients of the variable are summed into `a`, constants into `b`, and
the equation reduces to `ax = b`. `a == 0` branches into "no solution" (if
`b != 0`) or "infinite solutions" (if `b == 0`) before any division happens.

### Quadratic

Coefficients are bucketed by degree (`2`, `1`, `0`) into `a`, `b`, `c`, then
solved with the quadratic formula. The sign of the discriminant decides the
shape of the result:

- `> 0`: two distinct real roots (`x1`, `x2`)
- `== 0`: one real root (`x`)
- `< 0`: a complex conjugate pair, represented with the `ComplexNumber`
  helper class (`solver/utils.py`) so the API can return a clean
  `real ± imaginary·i` string instead of raw tuples.

Degenerate cases (`a == 0`) fall back to "no solution", "infinite
solutions", or "can't solve" rather than quietly treating the equation as
linear. That reclassification already happened upstream, in
`Equation._classify_single` / `fix_false_quadratic`, so if `a == 0` shows up
here it means something didn't fully cancel, and it's treated
conservatively rather than guessed at.

### Systems

Solved with plain Gaussian elimination: build an augmented matrix from the
parsed equations, forward-eliminate with partial pivoting (swap in a
nonzero pivot row when needed), then back-substitute. It's a standard
algorithm that's easy to check by hand, which matters more here than raw
performance. The system sizes involved (a handful of user-entered
equations) are far too small for elimination's O(n³) cost to be an issue.

A row that reduces to all-zero coefficients with a nonzero constant means
no solution. All zeros including the constant means infinite solutions,
since at least one equation was redundant.

## Shared Utilities (`solver/utils.py`)

- `clean(num)` rounds floating-point results that are extremely close to an
  integer, or to zero, back to that exact value. Without it, results would
  occasionally show up as an ugly near-integer (`2.9999999999`) instead of
  the exact answer (`3`).
- `power(num)` evaluates literal exponent chains like `"2^3"` by resolving
  them recursively, left to right. It's used when simplifying numeric
  exponents during term simplification.
- `ComplexNumber` is a small value type whose only job is `__str__`/
  `__repr__` formatting (e.g. `"2 + 3i"`, `"-1i"`, `"0"`), so the
  frontend/JSON layer doesn't have to special-case complex-number
  formatting itself.

## Frontend

The frontend (`static/main.js`) stays as simple as possible: it collects the
current input fields, POSTs them as JSON to `/solve`, and renders whatever
comes back. All the math lives server-side. Results are rendered with
[KaTeX](https://katex.org) rather than plain text so multi-variable
systems, exponents, and complex numbers show up as proper math notation.
The JS builds a LaTeX string from the JSON response (`x1` becomes `x_{1}`,
multiple variables get joined with `\begin{aligned}`) and hands it to KaTeX
to render. No equation-solving logic exists on the client.

## Known Limitations / Non-Goals

- No support for multi-character variable names or explicit multiplication
  operators (`*`).
- No support for nonlinear systems (e.g. a system mixing linear and
  quadratic equations).
- No persistence. Nothing is saved between requests; each `/solve` call is
  independent and stateless.
- Input validation is minimal. Malformed equations (more than one `=`,
  unsupported degrees) raise a `ValueError`, which the frontend currently
  surfaces as a generic "Can't Solve" rather than a specific error message.

