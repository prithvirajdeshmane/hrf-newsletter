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
- Each geo can have a `translations` block for multilingual content (see below).

### 2. Generate a Newsletter
Run:
```bash
python scripts/generate_newsletter.py <geo[-lang]>
```
Examples:
- `python scripts/generate_newsletter.py us` (defaults to English for US)
- `python scripts/generate_newsletter.py ca-fr` (Canadian French)
- `python scripts/generate_newsletter.py cn` (defaults to Chinese for China)
- `python scripts/generate_newsletter.py ne` (defaults to French for Niger)

#### Fallback Logic
- If you provide only the geo (e.g., `ca`), the script:
  - Uses English (`en`) if available in `translations`.
  - Otherwise, uses the first available language in the `translations` block.
- If you provide a full geo-lang code (e.g., `ca-fr`), it will use that specific translation.

#### Output
- Newsletters are saved in `generated_newsletters/<geo>/newsletter_<geo-lang>_<timestamp>.html`.

### 3. Image Validation
- All image paths referenced in the JSON (e.g., `image_url`) must exist in the `images/` directory.
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

### 7. Sending the Newsletter
(Coming soon)

---
For questions or contributions, please contact the project maintainer.
