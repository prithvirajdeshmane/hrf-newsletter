// HRF Newsletter Generator - Index Page JavaScript
// Consolidated script for all index.html functionality

document.addEventListener('DOMContentLoaded', function() {
    // DOM element references
    const newsletterForm = document.getElementById('newsletterForm');
    const countrySelect = document.getElementById('country');
    const credentialsModal = document.getElementById('credentialsModal');
    const credentialsForm = document.getElementById('credentialsForm');
    const editCredentialsLink = document.getElementById('editCredentialsLink');
    const closeModal = document.getElementById('closeModal');

    // Check if credentials modal should be shown based on server-side data attribute
    const showCredentialsModal = document.body.dataset.showCredentialsModal === 'true';
    if (showCredentialsModal && credentialsModal) {
        credentialsModal.classList.add('show');
    }

    // Newsletter form submission handler
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const selectedCountry = countrySelect.value;
            
            if (!selectedCountry) {
                alert('Please select a country');
                return;
            }
            
            try {
                // Store country in session via API
                const response = await fetch('/api/select-country', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        country: selectedCountry
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    // Navigate to clean build-newsletter URL
                    window.location.href = result.redirect_url;
                } else {
                    alert(result.error || 'Failed to select country. Please try again.');
                }
            } catch (error) {
                console.error('Error selecting country:', error);
                alert('Network error. Please check your connection and try again.');
            }
        });
    }

    // Credentials form submission handler
    if (credentialsForm) {
        credentialsForm.addEventListener('submit', async function(e) {
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
                    credentialsModal.classList.remove('show');
                    alert('Credentials saved successfully!');
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

    // Open credentials modal handler
    if (editCredentialsLink) {
        editCredentialsLink.addEventListener('click', function(event) {
            event.preventDefault();
            credentialsModal.classList.add('show');
        });
    }

    // Close credentials modal handler
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            credentialsModal.classList.remove('show');
        });
    }

    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === credentialsModal) {
            credentialsModal.classList.remove('show');
        }
    });
});
