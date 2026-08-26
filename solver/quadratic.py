import math
from .utils import clean, ComplexNumber

class QuadraticEquation:
    def __init__(self, equation_str, var):
        self.equation = equation_str
        self.var = var
        self.ref = []
    
    def parseTerm(self, term, is_right_side):
        if not term:
            return

        if term.startswith("+"):
            term = term[1:]

        if term.startswith(self.var):
            term = "1" + term
        elif term.startswith(f"-{self.var}"):
            term = "-1" + term[1:]

        val = 0

        if self.var in term:
            val = float(term[0:term.find(self.var)])
        else:
            val = float(term)

        self.ref.append({
            # "3x^2" -> degree 2, "3x" -> degree 1, "5" -> degree 0
            "degree": 2 if f"{self.var}^2" in term else 1 if self.var in term else 0,
            # "3x^2" -> {"coefficient":3}, "5" -> {"value":5}
            "coefficient" if self.var in term else "value": -val if is_right_side else val,
        })

    def parseSide(self, side, is_right_side):
        current_term = ""

        for i, char in enumerate(side):
            if char in "+-":
                if i == 0:
                    current_term += char
                    continue

                if side[i - 1] == "^":
                    current_term += char
                    continue

                if side[i - 1] in "eE":
                    current_term += char
                    continue

                self.parseTerm(current_term, is_right_side)
                current_term = char
            else:
                current_term += char

        if current_term:
            self.parseTerm(current_term, is_right_side)

    def parse(self):
        parts = self.equation.split("=")

        if len(parts) != 2:
            raise ValueError(f"There must be only one '=' in {self.equation}")

        left, right = parts

        self.parseSide(left, False)
        self.parseSide(right, True)

    def solve(self):
        if not self.ref:
            self.parse()

        a, b, c = 0, 0, 0

        # 3x^2 -5x + 2 = 0 -> a = 3, b = -5, c = 2
        for term in self.ref:
            if term["degree"] == 2:
                a += term["coefficient"]
            elif term["degree"] == 1:
                b += term["coefficient"]
            elif term["degree"] == 0:
                c += term["value"]
            else:
                raise ValueError(f"Unsupported equation: {self.equation}")

        # 0 = 0 -> infinite / 0 = 5 -> no solution / 5x + 2 = 0 leaked here -> can't solve as quadratic
        if a == 0 and b == 0 and c == 0:
            return { "status": "Infinite Solutions" }

        if a == 0 and b == 0:
            return { "status": "No Solution" }

        if a == 0:
            return { "status": "Can't Solve" }

        discriminant = clean(b ** 2 - 4 * a * c)

        if discriminant < 0:
            real = clean(-b / (2 * a))
            imaginary = clean(math.sqrt(-discriminant) / (2 * a))

            # x^2 + 1 = 0 -> real = 0, imaginary = 1 -> x1 = 0 + 1i, x2 = 0 - 1i
            z1 = ComplexNumber(round(real, 3), round(imaginary, 3))
            z2 = ComplexNumber(round(real, 3), -round(imaginary, 3))

            return (
                {
                    f"{self.var}1": z1,
                    f"{self.var}2": z2,
                    "status": "Solved"
                }
            )

        pos_root = clean((-b + math.sqrt(discriminant)) / (2 * a))
        neg_root = clean((-b - math.sqrt(discriminant)) / (2 * a))

        # discriminant == 0 -> one repeated root (x1 == x2, so return just one)
        if discriminant > 0:
            return (
                {
                    f"{self.var}1": round(pos_root, 3),
                    f"{self.var}2": round(neg_root, 3),
                    "status": "Solved"
                }
            )
        else:
            return (
                {
                    self.var: round(pos_root, 3),
                    "status": "Solved"
                }
            )
