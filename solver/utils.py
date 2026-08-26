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


def simplify_power_eq(equation, var):
    parts = equation.split("=")

    if len(parts) != 2:
        raise ValueError(f"There must be only one '=' in {equation}")

    left, right = parts

    left_str = "".join(simplify_power_side(left, var))
    right_str = "".join(simplify_power_side(right, var))
    
    return f"{left_str}={right_str}"


def simplify_power_side(side, var):
    simplified = []
    current_term = ""

    for i, char in enumerate(side):
        if char in "+-":
            if i == 0 or side[i - 1] in "^eE":
                current_term += char
                continue

            if "^" in current_term:
                if var in current_term:
                    simplified.append(simplify_power_term(current_term, var))
                else:
                    simplified.append(simplify_power_term(current_term))
            else:
                simplified.append(current_term)

            current_term = char
        else:
            current_term += char

    if current_term and "^" in current_term:
        if var in current_term:
            simplified.append(simplify_power_term(current_term, var))
        else:
            simplified.append(simplify_power_term(current_term))
    elif current_term:
        simplified.append(current_term)
    
    return simplified


def simplify_power_term(term, var = ""):
    if not term:
        return

    tmp = term

    if term[0] == "+":
        term = term[1:]

    if var == "":
        return power(term)
        
    if term.startswith(var):
        term = "1" + term
    elif term.startswith(f"-{var}"):
        term = "-1" + term[1:]

    # "3x^2^1" -> exponent part "2^1" gets reduced to "2" via power(), giving "3x^2"
    if f"{var}^" in term:
        exp_start = term.rfind(f"{var}^") + 2
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
        term = term.replace(f"{var}^0", "")
    elif f"{var}^1" in term:
        term = term.replace(f"{var}^1", var)
    
    return f"+{term}" if tmp[0] == "+" else term


def fix_false_quadratic(equation, var):
    """
    Detect equations that *look* quadratic (they contain "var^2" terms)
    but are actually linear because every "var^2" term cancels out once
    the equation is balanced (e.g. "x^2-x^2=0", or "x^2+3x-x^2=5").

    This is meant to run AFTER simplify_power_eq, since it relies on every
    "var^2" term already having an explicit, standalone numeric coefficient
    (e.g. "x^2" -> "1x^2", "-x^2" -> "-1x^2").

    How it works:
    1. Collect every "var^2" term's coefficient on each side of "=".
    2. Move everything to one side conceptually: net_coefficient =
       (sum of coefficients on the left) - (sum of coefficients on the right).
    3. If net_coefficient is 0, the "var^2" terms cancel each other out
       completely, meaning the equation never actually behaves like a
       quadratic. In that case, strip the "^2" from every "var^2" term
       (turning it into a plain "var" term) and return the fixed equation.
    4. Otherwise (a real quadratic, or no "var^2" terms at all), return the
       equation unchanged.

    Note: stripping "^2" this way keeps the equation mathematically
    equivalent, since the matched terms still carry the exact same
    coefficients and therefore still cancel out to 0 once reduced to
    power 1.
    """
    left, right = equation.split("=")

    # Matches a signed numeric coefficient directly followed by "var^2",
    # e.g. "1x^2", "-1x^2", "2.5x^2".
    coefficient_pattern = rf"([+-]?\d+(?:\.\d+)?){re.escape(var)}\^2"

    left_coefficients = [float(c) for c in re.findall(coefficient_pattern, left)]
    right_coefficients = [float(c) for c in re.findall(coefficient_pattern, right)]

    if not left_coefficients and not right_coefficients:
        # No "var^2" terms at all, nothing to check/fix.
        return equation

    net_coefficient = sum(left_coefficients) - sum(right_coefficients)

    if abs(net_coefficient) > 1e-10:
        # The "var^2" terms don't fully cancel out, so this is a genuine
        # quadratic equation. Leave it as it is.
        return equation

    # The "var^2" terms cancel out completely -> this is really a linear
    # equation wearing a quadratic disguise. Strip the "^2" everywhere.
    term_pattern = rf"({re.escape(var)})\^2"
    fixed_left = re.sub(term_pattern, r"\1", left)
    fixed_right = re.sub(term_pattern, r"\1", right)

    return f"{fixed_left}={fixed_right}"


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
