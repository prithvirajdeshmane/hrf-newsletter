// HRF Newsletter Generator - Index Page JavaScript
// Simplified script for newsletter form functionality

document.addEventListener('DOMContentLoaded', function() {
    // DOM element references
    const newsletterForm = document.getElementById('newsletterForm');
    const countrySelect = document.getElementById('country');

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
});
