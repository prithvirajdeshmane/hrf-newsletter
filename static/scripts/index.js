// Scripts for index.html
// Show credentials modal if creds_ok is false (from Flask)
// (handled by template logic below)

// If creds_ok is false, show modal on DOMContentLoaded
window.addEventListener('DOMContentLoaded', function() {
    if (typeof creds_ok !== 'undefined' && !creds_ok) {
        document.getElementById('credentialsModal').style.display = 'block';
    }
});

// Handle credentials form submission
if (document.getElementById('credentialsForm')) {
    document.getElementById('credentialsForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const apiKey = document.getElementById('apiKey').value;
        const serverPrefix = document.getElementById('serverPrefix').value;
        try {
            const response = await fetch('/api/save-credentials', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    api_key: apiKey,
                    server_prefix: serverPrefix
                })
            });
            if (response.ok) {
                document.getElementById('credentialsModal').style.display = 'none';
                // Credentials saved successfully - modal closes silently
            } else {
                const result = await response.json();
                const errorMessage = result.error || 'Error saving credentials. Please try again.';
                alert(errorMessage);
            }
        } catch (error) {
            console.error('Error saving credentials:', error);
            alert('Network error. Please check your connection and try again.');
        }
    });
}

// Handle newsletter building
if (document.getElementById('newsletterForm')) {
    document.getElementById('newsletterForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const selectedCountry = document.getElementById('country').value;
        if (!selectedCountry) {
            alert('Please select a country');
            return;
        }
        // Navigate to build-newsletter page with only country parameter
        const params = new URLSearchParams({
            country: selectedCountry
        });
        window.location.href = `/build-newsletter?${params.toString()}`;
    });
}

// Open credentials modal on CTA click
if (document.getElementById('editCredentialsLink')) {
    document.getElementById('editCredentialsLink').addEventListener('click', function(event) {
        event.preventDefault();
        document.getElementById('credentialsModal').style.display = 'block';
    });
}
if (document.getElementById('closeModal')) {
    document.getElementById('closeModal').addEventListener('click', function() {
        document.getElementById('credentialsModal').style.display = 'none';
    });
}
