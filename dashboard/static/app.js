const compareBtn = document.getElementById("compareBtn");

compareBtn.addEventListener("click", async () => {

    const expected =
        document.getElementById("expected").files[0];

    const actual =
        document.getElementById("actual").files[0];

    if (!expected || !actual) {

        alert("Please select both PDF files.");

        return;
    }

    document.getElementById("results").classList.add("hidden");

    document.getElementById("loading").classList.remove("hidden");

    const formData = new FormData();

    formData.append("expected", expected);

    formData.append("actual", actual);

    const response = await fetch("/compare", {

        method: "POST",

        body: formData

    });

    const data = await response.json();

    document.getElementById("loading").classList.add("hidden");

    if (!data.success) {

        alert(data.message);

        return;
    }

    document.getElementById("results").classList.remove("hidden");

    document.getElementById("alignedPairs").innerText =
        data.aligned_pairs;

    document.getElementById("totalDifferences").innerText =
        data.total;

    document.getElementById("formattingCount").innerText =
        data.summary.formatting || 0;

    document.getElementById("wordCount").innerText =
        data.summary.word || 0;

    document.getElementById("characterCount").innerText =
        data.summary.character || 0;

    document.getElementById("numberCount").innerText =
        data.summary.number || 0;

    const logs = document.getElementById("logs");

    logs.innerHTML = "";

    data.logs.forEach(log => {

        logs.innerHTML += `

        <div class="log">

            <h4>${log.category.toUpperCase()}</h4>

            <p><strong>Expected:</strong> ${log.expected ?? "-"}</p>

            <p><strong>Actual:</strong> ${log.actual ?? "-"}</p>

            <p>${log.description}</p>

        </div>

        `;

    });

});