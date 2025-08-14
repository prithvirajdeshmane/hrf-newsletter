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
     * Makes POST request to upload images and displays results in popup.
     */
    function uploadToMailchimp() {
        // Show loading state
        const uploadBtn = document.querySelector('button[onclick="uploadToMailchimp()"]');
        const originalText = uploadBtn.innerHTML;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        uploadBtn.disabled = true;
        
        // Make POST request to upload images
        fetch('/newsletters-generated', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Format results for display
            let message = `Upload Results:\n`;
            message += `Total Images: ${data.total_images}\n`;
            message += `Successful: ${data.successful_uploads}\n`;
            message += `Failed: ${data.failed_uploads}\n\n`;
            
            if (data.results && data.results.length > 0) {
                message += 'Image Details:\n';
                data.results.forEach(result => {
                    const status = result.status === 'success' ? '✅' : '❌';
                    let details = result.status === 'success' ? 'URL received' : result.error;
                    
                    // Add compression info for successful uploads
                    if (result.status === 'success' && result.compressed) {
                        const originalKB = Math.round(result.original_size / 1024);
                        const finalKB = Math.round(result.final_size / 1024);
                        details += ` (compressed: ${originalKB}KB → ${finalKB}KB)`;
                    }
                    
                    message += `${status} ${result.name}: ${details}\n`;
                });
            }
            
            // Display results in alert popup
            alert(message);
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
