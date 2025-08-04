# Global Human Rights Foundation Newsletter Generation Tool

A Python command-line tool for generating localized, multilingual email newsletters with robust geo/language fallback, image validation, and user-friendly CLI.

---

## Prerequisites
- Python 3.x
- Jinja2 (`pip install Jinja2`)

## Setup
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up Mailchimp API credentials:
   - Create a `.env` file in the project root
   - Add your Mailchimp API credentials:
     ```
     MAILCHIMP_API_KEY=your_api_key_here
     MAILCHIMP_SERVER_PREFIX=your_server_prefix_here
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

## Usage

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

### Running the Script

To generate newsletters for all translations under a specific geo, run the script with the base geo code. For example, to generate newsletters for the US and Switzerland (`ch`):

```bash
python scripts/generate_newsletter.py us
python scripts/generate_newsletter.py ch
```` (generates all translations for US, e.g., `us-en`)
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

## Country & Language Reference
For a comprehensive list of geo codes, language codes, script directions, and local country names, see:
- [COUNTRY_LANGUAGE_REFERENCE.md](COUNTRY_LANGUAGE_REFERENCE.md)

For questions or contributions, please contact the project maintainer.
