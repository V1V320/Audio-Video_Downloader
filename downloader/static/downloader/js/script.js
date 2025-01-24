document.getElementById('downloadBtn').addEventListener('click', async function() {
    const links = document.getElementById('links').value.split(',').map(link => link.trim());
    const option = document.getElementById('option').value;

    if (links.length === 0) {
        document.getElementById('result').textContent = "Please enter at least one link.";
        return;
    }

    const response = await fetch('/api/download/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ links: links, option: option })
    });

    const result = await response.json();
    if (response.ok) {
        document.getElementById('result').textContent = result.message || "Download started.";
    } else {
        document.getElementById('result').textContent = result.error || "An error occurred.";
    }
});
