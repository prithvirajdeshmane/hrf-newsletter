// Scripts for build-newsletter.html
const urlParams = new URLSearchParams(window.location.search);
const selectedCountry = urlParams.get('country');
let selectedLanguages = [];
document.getElementById('selectedCountry').textContent = selectedCountry || 'Not selected';
async function fetchCountryLanguages() {
    try {
        const response = await fetch('/api/countries');
        const countries = await response.json();
        if (selectedCountry && countries[selectedCountry]) {
            const languagesDict = countries[selectedCountry].languages || {};
            selectedLanguages = Object.keys(languagesDict);
            const languagesHtml = selectedLanguages.map(lang => 
                `<span class="language-tag">${lang}</span>`
            ).join('');
            document.getElementById('selectedLanguages').innerHTML = languagesHtml;
        }
    } catch (error) {
        console.error('Error fetching country languages:', error);
        document.getElementById('selectedLanguages').innerHTML = 'Error loading languages';
    }
}
fetchCountryLanguages();
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}
function triggerFileInput(fileInputId) {
    document.getElementById(fileInputId).click();
}
function setupFileInput(textInputId, fileInputId) {
    const fileInput = document.getElementById(fileInputId);
    const textInput = document.getElementById(textInputId);
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            const fileName = file.name;
            textInput.value = `📁 ${fileName}`;
            textInput.setAttribute('data-file-selected', 'true');
            const reader = new FileReader();
            reader.onload = function(e) {
                textInput.setAttribute('data-file-data', e.target.result);
                console.log(`File ${fileName} converted to base64 (${Math.round(e.target.result.length/1024)}KB)`);
            };
            reader.onerror = function() {
                console.error(`Failed to read file: ${fileName}`);
                textInput.value = '';
                textInput.removeAttribute('data-file-selected');
                textInput.removeAttribute('data-file-data');
            };
            reader.readAsDataURL(file);
        }
    });
}
function setupUrlValidation(inputId, errorId) {
    const input = document.getElementById(inputId);
    const errorDiv = document.getElementById(errorId);
    input.addEventListener('blur', function() {
        const value = this.value.trim();
        if (value && !isValidUrl(value)) {
            this.classList.add('error');
            errorDiv.textContent = 'Please enter a valid URL';
        } else {
            this.classList.remove('error');
            errorDiv.textContent = '';
        }
    });
}
function generateCtaSections(count) {
    const container = document.getElementById('ctaSections');
    container.innerHTML = '';
    for (let i = 1; i <= count; i++) {
        const ctaHtml = `
            <div class="cta-section">
                <h4>CTA ${i}</h4>
                <div class="form-group">
                    <label for="ctaText${i}">Button Text:</label>
                    <input type="text" id="ctaText${i}" placeholder="e.g. 'Donate Now', 'Volunteer'">
                </div>
                <div class="form-group">
                    <label for="ctaUrl${i}">CTA URL:</label>
                    <input type="text" id="ctaUrl${i}" placeholder="https://example.com/action">
                    <div class="error-message" id="ctaUrl${i}Error"></div>
                </div>
            </div>
        `;
        container.innerHTML += ctaHtml;
    }
    for (let i = 1; i <= count; i++) {
        setupUrlValidation(`ctaUrl${i}`, `ctaUrl${i}Error`);
    }
}
function generateStorySections(count) {
    const container = document.getElementById('storySections');
    container.innerHTML = '';
    for (let i = 1; i <= count; i++) {
        const storyHtml = `
            <div class="container-section">
                <h3>Story ${i}:</h3>
                <div class="form-group">
                    <label for="storyImage${i}">Story Image (JPG or PNG):</label>
                    <div class="file-input-group">
                        <input type="text" id="storyImage${i}" placeholder="Enter image URL or select file">
                        <button type="button" class="file-btn" onclick="triggerFileInput('storyImageFile${i}')">Select File</button>
                        <input type="file" id="storyImageFile${i}" class="hidden-file-input" accept=".jpg,.jpeg,.png">
                    </div>
                    <div class="error-message" id="storyImage${i}Error"></div>
                </div>
                <div class="form-group">
                    <label for="storyImageAlt${i}">Image alt:</label>
                    <input type="text" id="storyImageAlt${i}" placeholder="e.g., 'Community members at a peaceful demonstration'">
                </div>
                <div class="form-group">
                    <label for="storyHeadline${i}">Headline:</label>
                    <input type="text" id="storyHeadline${i}" placeholder="e.g., 'Local Community Stands Up for Justice'">
                </div>
                <div class="form-group">
                    <label for="storyDescription${i}">Description:</label>
                    <input type="text" id="storyDescription${i}" placeholder="e.g., 'Residents organize peaceful protest to demand accountability...'">
                </div>
                <div class="form-group">
                    <label for="storyUrl${i}">Story URL:</label>
                    <input type="text" id="storyUrl${i}" placeholder="https://example.com/story">
                    <div class="error-message" id="storyUrl${i}Error"></div>
                </div>
            </div>
        `;
        container.innerHTML += storyHtml;
    }
    for (let i = 1; i <= count; i++) {
        setupFileInput(`storyImage${i}`, `storyImageFile${i}`);
        setupUrlValidation(`storyUrl${i}`, `storyUrl${i}Error`);
    }
}
document.getElementById('ctaCount').addEventListener('change', function() {
    generateCtaSections(parseInt(this.value));
});
document.getElementById('storyCount').addEventListener('change', function() {
    generateStorySections(parseInt(this.value));
});
setupFileInput('heroImage', 'heroImageFile');
setupUrlValidation('learnMoreUrl', 'learnMoreUrlError');
document.getElementById('newsletterBuildForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const heroImage = document.getElementById('heroImage').value.trim();
    if (!heroImage) {
        alert('Please provide a hero image');
        return;
    }
    document.getElementById('generateBtn').disabled = true;
    document.getElementById('loadingDiv').style.display = 'block';
    try {
        function getImageData(inputId) {
            const input = document.getElementById(inputId);
            const fileData = input.getAttribute('data-file-data');
            const isFileSelected = input.getAttribute('data-file-selected') === 'true';
            if (isFileSelected && fileData) {
                return fileData;
            } else {
                return input.value.trim();
            }
        }
        const heroImageData = getImageData('heroImage');
        const formData = {
            country: selectedCountry,
            languages: selectedLanguages ? selectedLanguages.join(',') : '',
            hero: {
                image: heroImageData,
                imageAlt: document.getElementById('heroImageAlt').value.trim(),
                headline: document.getElementById('heroHeadline').value.trim(),
                description: document.getElementById('heroDescription').value.trim(),
                learnMoreUrl: document.getElementById('learnMoreUrl').value.trim()
            },
            ctas: [],
            stories: []
        };
        const ctaCount = parseInt(document.getElementById('ctaCount').value);
        for (let i = 1; i <= ctaCount; i++) {
            const text = document.getElementById(`ctaText${i}`).value.trim();
            const url = document.getElementById(`ctaUrl${i}`).value.trim();
            if (text && url) {
                formData.ctas.push({ text, url });
            }
        }
        const storyCount = parseInt(document.getElementById('storyCount').value);
        for (let i = 1; i <= storyCount; i++) {
            const imageData = getImageData(`storyImage${i}`);
            const imageAlt = document.getElementById(`storyImageAlt${i}`).value.trim();
            const headline = document.getElementById(`storyHeadline${i}`).value.trim();
            const description = document.getElementById(`storyDescription${i}`).value.trim();
            const url = document.getElementById(`storyUrl${i}`).value.trim();
            if (imageData && url) {
                formData.stories.push({ 
                    image: imageData, 
                    imageAlt, 
                    headline, 
                    description, 
                    url 
                });
            }
        }
        const response = await fetch('/api/build-newsletter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        const result = await response.json();
        if (response.ok) {
            if (result.local_files && result.local_files.length > 0) {
                alert(`Newsletter(s) generated successfully!\n\nGenerated files:\n${result.local_files.join('\n')}`);
            } else {
                alert(`${result.message || 'Success'}`);
            }
        } else {
            alert(`Error generating newsletter: ${result.error || 'Unknown error'}`);
        }
    } catch (error) {
        alert('Error generating newsletter. Please try again.');
        console.error('Newsletter generation error:', error);
    } finally {
        document.getElementById('generateBtn').disabled = false;
        document.getElementById('loadingDiv').style.display = 'none';
    }
});
// Initial setup for CTAs and Stories
window.addEventListener('DOMContentLoaded', function() {
    generateCtaSections(parseInt(document.getElementById('ctaCount').value));
    generateStorySections(parseInt(document.getElementById('storyCount').value));
});
