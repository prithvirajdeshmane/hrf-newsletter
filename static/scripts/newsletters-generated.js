// HRF Newsletter Generator - Newsletters Generated Page JavaScript
// Consolidated script for all newsletters-generated.html functionality

document.addEventListener('DOMContentLoaded', function() {
    
    /**
     * Navigate back to the build newsletter page.
     * The country is already stored in the session, so no parameters needed.
     */
    function goBackToEditor() {
        // Navigate back to the build newsletter page (country is already in session)
        window.location.href = '/build-newsletter';
    }

    /**
     * Handle Mailchimp upload functionality.
     * Makes POST request to upload images, then uploads newsletters.
     */
    function uploadToMailchimp() {
        // Show loading state
        const uploadBtn = document.querySelector('button[onclick="uploadToMailchimp()"]');
        const originalText = uploadBtn.innerHTML;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading Images...';
        uploadBtn.disabled = true;
        
        // Make POST request to upload images
        fetch('/newsletters-generated', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(imageData => {
            // Check if image upload was successful
            if (!imageData.success) {
                throw new Error(imageData.message || 'Image upload failed');
            }
            
            // Update button text for newsletter upload
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading Newsletters...';
            
            // Upload newsletters after successful image upload
            return fetch('/api/upload-newsletters', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: null  // Will use session from Flask session
                })
            });
        })
        .then(response => response.json())
        .then(newsletterData => {
            // Check if newsletter upload was successful
            if (newsletterData.success) {
                // Redirect to success page
                window.location.href = newsletterData.redirect_url;
            } else {
                throw new Error(newsletterData.error || 'Newsletter upload failed');
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            alert(`Upload failed: ${error.message}`);
        })
        .finally(() => {
            // Restore button state
            uploadBtn.innerHTML = originalText;
            uploadBtn.disabled = false;
        });
    }

    // Make functions globally accessible for onclick handlers
    window.goBackToEditor = goBackToEditor;
    window.uploadToMailchimp = uploadToMailchimp;
});
