from flask import Flask, render_template, request, jsonify
from solver.equation import Equation

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/solve", methods=["POST"])
def solve():
    data = request.get_json()
    
    equations = data["equations"]
    equation = Equation(
        equations if len(equations) > 1 else equations[0]
    )

    return jsonify(equation.solve())
