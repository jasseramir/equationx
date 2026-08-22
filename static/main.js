let count = 1;

const fieldGroup = document.getElementById("fieldGroup");
const addBtn = document.getElementById("addBtn");
const submitBtn = document.getElementById("submitBtn");
const resultDiv = document.getElementById("result");

function updateNumbers() {
    const fields = fieldGroup.querySelectorAll(".single-field");
    
    fields.forEach((field, index) => {
        const numSpan = field.querySelector(".eq-num");
        const deleteBtn = field.querySelector(".delete-btn");

        if (numSpan) {
            numSpan.textContent = index + 1;
        }
        
        if (deleteBtn) {
            deleteBtn.disabled = fields.length === 1;
        }
    });

    count = fields.length + 1;
}

function insertInput() {
    const input = 
    `
      <div class="single-field">
        <label class="eq-label">Equation <span class="eq-num">${count}</span></label>

        <div class="input-container">
          <input
            type="text"
            class="eq-input"
            name="input${count}"
            placeholder="Your Equation"
            required
          />

          <button type="button" class="btn delete-btn" aria-label="Delete">
            <i class="ri-close-line"></i>
          </button>
        </div>
      </div>
    `;

    fieldGroup.insertAdjacentHTML('beforeend', input);
    updateNumbers(); 
}

function renderSuccessResult(data) {
    resultDiv.style.display = "flex";

    // status can be "Solved", "Infinite Solutions", "No Solution", "Not Quadratic".
    // equation.py can now also attach a "type" key ("Identity"/"Contradiction")
    // when it resolves the equation itself (e.g. "x^0=2" -> "1=2"), so we show
    // that alongside the status instead of dropping it silently.
    if (data.status && data.status !== "Solved") {
        const statusText = data.type
            ? `\\begin{gathered}\\text{${data.status}} \\\\ \\text{(${data.type})}\\end{gathered}`
            : `\\text{${data.status}}`;
        
        katex.render(statusText, resultDiv, {
            throwOnError: false,
            displayMode: true
        });
        return;
    }

    const latexLines = Object.entries(data)
        .filter(([key]) => key !== "status" && key !== "type") // these aren't variables, don't render them as ones
        .map(([key, val]) => {
            const formattedKey = key.replace(/(\d+)/g, '_{$1}'); // x1 -> x_{1}
            return `${formattedKey} &= ${val}`;
        });

    const latexString = `\\begin{aligned} ${latexLines.join(" \\\\ ")} \\end{aligned}`;

    katex.render(latexString, resultDiv, {
        throwOnError: false,
        displayMode: true
    });
}

function renderErrorResult() {
    resultDiv.style.display = "flex";
    
    katex.render("\\text{Can't Solve}", resultDiv, {
        throwOnError: false,
        displayMode: true
    });
}

if (addBtn) {
    addBtn.addEventListener("click", () => {
        insertInput();
    });
}

if (fieldGroup) {
    fieldGroup.addEventListener("click", function (e) {
        const fields = fieldGroup.querySelectorAll(".single-field");
        const deleteBtn = e.target.closest(".delete-btn");

        if (deleteBtn && fields.length > 1) {
            deleteBtn.closest(".single-field").remove();
            updateNumbers();
        }
    });
}

if (submitBtn) {
    submitBtn.addEventListener("click", async (e) => {
        e.preventDefault();

        const inputElems = fieldGroup.querySelectorAll(".eq-input");
        const equations = Array.from(inputElems).map(input => input.value.trim());

        try {
            const response = await fetch("/solve", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ equations })
            });
            
            if (!response.ok) {
                renderErrorResult();
                return;
            }

            const data = await response.json();
            renderSuccessResult(data);
        } catch (err) {
            renderErrorResult();
        }
    });
}

insertInput();
