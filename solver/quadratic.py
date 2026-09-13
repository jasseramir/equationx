import math
import re
from .utils import clean, ComplexNumber

def extract_x(u, n):
    if u == 0:
        return [0.0]

    if n % 2 == 0:
        if u > 0:
            root = clean(round(u ** (1 / n), 3))
            return [root, -root]
        return []

    sign = 1 if u > 0 else -1
    root = round((abs(u) ** (1 / n)) * sign, 3)
    return [root]

class QuadraticEquation:
    def __init__(self, equation_str, var):
        self.equation = equation_str
        self.var = var
        self.ref = []
        self.degrees = set()
    
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
        degree = 0

        if self.var in term:
            val = float(term[0:term.find(self.var)])

            pattern = rf"{re.escape(self.var)}\^(-?\d+)"
            matched = re.search(pattern, term)

            degree = int(matched.group(1)) if matched else 1
        else:
            val = float(term)
            degree = 0
        
        self.degrees.add(degree)

        self.ref.append({
            "degree": degree,
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
        
        self.degrees.add(0)
        sorted_deg = sorted(self.degrees, reverse=True)
        
        if len(sorted_deg) == 2:
            mid = sorted_deg[0] // 2
            self.degrees.add(mid)
            sorted_deg = sorted(self.degrees, reverse=True)

        self.degrees = sorted_deg

    def solve(self):
        self.ref = []
        self.degrees = set()
        
        self.parse()
        
        if self.degrees[0] != 2 * self.degrees[1]:
            return { "status": "Not Quadratic" }
        
        n = self.degrees[1]

        a, b, c = 0, 0, 0

        for term in self.ref:
            if term["degree"] == self.degrees[0]:
                a += term["coefficient"]
            elif term["degree"] == self.degrees[1]:
                b += term["coefficient"]
            elif term["degree"] == self.degrees[2]:
                c += term["value"]
            else:
                raise ValueError(f"Unsupported equation: {self.equation}")

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

            z1 = ComplexNumber(round(real, 3), round(imaginary, 3))
            z2 = ComplexNumber(round(real, 3), -round(imaginary, 3))

            return {
                f"{self.var}1": z1,
                f"{self.var}2": z2,
                "status": "Solved"
            }

        u1 = clean((-b + math.sqrt(discriminant)) / (2 * a))
        u2 = clean((-b - math.sqrt(discriminant)) / (2 * a))

        all_x_values = []
        all_x_values.extend(extract_x(u1, n))

        if discriminant > 0:
            all_x_values.extend(extract_x(u2, n))

        unique_x = sorted(list(set(all_x_values)))

        if not unique_x:
            return { "status": "No Real Solution" }

        result = { f"{self.var}{i+1}": clean(val) for i, val in enumerate(unique_x) }
        result["status"] = "Solved"
        
        return result

