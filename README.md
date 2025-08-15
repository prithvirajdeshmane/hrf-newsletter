# HRF Newsletter Generator

A comprehensive web-based tool for generating localized, multilingual email newsletters with automatic Mailchimp integration, RTL language support, and professional template management.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Features](#features)
- [Quick Start Guide](#quick-start-guide)
- [Mailchimp Integration](#mailchimp-integration)
- [Detailed Usage](#detailed-usage)
- [Troubleshooting](#troubleshooting)
- [Reference](#reference)

---

## Project Structure
```
hrf-newsletter/
├── app.py                             # Flask web application
├── scripts/
│   ├── DataManager.py                 # Country/language data management
│   ├── mailchimp_newsletter_uploader.py # Complete newsletter upload workflow
│   ├── mailchimp_image_uploader.py    # Image upload to Mailchimp
│   ├── image_utils.py                 # Image processing utilities
│   ├── translation_service.py         # Google Translate integration
│   └── env_utils.py                   # Environment variable utilities
├── templates/
│   ├── index.html                     # Country selection page
│   ├── build-newsletter.html          # Newsletter builder interface
│   ├── newsletters-generated.html     # Generation results page
│   ├── newsletters-uploaded.html      # Upload success page
│   └── newsletter_template.html       # Email template
├── static/
│   ├── scripts/                       # Frontend JavaScript
│   ├── styles/                        # CSS stylesheets
│   └── images/brand/                  # Brand assets (logo)
├── data/
│   └── country_languages.json         # Country/language configuration
├── generated_newsletters/             # Output directory (auto-created)
├── requirements.txt                   # Python dependencies
├── .env                              # Environment variables (create this)
└── README.md
```

## Prerequisites
- Python 3.7 or higher
- Mailchimp Marketing API account and credentials
- Internet connection for Mailchimp integration

## Setup
1. **Clone this repository**
   ```bash
   git clone <repository-url>
   cd hrf-newsletter
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Mailchimp API credentials**
   - Create a `.env` file in the project root
   - Add your Mailchimp API credentials:
     ```env
     MAILCHIMP_API_KEY=your_api_key_here
     MAILCHIMP_SERVER_PREFIX=your_server_prefix_here
     ```
   - Get these credentials from your Mailchimp account under Account > Extras > API keys

4. **Test your connection** (optional)
   ```bash
   python scripts/utils/test_mailchimp_connection.py
   ```

## Features

- **Web-Based Interface**: User-friendly browser interface for building newsletters with intuitive form controls.
- **RTL Language Support**: Full support for Right-to-Left languages (Arabic, Hebrew, Persian) with proper text direction.
- **Multi-Language Support**: Supports multiple languages per country with localized country names.
- **Google Translate Integration**: Automatic translation of newsletter content for non-English languages.
- **Image Processing**: Automatic image compression and optimization for web delivery.
- **Complete Mailchimp Integration**: 
  - **Automated Workflow**: Upload images → Replace URLs → Create templates in one click
  - **Image Upload**: Automatically uploads user images to Mailchimp Content Studio with 1MB compression
  - **URL Substitution**: Replaces local image paths with Mailchimp URLs in newsletter HTML
  - **Template Creation**: Uploads processed newsletters as ready-to-use Mailchimp templates
  - **Session Management**: Tracks uploads per user session for proper isolation
- **Professional UI**: Modern, responsive design with progress indicators and error handling
- **File Management**: Organized output with `mailchimp_versions` folders for processed templates

## Quick Start Guide

1. **Start the web application**:
   ```bash
   python app.py
   ```

2. **Open your browser** to `http://localhost:5000` (development mode)

3. **Build your newsletter**:
   - Select a country from the dropdown
   - Upload hero image and add headline/description
   - Add up to 2 story images with headlines and descriptions
   - Add call-to-action buttons

4. **Generate newsletters**:
   - Click "Generate Newsletter(s)"
   - Newsletters are created for each language supported by the selected country
   - Files are saved in `generated_newsletters/{Country_Name}/`

5. **Upload to Mailchimp** (optional):
   - Click "Upload to Mailchimp" on the results page
   - Images are automatically uploaded and URLs replaced
   - Newsletter templates are created in your Mailchimp account

## Mailchimp Integration

The application provides seamless integration with Mailchimp Marketing API:

### **Automated Upload Workflow**
1. **Image Processing**: User-uploaded images are compressed (if >1MB) and uploaded to Mailchimp Content Studio
2. **URL Substitution**: Local image references in HTML are replaced with Mailchimp-hosted URLs
3. **Template Creation**: Processed newsletters are uploaded as templates with descriptive names

### **Template Naming Convention**
Templates are named using the format: `{Country}_{Language}_{Date}_{Time}`
- Example: `Switzerland_French_081425_160015`

### **File Organization**
- Original newsletters: `generated_newsletters/{Country}/`
- Mailchimp-ready versions: `generated_newsletters/{Country}/mailchimp_versions/`

### **Session Management**
Each user session maintains isolated image uploads and processing to prevent conflicts between concurrent users.

## Detailed Usage

### 1. Country & Language Configuration
- Countries and languages are configured in `data/country_languages.json`
- Each country can support multiple languages with localized country names
- RTL languages (Arabic, Hebrew, etc.) use `"scriptDirection": "rtl"`

#### JSON Structure Example:
```json
{
  "Bahrain": {
    "countryCode": "BH",
    "languages": {
      "English": {
        "languageCode": "en",
        "locale": "en-BH"
      },
      "Arabic": {
        "languageCode": "ar",
        "locale": "ar-BH",
        "preferredName": "البحرين",
        "scriptDirection": "rtl"
      }
    }
  }
}
```

**Key Features:**
- `preferredName`: Localized country name in the target language
- `scriptDirection`: "rtl" for Right-to-Left languages (defaults to "ltr")
- `locale`: Full locale code for proper formatting
- Add your newsletter images to the `images/` directory:
  - **Brand images** (shared across all geos): Place in `images/brand/` (e.g., `images/brand/HRF-Logo.png`)
  - **Geo-specific images**: Place in `images/{geo}/` (e.g., `images/us/hero.jpg`, `images/ch/story-1.jpg`)
- **Important**: The script uploads ALL images from both `images/brand/` and `images/{geo}/` folders to Mailchimp, ensuring comprehensive image availability.

### 2. Generate Newsletters for a Geo
Run:
```bash
python scripts/generate_newsletter.py <geo>
```
Examples:
- `- `MAILCHIMP_API_KEY`: Your Mailchimp Marketing API key.
- `MAILCHIMP_SERVER_PREFIX`: The server prefix from your API key (e.g., `us21`).

### Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## 🚀 Setup Instructions

### 1. **Choose Your Geo (Country)**
- Select a `geo` code for the country you want to create a newsletter for.  
  Example: `us` for United States, `ca` for Canada, `mx` for Mexico, etc.
- Refer to [`COUNTRY_LANGUAGE_REFERENCE.md`](./COUNTRY_LANGUAGE_REFERENCE.md) for the list of supported country-language codes.

---

### 2. **Prepare Your JSON Configuration**
- The foundation name, footer text, and logo are hardcoded in the newsletter template.
- Add a new block for your country using the geo code.

Each geo must include the following:

#### 🔹 `hero` Section (Required)
- Contains the main news highlight.
- Must include:
  - `image_url`
  - `cta_learn_more_url` (optional)
  - `ctas_buttons` with one or more `url`s

#### 🔹 `stories` Section (Optional)
- You may include up to **two** additional stories.
- Each story must include:
  - `image_url`
  - `url`

#### 🔹 `translations` Section (Required)
- Define content in **each supported language** for the geo.
- For each language, include:
  - `lang` and `dir`
  - `metadata.country_name`
  - `hero` section with:
    - `image_alt`
    - `headline`
    - `description`
    - `ctas_buttons.text` (button labels)
  - Optional `stories` with:
    - `image_alt`
    - `headline`
    - `description`

> ⚠️ **Note:** Ensure your JSON structure is correct and follows the nesting pattern. Malformed JSON will break the template generation process.

---

### 3. **Add Image Assets**
- Create an image directory for your geo under the project’s `images/` folder.  
  Example:  
  ```
  images/us/
  ├── hero.jpg
  ├── story-1.jpg  (optional)
  └── story-2.jpg  (optional)
  ```
- **File names must match the following convention:**
  - `hero.jpg`
  - `story-1.jpg` (if used)
  - `story-2.jpg` (if used)

---

### 4. **Run the Program**
Once your JSON and images are in place:

```bash
# Example command to generate templates
python scripts/generate_newsletter.py <geo>
```

Templates will be created for **each language** defined in the `translations` section for the selected geo.

---

## ✅ Best Practices

- Use absolute URLs for all external links (e.g., CTAs, story links).
- Keep text content under reasonable length for email readability.
- Make sure all image paths are valid and correctly placed in the `images/<geo>/` folder.
- Validate your JSON using a linter or online tool before running the script.


### Running the Script

To generate newsletters for all translations under a specific geo, run the script with the base geo code. For example, to generate newsletters for the US and Switzerland (`ch`):

```bash
python scripts/generate_newsletter.py us
python scripts/generate_newsletter.py ch
```

Examples:
- `python scripts/generate_newsletter.py us` (generates all translations for US, e.g., `us-en`)
- `python scripts/generate_newsletter.py ca` (generates both `ca-en` and `ca-fr`)
- `python scripts/generate_newsletter.py cn` (generates all translations for China)
- `python scripts/generate_newsletter.py ne` (generates all translations for Niger)

#### How It Works
- The script takes only the base geo code as input (never hyphenated geo-lang).
- For each language listed in the `translations` block for that geo, a newsletter is generated (e.g., `ca-en`, `ca-fr`).
- All output files are saved in `generated_newsletters/<geo>/`.

#### Output Example
If you run:
```bash
python scripts/generate_newsletter.py ca
```
You will get:
- `generated_newsletters/ca/newsletter_ca-en_<timestamp>.html`
- `generated_newsletters/ca/newsletter_ca-fr_<timestamp>.html`

### 2a. Global Logo Banner
- The newsletter includes a banner at the top with your logo centered.
- Place your logo at `images/brand/HRF-Logo.png` (PNG recommended, max width 200px for best appearance).
- **Important**: The HRF logo is hardcoded in the template at `static/images/brand/HRF-Logo.png`:
  ```json
  "global": {
    "foundation_name": "Global Human Rights Foundation",
    "footer_text": "© 2025 Global Human Rights Foundation. All rights reserved.",
    "logo_url": "images/brand/HRF-Logo.png"
  }
  ```
- The banner will be the same width as the rest of the content.

### 3. Image Handling & Mailchimp Integration
- **Automatic Upload**: The script automatically uploads ALL images from `images/brand/` and `images/{geo}/` folders to Mailchimp Content Studio.
- **Image Compression**: Images larger than 1MB are automatically compressed using Pillow before upload.
- **URL Replacement**: All local image URLs in the generated HTML are replaced with Mailchimp-hosted URLs for email compatibility.
- **Folder Validation**: The script validates that both `images/brand/` and `images/{geo}/` folders exist before processing.
- **Supported Formats**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` files are automatically detected and uploaded.
- **Local Viewing**: For local HTML file viewing, image paths work correctly when opening files from the `generated_newsletters/` folder.

### 4. Error Handling
- If you provide a geo code that exists but is empty, you'll see:
  - `Error: Geo '<geo>' exists in the data, but contains no content or translations.`
- If you provide an invalid geo or geo-lang code, you'll see:
  - `Error: Geo '<geo>' could not be resolved.`

### 5. JSON Structure Example
```json
"ca": {
  "hero": { ... },
  "translations": {
    "en": { ... },
    "fr": { ... }
  }
}
```
- For Chinese (Simplified):
```json
"cn": {
  ...
  "translations": {
    "zh": { ... }
  }
}
```
- For Indonesia:
```json
"id": {
  ...
  "translations": {
    "id": { ... }
  }
}
```

### 6. Adding New Geos or Languages
- Note: Geo-specific configuration is no longer needed - all content is now provided via the web interface.
- Add a `translations` block with language codes as keys (e.g., `en`, `fr`, `zh`, `id`).
- Provide all required fields (see examples above).

### 7. Troubleshooting

#### Images Not Displaying Locally
- If images show as broken/404 when opening the HTML file in your browser:
  - Ensure you're opening the HTML from the correct location (`generated_newsletters/<geo>/`).
  - Verify that image files exist in the appropriate `images/brand/` or `images/{geo}/` folders.

#### Mailchimp Template Issues
- If images don't appear in uploaded Mailchimp templates:
  - Check that the logo file exists at `static/images/brand/HRF-Logo.png`.
  - Verify that image files exist in the expected folders before running the script.
  - Review the console output for successful image uploads and URL replacements.

#### Network/SSL Issues
- If you encounter SSL certificate errors during Mailchimp uploads, this may be due to corporate network SSL inspection. The script includes workarounds for common network security configurations.

---

## Reference

### Dependencies
The project requires the following Python packages (automatically installed via `requirements.txt`):
- **`Jinja2`** - Template rendering engine for generating HTML newsletters
- **`Pillow`** - Image processing and compression (for images >1MB)
- **`requests`** - HTTP requests to Mailchimp API
- **`python-dotenv`** - Environment variable management for API credentials

### Script Organization
After recent refactoring, the scripts are organized as follows:
- **`generate_newsletter.py`** - Main entry point for newsletter generation
- **`mailchimp_template_upload.py`** - Handles HTML template uploads to Mailchimp (renamed from `mailchimp_upload.py`)
- **`mailchimp_image_upload.py`** - Handles image uploads to Mailchimp Content Studio
- **`image_utils.py`** - Image compression and processing utilities
- **`utils/test_mailchimp_connection.py`** - Standalone connection testing utility (moved from root scripts folder)

### Removed Scripts
The following scripts were removed during reorganization as they were redundant or incomplete:
- `mailchimp_base64_upload.py` - Functionality merged into `mailchimp_image_upload.py`
- `send_newsletter.py` - Incomplete email sending simulation

---

## Country & Language Reference
For a comprehensive list of geo codes, language codes, script directions, and local country names, see:
- [COUNTRY_LANGUAGE_REFERENCE.md](COUNTRY_LANGUAGE_REFERENCE.md)

For questions or contributions, please contact the project maintainer.
