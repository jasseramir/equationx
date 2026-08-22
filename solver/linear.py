from .utils import clean

class LinearEquation:
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
            "type": "variable" if self.var in term else "number",
            "coefficient" if self.var in term else "value": -val if is_right_side else val,
        })

    def parseSide(self, side, is_right_side):
        current_term = ""

        for i, char in enumerate(side):
            if char in "+-":
                if i == 0 or side[i - 1] in "eE":
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

        a, b = 0, 0

        for term in self.ref:
            if term["type"] == "variable":
                a += term["coefficient"]
            else:
                b += -term["value"]

        if a == 0 and b == 0:
            return { "status": "Infinite Solutions" }

        if a == 0:
            return { "status": "No Solution" }

        return (
            {
                self.var: round(clean(b / a)),
                "status": "Solved"
            }
        )
