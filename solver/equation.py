# ERRORS IN THIS CODE WERE FIXED BY AI

import re

from .utils import power, simplify_power_eq, fix_false_quadratic
from .linear import LinearEquation
from .quadratic import QuadraticEquation
from .system_of_eqs import SystemOfEquations

class Equation:
    def __init__(self, equation_s_):
        if isinstance(equation_s_, list):
            self.equation = [eq.replace(" ", "") for eq in equation_s_]
        else:
            self.equation = equation_s_.replace(" ", "")
    
    def __str__(self):
        if isinstance(self.equation, list):
            return "\n".join(self.equation)
        return self.equation

    def getType(self):
        if isinstance(self.equation, list):
            simplified_equations = []

            for equation in self.equation:
                variable = self._extract_variable(equation)
                result, simplified = self._classify_single(equation, variable)

                # A system is only supported when every equation in it is
                # linear. A dict result just means that particular equation
                # collapsed into a plain number comparison (e.g. "1=2"),
                # which is still a (degenerate) linear equation, so we keep it.
                if isinstance(result, str) and result != "LINEAR":
                    return "UNKNOWN"

                simplified_equations.append(simplified)

            # Keep the simplified/fixed versions so solve() doesn't have to
            # redo this work (and so LinearEquation/QuadraticEquation/
            # SystemOfEquations work off the cleaned-up equations).
            self.equation = simplified_equations

            return "SYSTEM"

        variable = self.getVars()
        result, simplified = self._classify_single(self.equation, variable)

        self.equation = simplified

        return result

    def _classify_single(self, equation, variable):
        """
        Classify a single (non-system) equation string.

        Returns a tuple: (result, simplified_equation)
        - `result` is either:
            - a dict with a "status" key, if the equation has no variable
              left after simplification (e.g. "x^0=2" becomes "1=2", which
              is just a numeric comparison, already solved).
            - one of "LINEAR", "QUADRATIC", or "UNKNOWN".
        - `simplified_equation` is the equation after simplify_power_eq
          (and fix_false_quadratic, when relevant) has been applied to it.
        """
        simplified = simplify_power_eq(equation, variable)

        # The variable can disappear entirely after simplification, e.g.
        # "x^0=2" -> "1=2" (simplify_power_eq drops "var^0" and keeps only
        # its coefficient). When that happens, this is really just a
        # numeric comparison, so we can resolve it right here.
        # Note: we check for ANY leftover variable (not just the specific
        # "variable" we simplified with), since an equation from a system
        # can have more than one letter in it (e.g. "x^0+y=5"), and losing
        # "x" there does not mean the equation became fully numeric.
        if not variable or not self._extract_variable(simplified):
            left, right = simplified.split("=")

            left_value = self._evaluate_constant_side(left)
            right_value = self._evaluate_constant_side(right)

            if abs(left_value - right_value) < 1e-9:
                return {"status": "Infinite Solutions", "type": "Identity"}, simplified

            return {"status": "No Solution", "type": "Contradiction"}, simplified

        # Some equations look quadratic (they contain "var^2" terms) but
        # those terms fully cancel out, making them linear in disguise.
        simplified = fix_false_quadratic(simplified, variable)

        # "3x^2 + 5 = 0" -> matches "^2" for variable "x", giving degrees = ["^2"]
        degrees = re.findall(
            rf"{re.escape(variable)}((?:\^-?\d+(?:\.\d+)?)+)",
            simplified
        )

        if not degrees:
            return "LINEAR", simplified

        # degrees like "^2" or "^2^1" -> "2" or "2^1" -> evaluated to 2.0 via power()
        evaluated_degrees = [float(power(degree[1:])) for degree in degrees]

        if all(degree == 2 for degree in evaluated_degrees):
            return "QUADRATIC", simplified

        if all(degree == 1 for degree in evaluated_degrees):
            return "LINEAR", simplified

        return "UNKNOWN", simplified

    @staticmethod
    def _evaluate_constant_side(side):
        """
        Sum up a side of the equation once it no longer contains any
        variable, e.g. "2+3" -> 5.0, "-1" -> -1.0.
        """
        total = 0.0
        current_term = ""

        for i, char in enumerate(side):
            if char in "+-" and i != 0:
                total += float(current_term)
                current_term = char
            else:
                current_term += char

        if current_term:
            total += float(current_term)

        return total

    @staticmethod
    def _is_scientific_e(char, text, start, end):
        """
        True if `char` ('e'/'E') is being used as scientific notation
        (e.g. the "e" in "2e5") rather than as a variable name.
        """
        return (
            char in "eE"
            and start > 0
            and end < len(text)
            and text[start - 1].isdigit()
            and text[end].isdigit()
        )

    @staticmethod
    def _extract_variable(equation):
        """
        Return the first real variable letter found in a single equation
        string, ignoring "e"/"E" when used as scientific notation.
        Returns "" if no variable is present.
        """
        for match in re.finditer(r"[a-zA-Z]", equation):
            char = match.group()

            if Equation._is_scientific_e(char, equation, match.start(), match.end()):
                continue

            return char

        return ""

    def getVars(self):
        if isinstance(self.equation, list):
            variables = set()

            for equation in self.equation:
                for match in re.finditer(r"[a-zA-Z]", equation):
                    char = match.group()

                    if self._is_scientific_e(char, equation, match.start(), match.end()):
                        continue

                    variables.add(char)

            return sorted(list(variables))

        return self._extract_variable(self.equation)
    
    def solve(self):
        eq_type = self.getType()

        # getType() already fully solved the equation (e.g. it collapsed
        # into a plain number comparison like "1=2"), so there's nothing
        # left for LinearEquation/QuadraticEquation to do.
        if isinstance(eq_type, dict):
            return eq_type

        variables = self.getVars()

        match eq_type:
            case "SYSTEM":
                return SystemOfEquations(self.equation, variables).solve()
            case "QUADRATIC":
                return QuadraticEquation(self.equation, variables).solve()
            case "LINEAR":
                return LinearEquation(self.equation, variables).solve()
            case _:
                raise ValueError("Unsupported or Invalid Equation(s)")
