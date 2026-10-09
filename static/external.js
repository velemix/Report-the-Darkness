const form = document.getElementById('complaintForm');
form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const complaint = document.getElementById('complaintInput').value;

    const response = await fetch('/complaint', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ complaint })
    });

    const result = await response.json();
    document.getElementById('result').textContent = result.result;
});