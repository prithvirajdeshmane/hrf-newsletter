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

## Usage

### 1. Edit Content
- Update `data/newsletter_data.json` to add or modify geos and languages.
- Each geo (e.g., `us`, `ca`, `cn`, `id`) is a top-level key.
- **Each geo must have a `translations` block** for multilingual content (see below).
- Add your newsletter images to the `images/` directory. For the global logo banner, place your logo at `images/global/HRF-Logo.png`.

### 2. Generate Newsletters for a Geo
Run:
```bash
python scripts/generate_newsletter.py <geo>
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
- The banner will be the same width as the rest of the content.

### 3. Image Validation & Path Conventions
- All image paths referenced in the JSON (e.g., `image_url`) must exist in the `images/` directory.
- For local viewing, the template automatically prefixes image paths with `../../` so images display correctly when you open the generated HTML files directly in your browser.
- If any image is missing, the script will print a clear error and abort generation.

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

### 7. Troubleshooting: Images Not Displaying
- If images show as broken/404 when opening the HTML file in your browser, ensure:
  - The referenced image paths in your JSON are correct and the files exist.
  - You are opening the HTML from the correct location (e.g., `generated_newsletters/<geo>/`).
  - The template prefixes image URLs with `../../` to resolve from the newsletter output folder to the project root.

---

## Country & Language Reference
For a comprehensive list of geo codes, language codes, script directions, and local country names, see:
- [COUNTRY_LANGUAGE_REFERENCE.md](COUNTRY_LANGUAGE_REFERENCE.md)

For questions or contributions, please contact the project maintainer.
