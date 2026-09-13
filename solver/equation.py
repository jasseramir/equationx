import re

from .utils import power, EquationValidator
from .linear import LinearEquation
from .quadratic import QuadraticEquation
from .system_of_eqs import SystemOfEquations

class Equation:
    def __init__(self, equation_s_):
        if isinstance(equation_s_, list):
            self.equation = [eq.replace(" ", "") for eq in equation_s_]
        else:
            self.equation = equation_s_.replace(" ", "")
        
        vars_list = self.getVars()
        self.var = vars_list[0] if len(vars_list) == 1 else "x"
    
    def __str__(self):
        if isinstance(self.equation, list):
            return "\n".join(self.equation)
        return self.equation
    
    def simplify(self, eq):
        return EquationValidator(eq, self.var).simplify_power_eq().remove_unneccesary_terms()

    def getType(self):
        if isinstance(self.equation, list):
            for eq in self.equation:
                clean_eq = EquationValidator(eq, self.var).simplify_power_eq()
                clean_eq = EquationValidator(clean_eq, self.var).remove_unneccesary_terms()
                if re.search(r"\^\d+", clean_eq):
                    return "UNKNOWN"
            return "SYSTEM"

        validator = EquationValidator(self.equation, self.var)
        clean_eq = validator.simplify_power_eq()
        clean_eq = validator.remove_unneccesary_terms()

        if re.search(r"\^\d+", clean_eq):
            return "QUADRATIC" if validator.is_quadratic() else "UNKNOWN"

        return "LINEAR"

    def getVars(self):
        equations = self.equation if isinstance(self.equation, list) else [self.equation]
        vars_set = set()
        
        for eq in equations:
            for char in eq:
                if char.isalpha():
                    vars_set.add(char)
                    
        return sorted(list(vars_set))
        
    def solve(self):
        variables = self.getVars()
        eq_type = self.getType()

        if eq_type == "SYSTEM":
            if len(variables) > len(self.equation):
                raise ValueError(f"Underdetermined system: Found {len(variables)} variables for {len(self.equation)} equations.")
        elif eq_type in ["LINEAR", "QUADRATIC"]:
            if len(variables) > 1:
                raise ValueError(f"Single {eq_type.lower()} equation cannot have multiple variables: {variables}")
            elif len(variables) == 0:
                raise ValueError("No variable found in the equation.")

        match eq_type:
            case "SYSTEM":
                return SystemOfEquations(self.equation, variables).solve()
            case "QUADRATIC":
                return QuadraticEquation(self.equation, variables[0]).solve()
            case "LINEAR":
                return LinearEquation(self.equation, variables[0]).solve()
            case _:
                raise ValueError("Unsupported or Invalid Equation(s)")

