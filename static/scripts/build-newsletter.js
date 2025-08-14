// HRF Newsletter Generator - Build Newsletter Page JavaScript
// Consolidated script for all build-newsletter.html functionality

document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    const urlParams = new URLSearchParams(window.location.search);
    const selectedCountry = urlParams.get('country');
    let selectedLanguages = [];
    
    // Initialize country display
    const selectedCountryElement = document.getElementById('selectedCountry');
    if (selectedCountryElement) {
        selectedCountryElement.textContent = selectedCountry || 'Not selected';
    }
    
    // Fetch and display country languages
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
                const selectedLanguagesElement = document.getElementById('selectedLanguages');
                if (selectedLanguagesElement) {
                    selectedLanguagesElement.innerHTML = languagesHtml;
                }
            }
        } catch (error) {
            console.error('Error fetching country languages:', error);
            const selectedLanguagesElement = document.getElementById('selectedLanguages');
            if (selectedLanguagesElement) {
                selectedLanguagesElement.innerHTML = 'Error loading languages';
            }
        }
    }
    
    // Initialize country languages
    fetchCountryLanguages();

    // Utility functions
    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    // Get image data from input field (returns the URL value)


    function triggerFileInput(fileInputId) {
        document.getElementById(fileInputId).click();
    }

    function setupFileInput(textInputId, fileInputId) {
        const fileInput = document.getElementById(fileInputId);
        const textInput = document.getElementById(textInputId);
        
        if (!fileInput || !textInput) return;
        
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
        
        if (!input || !errorDiv) return;
        
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

    // Helper functions for DOM element creation
    function createElement(tag, className = '', textContent = '') {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (textContent) element.textContent = textContent;
        return element;
    }

    function createFormGroup(labelText, inputId, inputType = 'text', placeholder = '', hasError = false) {
        const group = createElement('div', 'form-group');
        
        const label = createElement('label');
        label.setAttribute('for', inputId);
        label.textContent = labelText;
        
        const input = createElement('input');
        input.type = inputType;
        input.id = inputId;
        input.placeholder = placeholder;
        
        group.append(label, input);
        
        if (hasError) {
            const errorDiv = createElement('div', 'error-message');
            errorDiv.id = `${inputId}Error`;
            group.appendChild(errorDiv);
        }
        
        return group;
    }

    function createFileInputGroup(labelText, textInputId, fileInputId, placeholder = '') {
        const group = createElement('div', 'form-group');
        
        const label = createElement('label');
        label.setAttribute('for', textInputId);
        label.textContent = labelText;
        
        const fileInputGroup = createElement('div', 'file-input-group');
        
        const textInput = createElement('input');
        textInput.type = 'text';
        textInput.id = textInputId;
        textInput.placeholder = placeholder;
        
        const fileButton = createElement('button', 'file-btn', 'Select File');
        fileButton.type = 'button';
        fileButton.setAttribute('onclick', `triggerFileInput('${fileInputId}')`);
        
        const fileInput = createElement('input', 'hidden-file-input');
        fileInput.type = 'file';
        fileInput.id = fileInputId;
        fileInput.accept = '.jpg,.jpeg,.png';
        
        const errorDiv = createElement('div', 'error-message');
        errorDiv.id = `${textInputId}Error`;
        
        fileInputGroup.append(textInput, fileButton, fileInput);
        group.append(label, fileInputGroup, errorDiv);
        
        return group;
    }

    function generateCtaSections(count) {
        const container = document.getElementById('ctaSections');
        if (!container) return;
        
        container.innerHTML = '';
        for (let i = 1; i <= count; i++) {
            const ctaSection = createElement('div', 'cta-section');
            const title = createElement('h4', '', `CTA ${i}`);
            
            const textGroup = createFormGroup('Button Text:', `ctaText${i}`, 'text', "e.g. 'Donate Now', 'Volunteer'");
            const urlGroup = createFormGroup('CTA URL:', `ctaUrl${i}`, 'text', 'https://example.com/action', true);
            
            ctaSection.append(title, textGroup, urlGroup);
            container.appendChild(ctaSection);
        }
        
        // Setup validation for new CTA URL inputs
        for (let i = 1; i <= count; i++) {
            setupUrlValidation(`ctaUrl${i}`, `ctaUrl${i}Error`);
        }
    }

    function createSelectGroup(labelText, selectId, options, defaultValue = '') {
        const group = createElement('div', 'form-group');
        
        const label = createElement('label');
        label.setAttribute('for', selectId);
        label.textContent = labelText;
        
        const select = createElement('select');
        select.id = selectId;
        
        options.forEach(option => {
            const optionElement = createElement('option', '', option.text || option);
            optionElement.value = option.value || option;
            if (option.value === defaultValue || option === defaultValue) {
                optionElement.selected = true;
            }
            select.appendChild(optionElement);
        });
        
        group.append(label, select);
        return group;
    }

    function createCtaSection(i) {
        const ctaSection = createElement('div');
        ctaSection.id = `storyCtaSection${i}`;
        ctaSection.style.display = 'none';
        
        const textGroup = createFormGroup('Button Text:', `storyCtaText${i}`, 'text', "e.g. 'Donate', 'Volunteer'");
        const urlGroup = createFormGroup('CTA URL:', `storyCtaUrl${i}`, 'text', 'https://example.com/action', true);
        
        ctaSection.append(textGroup, urlGroup);
        return ctaSection;
    }

    function generateStorySections(count) {
        const container = document.getElementById('storySections');
        if (!container) return;
        
        container.innerHTML = '';
        for (let i = 1; i <= count; i++) {
            const storySection = createElement('div', 'container-section');
            const title = createElement('h3', '', `Story ${i}:`);
            
            // Create form groups
            const imageGroup = createFileInputGroup(
                'Story Image (JPG or PNG):', 
                `storyImage${i}`, 
                `storyImageFile${i}`, 
                'Enter image URL or select file'
            );
            
            const altGroup = createFormGroup(
                'Image alt:', 
                `storyImageAlt${i}`, 
                'text', 
                "e.g., 'Community members at a peaceful demonstration'"
            );
            
            const headlineGroup = createFormGroup(
                'Headline:', 
                `storyHeadline${i}`, 
                'text', 
                "e.g., 'Local Community Stands Up for Justice'"
            );
            
            const descriptionGroup = createFormGroup(
                'Description:', 
                `storyDescription${i}`, 
                'text', 
                "e.g., 'Residents organize peaceful protest to demand accountability...'"
            );
            
            const urlGroup = createFormGroup(
                'Story URL:', 
                `storyUrl${i}`, 
                'text', 
                'https://example.com/story', 
                true
            );
            
            const ctaSelectGroup = createSelectGroup(
                'CTA button:', 
                `storyCta${i}`, 
                [{value: 'No', text: 'No'}, {value: 'Yes', text: 'Yes'}], 
                'No'
            );
            
            const ctaSection = createCtaSection(i);
            
            // Assemble the story section
            storySection.append(
                title, 
                imageGroup, 
                altGroup, 
                headlineGroup, 
                descriptionGroup, 
                urlGroup, 
                ctaSelectGroup, 
                ctaSection
            );
            
            container.appendChild(storySection);
        }
        
        // Setup file inputs and URL validation for new story sections
        for (let i = 1; i <= count; i++) {
            setupFileInput(`storyImage${i}`, `storyImageFile${i}`);
            setupUrlValidation(`storyUrl${i}`, `storyUrl${i}Error`);
            setupUrlValidation(`storyCtaUrl${i}`, `storyCtaUrl${i}Error`);
            
            // Setup CTA dropdown toggle functionality
            const ctaSelect = document.getElementById(`storyCta${i}`);
            const ctaSection = document.getElementById(`storyCtaSection${i}`);
            
            if (ctaSelect && ctaSection) {
                ctaSelect.addEventListener('change', function() {
                    if (this.value === 'Yes') {
                        ctaSection.style.display = 'block';
                    } else {
                        ctaSection.style.display = 'none';
                        // Clear CTA fields when hiding
                        const ctaText = document.getElementById(`storyCtaText${i}`);
                        const ctaUrl = document.getElementById(`storyCtaUrl${i}`);
                        if (ctaText) ctaText.value = '';
                        if (ctaUrl) ctaUrl.value = '';
                    }
                });
            }
        }
    }

    function getImageData(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return '';
        
        const fileData = input.getAttribute('data-file-data');
        const isFileSelected = input.getAttribute('data-file-selected') === 'true';
        
        if (isFileSelected && fileData) {
            return fileData;
        } else {
            return input.value.trim();
        }
    }

    // Event listeners for dynamic sections
    const ctaCountSelect = document.getElementById('ctaCount');
    if (ctaCountSelect) {
        ctaCountSelect.addEventListener('change', function() {
            generateCtaSections(parseInt(this.value));
        });
    }

    const storyCountSelect = document.getElementById('storyCount');
    if (storyCountSelect) {
        storyCountSelect.addEventListener('change', function() {
            generateStorySections(parseInt(this.value));
        });
    }

    // Setup initial file inputs and URL validation
    setupFileInput('heroImage', 'heroImageFile');
    setupUrlValidation('learnMoreUrl', 'learnMoreUrlError');

    // Newsletter form submission handler
    const newsletterForm = document.getElementById('newsletterBuildForm');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const heroImage = document.getElementById('heroImage');
            if (!heroImage || !heroImage.value.trim()) {
                alert('Please provide a hero image');
                return;
            }
            
            const generateBtn = document.getElementById('generateBtn');
            const loadingDiv = document.getElementById('loadingSpinner');
            
            if (generateBtn) generateBtn.disabled = true;
            if (loadingDiv) {
                loadingDiv.classList.add('show');
                loadingDiv.classList.remove('hide');
            }
            
            try {
                const formData = collectFormData();
                
                // Submit form data
                await submitNewsletterForm(formData);
            } catch (error) {
                console.error('Error generating newsletter:', error);
                alert('Error generating newsletter. Please try again.');
            } finally {
                if (generateBtn) generateBtn.disabled = false;
                if (loadingDiv) {
                    loadingDiv.classList.add('hide');
                    loadingDiv.classList.remove('show');
                }
            }
        });
    }

    // Helper functions for form data collection
    function collectHeroData() {
        const heroImageData = getImageData('heroImage');
        return {
            image: heroImageData,
            imageAlt: document.getElementById('heroImageAlt')?.value.trim() || '',
            headline: document.getElementById('heroHeadline')?.value.trim() || '',
            description: document.getElementById('heroDescription')?.value.trim() || '',
            learnMoreUrl: document.getElementById('learnMoreUrl')?.value.trim() || ''
        };
    }

    function collectCtaData() {
        const ctas = [];
        const ctaCount = parseInt(ctaCountSelect?.value || 0);
        
        for (let i = 1; i <= ctaCount; i++) {
            const textElement = document.getElementById(`ctaText${i}`);
            const urlElement = document.getElementById(`ctaUrl${i}`);
            const text = textElement?.value.trim();
            const url = urlElement?.value.trim();
            
            if (text && url) {
                ctas.push({ text, url });
            }
        }
        
        return ctas;
    }

    function collectStoryCta(storyIndex) {
        const ctaSelect = document.getElementById(`storyCta${storyIndex}`);
        const hasCta = ctaSelect?.value === 'Yes';
        
        if (!hasCta) return null;
        
        const ctaText = document.getElementById(`storyCtaText${storyIndex}`)?.value.trim() || '';
        const ctaUrl = document.getElementById(`storyCtaUrl${storyIndex}`)?.value.trim() || '';
        
        return (ctaText && ctaUrl) ? { text: ctaText, url: ctaUrl } : null;
    }

    function collectStoryData() {
        const stories = [];
        const storyCount = parseInt(storyCountSelect?.value || 0);
        
        for (let i = 1; i <= storyCount; i++) {
            const imageData = getImageData(`storyImage${i}`);
            const imageAlt = document.getElementById(`storyImageAlt${i}`)?.value.trim() || '';
            const headline = document.getElementById(`storyHeadline${i}`)?.value.trim() || '';
            const description = document.getElementById(`storyDescription${i}`)?.value.trim() || '';
            const url = document.getElementById(`storyUrl${i}`)?.value.trim() || '';
            
            if (imageData && url) {
                const storyData = { 
                    image: imageData, 
                    imageAlt, 
                    headline, 
                    description, 
                    url 
                };
                
                const cta = collectStoryCta(i);
                if (cta) {
                    storyData.cta = cta;
                }
                
                stories.push(storyData);
            }
        }
        
        return stories;
    }

    function collectFormData() {
        return {
            country: selectedCountry,
            languages: selectedLanguages ? selectedLanguages.join(',') : '',
            hero: collectHeroData(),
            ctas: collectCtaData(),
            stories: collectStoryData()
        };
    }

    async function submitNewsletterForm(formData) {
        const response = await fetch('/api/build-newsletter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Navigate to results page with generation data
            if (result.result_data) {
                const { country, total_newsletters, languages, filenames } = result.result_data;
                const params = new URLSearchParams({
                    country: country,
                    total: total_newsletters.toString(),
                    languages: languages.join(','),
                    filenames: filenames.join(',')
                });
                window.location.href = `/newsletters-generated?${params.toString()}`;
            } else {
                // Fallback for older API response format
                alert(`${result.message || 'Success'}`);
            }
        } else {
            alert(`Error generating newsletter: ${result.error || 'Unknown error'}`);
        }
    }

    // Make triggerFileInput globally accessible for onclick handlers
    window.triggerFileInput = triggerFileInput;

    // Initialize with default CTA and story sections
    generateCtaSections(parseInt(ctaCountSelect?.value || 0));
    generateStorySections(parseInt(document.getElementById('storyCount').value));
});
