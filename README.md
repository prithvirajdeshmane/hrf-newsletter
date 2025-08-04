# Global Human Rights Foundation Newsletter Generation Tool

A Python command-line tool for generating localized, multilingual email newsletters with robust geo/language fallback, image validation, and user-friendly CLI.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Features](#features)
- [Quick Start Guide](#quick-start-guide)
- [Detailed Usage](#detailed-usage)
- [Troubleshooting](#troubleshooting)
- [Reference](#reference)

---

## Project Structure
```
hrf-newsletter/
├── scripts/
│   ├── generate_newsletter.py          # Main script
│   ├── mailchimp_template_upload.py    # Template upload to Mailchimp
│   ├── mailchimp_image_upload.py       # Image upload to Mailchimp
│   ├── image_utils.py                  # Image compression utilities
│   └── utils/
│       └── test_mailchimp_connection.py # Connection testing utility
├── templates/
│   └── newsletter_template.html        # Jinja2 newsletter template
├── data/
│   └── newsletter_data.json           # Newsletter content configuration
├── images/
│   ├── global/                        # Global images (logos, etc.)
│   └── {geo}/                         # Geo-specific images
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

- **Automated Newsletter Generation**: Creates localized HTML newsletters from a central JSON data source.
- **Multi-Language Support**: Supports multiple translations for each geographical region (geo).
- **Dynamic Image Path Handling**: Automatically adjusts image paths for correct local viewing.
- **Mailchimp Integration**: 
  - **Template Upload**: Automatically uploads each generated newsletter as a new template in Mailchimp.
  - **Comprehensive Image Upload**: Automatically uploads ALL images from `images/global/` and `images/{geo}/` folders to Mailchimp Content Studio, regardless of whether they're referenced in the JSON data.
  - **Image Compression**: Automatically compresses images larger than 1MB using Pillow before upload.
  - **Smart URL Replacement**: Replaces all local image URLs in the HTML with Mailchimp-hosted URLs, handling multiple URL formats (`./images/...`, `/images/...`, `images/...`).
  - **Global Image Support**: Ensures global images (like logos) are included in every newsletter upload.
- **Error Handling**: Halts on any image or template upload failure with a descriptive error message.
- **Upload Summary**: Displays a summary of all successfully uploaded newsletters at the end of each run.

## Quick Start Guide

## Detailed Usage

### 1. Edit Content
- Update `data/newsletter_data.json` to add or modify geos and languages.
- Each geo (e.g., `us`, `ca`, `cn`, `id`) is a top-level key.
- **Each geo must have a `translations` block** for multilingual content (see below).
- Add your newsletter images to the `images/` directory:
  - **Global images** (shared across all geos): Place in `images/global/` (e.g., `images/global/HRF-Logo.png`)
  - **Geo-specific images**: Place in `images/{geo}/` (e.g., `images/us/hero.jpg`, `images/ch/story-1.jpg`)
- **Important**: The script uploads ALL images from both `images/global/` and `images/{geo}/` folders to Mailchimp, ensuring comprehensive image availability.

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
- Open the main configuration file (`data/newsletter_data.json`).
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
- Place your logo at `images/global/HRF-Logo.png` (PNG recommended, max width 200px for best appearance).
- **Important**: Ensure the `logo_url` field is defined in the `global` section of your `newsletter_data.json`:
  ```json
  "global": {
    "foundation_name": "Global Human Rights Foundation",
    "footer_text": "© 2025 Global Human Rights Foundation. All rights reserved.",
    "logo_url": "images/global/HRF-Logo.png"
  }
  ```
- The banner will be the same width as the rest of the content.

### 3. Image Handling & Mailchimp Integration
- **Automatic Upload**: The script automatically uploads ALL images from `images/global/` and `images/{geo}/` folders to Mailchimp Content Studio.
- **Image Compression**: Images larger than 1MB are automatically compressed using Pillow before upload.
- **URL Replacement**: All local image URLs in the generated HTML are replaced with Mailchimp-hosted URLs for email compatibility.
- **Folder Validation**: The script validates that both `images/global/` and `images/{geo}/` folders exist before processing.
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
- Add a new block in `newsletter_data.json` for the geo code.
- Add a `translations` block with language codes as keys (e.g., `en`, `fr`, `zh`, `id`).
- Provide all required fields (see examples above).

### 7. Troubleshooting

#### Images Not Displaying Locally
- If images show as broken/404 when opening the HTML file in your browser:
  - Ensure you're opening the HTML from the correct location (`generated_newsletters/<geo>/`).
  - Verify that image files exist in the appropriate `images/global/` or `images/{geo}/` folders.

#### Mailchimp Template Issues
- If images don't appear in uploaded Mailchimp templates:
  - Check that the `logo_url` field is defined in the `global` section of `newsletter_data.json`.
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
