// ======================================================
// HELPER
// ======================================================

const $ = (id) =>
    document.getElementById(id);


// ======================================================
// API HELPER
// ======================================================

async function api(
    url,
    options = {}
) {

    const response = await fetch(
        url,
        {
            headers: {
                "Content-Type":
                    "application/json",

                ...(options.headers || {})
            },

            ...options
        }
    );


    const data =
        await response
            .json()
            .catch(
                () => ({})
            );


    if (!response.ok) {

        throw new Error(
            data.error ||
            `Request failed (${response.status})`
        );

    }


    return data;
}


// ======================================================
// MONEY FORMATTER
// ======================================================

function money(value) {

    return `₹${Number(
        value || 0
    ).toFixed(2)}`;

}


// ======================================================
// HTML ESCAPING
// ======================================================

function escapeHtml(value) {

    return String(
        value ?? ""
    ).replace(
        /[&<>"']/g,

        (character) => ({

            "&": "&amp;",

            "<": "&lt;",

            ">": "&gt;",

            '"': "&quot;",

            "'": "&#039;"

        }[character])
    );

}


// ======================================================
// LOAD DASHBOARD
// ======================================================

async function loadDashboard() {

    const data =
        await api(
            "/api/dashboard"
        );


    $("total").textContent =
        money(data.total);


    $("count").textContent =
        data.count;


    $("topCategory").textContent =
        data.categories[0]?.category
        || "—";


    // --------------------------------------------
    // CATEGORY LIST
    // --------------------------------------------

    const max = Math.max(
        ...data.categories.map(
            x => Number(x.total)
        ),
        1
    );


    $("categories").innerHTML =
        data.categories.length

        ?

        data.categories
            .map(
                x => `

                    <div class="category-item">

                        <b>
                            ${escapeHtml(
                                x.category
                            )}
                        </b>

                        <div class="bar">

                            <span
                                style="
                                    width:
                                    ${(Number(x.total) / max) * 100}%
                                "
                            ></span>

                        </div>

                        <strong>
                            ${money(x.total)}
                        </strong>

                    </div>

                `
            )
            .join("")

        :

        `
            <p class="muted">
                No expenses yet.
            </p>
        `;


    // --------------------------------------------
    // EXPENSES
    // --------------------------------------------

    const expenses =
        await api(
            "/api/expenses"
        );


    $("expenseRows").innerHTML =
        expenses.length

        ?

        expenses
            .map(
                x => `

                    <tr>

                        <td>
                            ${escapeHtml(
                                x.title
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                x.category
                            )}
                        </td>

                        <td>
                            ${money(
                                x.amount
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                new Date(
                                    x.spent_at
                                ).toLocaleString()
                            )}
                        </td>

                        <td>

                            <button
                                class="action delete"
                                onclick="
                                    removeExpense(
                                        ${x.id}
                                    )
                                "
                            >
                                Delete
                            </button>

                        </td>

                    </tr>

                `
            )
            .join("")

        :

        `

            <tr>

                <td
                    colspan="5"
                    class="muted"
                >
                    No expenses saved.
                </td>

            </tr>

        `;
}


// ======================================================
// DELETE EXPENSE
// ======================================================

async function removeExpense(id) {

    if (
        !confirm(
            "Delete this expense?"
        )
    ) {

        return;

    }


    try {

        await api(
            `/api/expenses/${id}`,

            {
                method:
                    "DELETE"
            }
        );


        await loadDashboard();

    }

    catch (error) {

        alert(
            error.message
        );

    }

}


// ======================================================
// AI EXPENSE PARSER
// ======================================================

async function parseQuickEntry() {

    const text =
        $("quickText")
            .value
            .trim();


    if (!text) {

        alert(
            "Enter something like coffee 120."
        );

        return;

    }


    $("parseBtn").disabled =
        true;


    try {

        const data =
            await api(
                "/api/ai/parse-expense",

                {
                    method:
                        "POST",

                    body:
                        JSON.stringify({
                            text
                        })
                }
            );


        const result =
            data.result;


        $("parsePreview")
            .classList
            .remove("hidden");


        $("parsePreview").innerHTML = `

            <b>
                ${escapeHtml(
                    result.title
                )}
            </b>

            •

            ${money(
                result.amount
            )}

            •

            ${escapeHtml(
                result.category
            )}

            <br>

            <button
                id="useParsed"
                class="action"
            >
                Use in form
            </button>

        `;


        $("useParsed").onclick =
            () => {

                $("title").value =
                    result.title;


                $("amount").value =
                    result.amount;


                $("category").value =
                    result.category;


                $("note").value =
                    result.note || "";


                window.scrollTo({

                    top:
                        $("expenseForm")
                            .getBoundingClientRect()
                            .top
                        +
                        window.scrollY
                        -
                        80,

                    behavior:
                        "smooth"

                });

            };

    }

    catch (error) {

        alert(
            error.message
        );

    }

    finally {

        $("parseBtn").disabled =
            false;

    }

}


// ======================================================
// SAVE EXPENSE
// ======================================================

async function saveExpense(
    event
) {

    event.preventDefault();


    try {

        const spent =
            $("spentAt").value

            ?

            new Date(
                $("spentAt").value
            ).toISOString()

            :

            new Date().toISOString();


        await api(
            "/api/expenses",

            {

                method:
                    "POST",

                body:
                    JSON.stringify({

                        title:
                            $("title")
                                .value
                                .trim(),

                        amount:
                            Number(
                                $("amount")
                                    .value
                            ),

                        category:
                            $("category")
                                .value,

                        note:
                            $("note")
                                .value
                                .trim(),

                        spent_at:
                            spent

                    })

            }
        );


        event.target.reset();


        await loadDashboard();


        alert(
            "Expense saved."
        );

    }

    catch (error) {

        alert(
            error.message
        );

    }

}


// ======================================================
// AI INSIGHTS
// ======================================================

async function generateInsights() {

    $("insights").textContent =
        "Generating...";


    try {

        const data =
            await api(
                "/api/ai/insights",

                {

                    method:
                        "POST",

                    body:
                        "{}"

                }
            );


        $("insights").textContent =
            data.result;

    }

    catch (error) {

        $("insights").textContent =
            error.message;

    }

}


// ======================================================
// AI RECOMMENDATIONS
// ======================================================

async function generateRecommendation(
    event
) {

    event.preventDefault();


    $("recommendation")
        .textContent =
            "Generating...";


    try {

        const data =
            await api(
                "/api/ai/recommend",

                {

                    method:
                        "POST",

                    body:
                        JSON.stringify({

                            budget:
                                Number(
                                    $("budget")
                                        .value
                                ),

                            goal:
                                $("goal")
                                    .value
                                    .trim(),

                            preferences:
                                $("preferences")
                                    .value
                                    .trim()

                        })

                }
            );


        $("recommendation")
            .textContent =
                data.result;

    }

    catch (error) {

        $("recommendation")
            .textContent =
                error.message;

    }

}


// ======================================================
// LOAD AI HISTORY
// ======================================================

async function loadHistory() {

    const data =
        await api(
            "/api/history"
        );


    $("history").innerHTML =
        data.length

        ?

        data
            .map(
                x => `

                    <div
                        class="history-item"
                    >

                        <b>
                            ${escapeHtml(
                                x.action
                            )}
                        </b>

                        <small>
                            ${escapeHtml(
                                new Date(
                                    x.created_at
                                ).toLocaleString()
                            )}
                        </small>

                        <div>

                            <b>
                                Input:
                            </b>

                            ${escapeHtml(
                                x.input_text
                            )}

                        </div>

                        <pre>
${escapeHtml(
    x.output_text
)}
                        </pre>

                    </div>

                `
            )
            .join("")

        :

        `

            <p class="muted">
                No AI history yet.
            </p>

        `;
}


// ======================================================
// HEALTH CHECK
// ======================================================

async function checkHealth() {

    try {

        const data =
            await api(
                "/api/health"
            );


        $("healthBadge")
            .textContent =

            data.gemini_configured

            ?

            "API online • Gemini configured"

            :

            "API online • local AI fallback";

    }

    catch {

        $("healthBadge")
            .textContent =
                "API unavailable";

    }

}


// ======================================================
// EVENT LISTENERS
// ======================================================

$("parseBtn").onclick =
    parseQuickEntry;


$("expenseForm")
    .addEventListener(
        "submit",
        saveExpense
    );


$("insightsBtn").onclick =
    generateInsights;


$("recommendForm")
    .addEventListener(
        "submit",
        generateRecommendation
    );


$("historyBtn").onclick =
    loadHistory;


$("refreshBtn").onclick =
    loadDashboard;


// ======================================================
// START APPLICATION
// ======================================================

loadDashboard()
    .catch(
        error =>
            console.error(error)
    );


checkHealth();
