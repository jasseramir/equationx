# EquationX

EquationX is a simple web app that solves math equations. Type in one or more
equations, and it figures out what kind they are (linear, quadratic, or a
system of equations) and returns the solution — rendered as clean math using
[KaTeX](https://katex.org).

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

## Project Structure

```
project/
├── app.py                   # Flask app entry point
├── requirements.txt         # Python dependencies
├── solver/
│   ├── equation.py          # Classifies an equation and dispatches to the right solver
│   ├── linear.py            # Solves linear equations
│   ├── quadratic.py         # Solves quadratic equations (real & complex roots)
│   ├── system_of_eqs.py     # Solves systems of linear equations
│   └── utils.py             # Shared helpers (parsing, simplification, ComplexNumber)
├── templates/
│   └── index.html           # Main page
├── static/
│   ├── main.js               # Frontend logic (form handling, API calls, rendering)
│   ├── styles.css             # Styling
│   └── favicon.ico            # Website icon
├── README.md
└── DESIGN.md
```

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
python app.py
```

By default, Flask runs the app in debug mode locally at
`http://127.0.0.1:5000`. Open that URL in your browser to use EquationX.

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

