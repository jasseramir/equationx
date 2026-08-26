import re
from .utils import clean

class SystemOfEquations:
    def __init__(self, equations, variables):
        self.equations = equations
        self.variables = variables
        self.ref = []
        self.result = {}

    def parseTerm(self, term, is_right_side, equation_index):
        if not term:
            return

        term_var = None

        # a term only has one variable, e.g. "3x" -> term_var = "x", "5" -> term_var = None
        for variable in self.variables:
            if variable in term:
                term_var = variable
                break

        if term.startswith("+"):
            term = term[1:]

        if term_var is not None:
            # x -> 1x, -x -> -1x (so float() can grab the coefficient)
            if term.startswith(term_var):
                term = "1" + term
            elif term.startswith("-" + term_var):
                term = "-1" + term.replace("-", "", 1)
            
        if term_var is not None:
            # x + y = 5 -> "x" and "y" columns of equation_index get +1 each, "5" is on the right
            coefficient = (-1 if is_right_side else 1) * float(term[:term.find(term_var)])
            self.ref[equation_index][term_var] += coefficient
        else:
            self.ref[equation_index]["constant"] += -float(term) if is_right_side else float(term)

    def parseSide(self, side, is_right_side, equation_index):
        current_term = ""

        for i, char in enumerate(side):
            if char in "+-":
                if i == 0 or side[i - 1] in "eE":
                    current_term += char
                    continue

                self.parseTerm(current_term, is_right_side, equation_index)
                current_term = char
            else:
                current_term += char

        if current_term:
            self.parseTerm(current_term, is_right_side, equation_index)

    def parse(self):
        self.ref = []

        for i in range(len(self.equations)):
            left_side, right_side = re.sub(r"\s+", "", self.equations[i]).split("=")

            self.ref.append({})

            # every equation gets a 0 for each variable, even ones it doesn't use
            # (so all rows line up in the matrix, e.g. x + y = 5 and x - z = 1 both get a "y" and "z" slot)
            for variable in self.variables:
                self.ref[i][variable] = 0

            self.ref[i]["constant"] = 0

            self.parseSide(left_side, False, i)
            self.parseSide(right_side, True, i)

    def toMatrix(self):
        matrix = []

        for equation in self.ref:
            row = []

            for variable in self.variables:
                row.append(equation[variable])

            # x + y = 5 -> constant was stored as -5, flipped back to +5 for the matrix
            row.append(-equation["constant"])
            matrix.append(row)

        return matrix

    def solve(self):
        if not self.ref:
            self.parse()

        vars = sorted(list(self.variables))

        matrix = self.toMatrix()
        n = len(matrix)

        for pivot in range(n - 1):
            if matrix[pivot][pivot] == 0:
                for i in range(pivot + 1, n):
                    if matrix[i][pivot] != 0:
                        matrix[pivot], matrix[i] = matrix[i], matrix[pivot]
                        break

                if matrix[pivot][pivot] == 0:
                    continue

            for i in range(pivot + 1, n):
                # subtract a multiple of the pivot row so column "pivot" becomes 0 in row i
                factor = matrix[i][pivot] / matrix[pivot][pivot]

                for j in range(pivot, len(matrix[i])):
                    matrix[i][j] = clean(matrix[i][j] - factor * matrix[pivot][j])

        for row in matrix:
            constant = row[-1]
            coefficients = row[:-1]

            # 0 = 0 -> infinite solutions, 0 = 5 -> no solution
            all_zero = all(coefficient == 0 for coefficient in coefficients)

            if all_zero and constant == 0:
                return { "status": "Infinite Solutions" }

            if all_zero:
                return { "status": "No Solution" }

        for i in range(n - 1, -1, -1):
            temp = matrix[i][len(matrix[i]) - 1]

            # solve from the last row up, plugging in variables already found into earlier rows
            for j in range(i + 1, len(matrix[i]) - 1):
                current_var = vars[j]
                if self.result[current_var] is not None:
                    temp -= self.result[current_var] * matrix[i][j]

            result = clean(temp / matrix[i][i])
            self.result[vars[i]] = result

        self.result["status"] = "Solved"
        return self.result
