# EquationX

#### Video Demo: https://youtu.be/V8dZHhItgpo

#### GitHub: https://github.com/jasseramir/equationx

#### Live Demo: https://equationx-psi.vercel.app

#### Description:

EquationX is my CS50 final project. It's a Flask web app that solves math
equations: you type in one or more equations, it figures out what kind they
are (linear, quadratic, or a system of equations), and it returns the
solution rendered as proper math notation using [KaTeX](https://katex.org)
instead of plain text.

Equation solving looks simple until you actually try to build it from
scratch. There are a lot of cases to cover: equations with no solution,
equations with infinitely many solutions, quadratics with a negative
discriminant that need complex numbers, and equations that look like one
type but collapse into another once you simplify them (`x^2+3x-x^2=5` is
really linear, since its `x^2` terms cancel each other out). Getting all of
that right using nothing but string parsing, without pulling in a math
library, is what took most of the time on this project.

## Features

- **Linear equations** — e.g. `2x+3=7`
- **Quadratic equations** — e.g. `x^2-5x+6=0`, including complex roots when the
  discriminant is negative
- **Systems of equations** — multiple linear equations solved together via
  Gaussian elimination
- Detects special cases automatically: **no solution**, **infinite
  solutions**, and equations that collapse into a plain numeric identity
  (e.g. `x^0=2` → `1=2`)
- Add or remove equation fields dynamically in the UI
- Results rendered as proper math notation (via KaTeX)

## Files

**`app.py`** is the Flask application. It has two routes: `/` renders the
main page, and `/solve` takes a POST request with one or more equation
strings as JSON, passes them to the `Equation` class, and sends back the
solution as JSON. It also turns any `ComplexNumber` result into a plain
string so it can be serialized properly.

**`requirements.txt`** lists the only dependency: Flask. There's no math
library like `sympy` in here on purpose. The parsing and solving logic is
written by hand, term by term, which keeps the project small to install and
keeps every step of the math visible instead of hidden inside a library.

**`solver/equation.py`** handles classification. `Equation` strips
whitespace from the input, works out which variable(s) are involved, and
decides whether the equation (or list of equations) is `LINEAR`,
`QUADRATIC`, `SYSTEM`, or `UNKNOWN`. Along the way it simplifies exponents
(`x^0` and `x^1` collapse down to just their coefficient), resolves
equations with no variable left into an immediate "Infinite Solutions" or
"No Solution" answer, and catches the "false quadratic" case mentioned
above. Once it knows the type, it hands the simplified equation off to the
matching solver class.

**`solver/linear.py`** parses an equation term by term, sums the variable's
coefficients into `a` and the constants into `b`, and reduces things to
`ax = b`. It checks for `a == 0` before dividing, so it can return "No
Solution" or "Infinite Solutions" instead of crashing.

**`solver/quadratic.py`** buckets coefficients by degree (`2`, `1`, `0`)
into `a`, `b`, `c` and applies the quadratic formula. The sign of the
discriminant decides what comes back: two real roots, one repeated real
root, or a complex-conjugate pair built with the `ComplexNumber` helper when
it's negative.

**`solver/system_of_eqs.py`** solves several linear equations together with
Gaussian elimination and partial pivoting: build an augmented matrix,
forward-eliminate, then back-substitute. A row that reduces to all zeros on
one side but not the other means no solution; all zeros on both sides means
at least one equation was redundant, so there are infinite solutions.

**`solver/utils.py`** holds the shared helpers. `simplify_power_eq` and
`fix_false_quadratic` normalize exponents and catch equations that only
look quadratic. `clean` rounds floating-point results that are almost an
integer back to that exact value, so you get `3` instead of
`2.9999999999`. `power` evaluates exponent chains like `"2^3"`. And
`ComplexNumber` just knows how to format itself as a readable `a ± bi`
string.

**`templates/index.html`** is the single page of the app: a form where you
can add or remove equation fields, and a container where the result shows
up.

**`static/main.js`** is all the frontend logic. It manages the equation
fields, sends the current set of equations to `/solve` as JSON, and turns
the JSON response into a LaTeX string (`x1` becomes `x_{1}`, multiple
variables get joined with `\begin{aligned}`) that KaTeX then renders. There's
no math logic on the client at all; it just displays whatever the backend
computes.

**`static/styles.css`** styles the page, form, and result area.

**`DESIGN.md`** goes into more depth on the solver itself: why it's built
around string parsing instead of a math library, how classification works,
and why each edge case is handled the way it is.

## How It Works

1. The user submits one or more equation strings from the web UI.
2. The Flask route `/solve` passes them to the `Equation` class.
3. `Equation` classifies each equation as `LINEAR`, `QUADRATIC`, `SYSTEM`, or
   `UNKNOWN`, simplifying terms (like `x^2`, `x^0`, etc.) along the way.
4. Based on the classification, the equation is handed off to
   `LinearEquation`, `QuadraticEquation`, or `SystemOfEquations` to compute
   the actual solution.
5. The result is returned as JSON and rendered on the page using KaTeX.

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
# 1. Clone or download the project, then move into it
cd project

# 2. (Optional but recommended) create a virtual environment
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Running the app

```bash
flask run
```

This starts the development server locally at `http://127.0.0.1:5000`. Open
that URL in your browser to use EquationX. If `flask run` doesn't find the
app on its own, set `export FLASK_APP=app.py` (or on Windows, `set
FLASK_APP=app.py`) first, and add `--debug` if you want auto-reload while
developing.

You can also just try the live demo linked at the top of this file without
installing anything.

## Example Inputs

| Input | Result |
|---|---|
| `2x+3=7` | `x = 2` |
| `x^2-5x+6=0` | `x1 = 3`, `x2 = 2` |
| `x^2+1=0` | `x1 = 0 + 1i`, `x2 = 0 - 1i` |
| `x+y=5`, `x-y=1` | `x = 3`, `y = 2` |
| `x=x` | Infinite Solutions |
| `x=x+1` | No Solution |

## Notes

- Equations must contain exactly one `=` sign.
- Spaces in the input are stripped automatically, so `2x + 3 = 7` and
  `2x+3=7` are equivalent.
- Only single-letter variables are supported (e.g. `x`, `y`, `z`).

