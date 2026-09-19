import re

def clean(num):
    rounded = round(num)

    # 0.0000000001 -> 0, 2.9999999999 -> 3, 2.734829 -> 2.734829 (kept as-is)
    return (
        0 if abs(num) < 1e-10
        else rounded if abs(num - rounded) < 1e-8
        else round(num, 10)
    )


def power(num):
    if "^" not in num:
        return num

    # "2^3^2" -> splits into "2^3" and "2" -> resolves "2^3" first -> 8^2 = 64
    left_side, exp = num.rsplit("^", 1)
    base = power(left_side)
    
    return str(float(base) ** float(exp))


class EquationValidator:
    def __init__(self, equation_str, var="x"):
        self.equation = equation_str
        self.var = var
        self.ref = {}

    def simplify_power_term(self, term, var=""):
        if not term:
            return ""

        tmp = term

        if term[0] == "+":
            term = term[1:]

        if var == "":
            return power(term)

        # "3x^2^1" -> exponent part "2^1" gets reduced to "2" via power(), giving "3x^2"
        if f"{var}^" in term:
            exp_start = term.rfind(f"{var}^") + len(f"{var}^")
            rest_exp = term[exp_start:]
            if "^" in rest_exp:
                powered = power(rest_exp)
                term = term[:exp_start] + powered

        # "2^3x" -> the coefficient "2^3" (before the variable) gets reduced to "8", giving "8x"
        var_pos = term.find(var)
        if var_pos != -1 and "^" in term[:var_pos]:
            powered = power(term[:var_pos])
            term = powered + term[var_pos:]

        # "3x^0" -> "3" (x^0 = 1, drops the variable), "3x^1" -> "3x" (x^1 = x)
        if f"{var}^0" in term:
            term = term.replace(f"{var}^0", "1")
        elif f"{var}^1" in term:
            term = term.replace(f"{var}^1", var)
        
        return f"+{term}" if tmp[0] == "+" else term

    def simplify_power_side(self, side):
        simplified = []
        current_term = ""

        for i, char in enumerate(side):
            if char in "+-":
                if i == 0 or side[i - 1] in "^eE":
                    current_term += char
                    continue

                if "^" in current_term:
                    if self.var in current_term:
                        simplified.append(self.simplify_power_term(current_term, self.var))
                    else:
                        simplified.append(self.simplify_power_term(current_term))
                else:
                    simplified.append(current_term)

                current_term = char
            else:
                current_term += char

        if current_term and "^" in current_term:
            if self.var in current_term:
                simplified.append(self.simplify_power_term(current_term, self.var))
            else:
                simplified.append(self.simplify_power_term(current_term))
        elif current_term:
            simplified.append(current_term)
        
        return simplified

    def simplify_power_eq(self):
        parts = self.equation.split("=")

        if len(parts) != 2:
            raise ValueError(f"There must be only one '=' in {self.equation}")

        left, right = parts

        left_str = "".join(self.simplify_power_side(left))
        right_str = "".join(self.simplify_power_side(right))
        
        self.equation = f"{left_str}={right_str}"
        return self.equation

    def check_cancelling_terms_term(self, term, is_right_side):
        if not term or not re.search(r"[a-zA-Z]", term):
            return

        var = ""
        for char in term:
            if char.isalpha():
                var = char

        var_pos = term.find(var)
        coeff_str = term[:var_pos]

        if coeff_str in ("", "+"):
            coeff_str = "1"
        elif coeff_str == "-":
            coeff_str = "-1"

        coeff = float(coeff_str)
        change = coeff * (-1 if is_right_side else 1)

        if "^" in term:
            pattern = r"[a-zA-Z]\^(-?\d+)"
            matched = re.search(pattern, term)
            if matched:
                deg = matched.group(1)
                self.ref[deg] = self.ref.get(deg, 0) + change
        else:
            deg = "1"
            self.ref[deg] = self.ref.get(deg, 0) + change

    def check_cancelling_terms_side(self, side, is_right_side):
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

                self.check_cancelling_terms_term(current_term, is_right_side)
                current_term = char
            else:
                current_term += char

        if current_term:
            self.check_cancelling_terms_term(current_term, is_right_side)
    
    def check_cancelling_terms(self):
        parts = self.equation.split("=")
        
        if len(parts) != 2:
            raise ValueError(f"There must be only one '=' in {self.equation}")
        
        left, right = parts
        
        self.check_cancelling_terms_side(left, False)
        self.check_cancelling_terms_side(right, True)
    
    def remove_unneccesary_terms(self):
        self.ref = {}
        self.check_cancelling_terms()
        
        for deg, val in self.ref.items():
            if val == 0:
                if deg == "1":
                    pattern = rf"\s*\d*\.?\d*[a-zA-Z](?!\^)"
                else:
                    pattern = rf"\s*\d*\.?\d*[a-zA-Z]\^{deg}"
                
                self.equation = re.sub(pattern, "0", self.equation)
        
        return self.equation
        
    def is_quadratic(self):
        self.ref = {}
        self.check_cancelling_terms()
        
        active_degrees = sorted(
            [int(deg) for deg, val in self.ref.items() if val != 0], 
            reverse=True
        )
    
        if not active_degrees:
            return False
        
        if active_degrees[0] == 2:
            return True
        
        if len(active_degrees) >= 2:
            deg0, deg1 = active_degrees[0], active_degrees[1]
            if deg0 > 2 and deg0 % 2 == 0 and deg0 == 2 * deg1:
                return True
        
        return False


class ComplexNumber:
    def __init__(self, real, imaginary):
        self.real = clean(real)
        self.imaginary = clean(imaginary)

    def __str__(self):
        if self.imaginary == 0:
            return f"{self.real}"

        # imaginary = 1 -> "i" not "1i", imaginary = -1 -> "-i" not "-1i"
        sign = "+" if self.imaginary > 0 else "-"
        imag_str = "i" if abs(self.imaginary) == 1 else f"{abs(self.imaginary)}i"
        
        if self.real == 0:
            return imag_str if self.imaginary > 0 else f"-{imag_str}"
        
        return f"{self.real} {sign} {imag_str}"
    
    def __repr__(self):
        return self.__str__()

