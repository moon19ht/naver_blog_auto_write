# nblog - Naver Blog Automation CLI

A CLI-first automation tool for batch posting to Naver Blog. Supports JSON-driven workflows for posting multiple blog entries across multiple accounts.

## Features

- **JSON-Driven Batch Posting** - Post multiple blog entries from a single JSON file
- **Multi-Account Support** - Handle multiple Naver accounts in one batch
- **Secure Credential Management** - Environment variables, secrets files, never logs passwords
- **Validation & Reporting** - Validate input files and generate JSON reports
- **Headless Operation** - Run on servers without GUI (Arch Linux CLI supported)
- **Chrome DevTools Protocol** - Robust browser automation with CDP

## Quick Start

```bash
# Clone and setup
git clone https://github.com/moon19ht/naver_blog_auto_write.git
cd naver_blog_auto_write
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Validate your input file
./nblog validate input.json

# Dry run (see what would be posted)
./nblog post input.json --all --dry-run

# Post all entries
./nblog post input.json --all
```

## Installation

### Requirements

- Python 3.8+
- Chrome/Chromium browser
- Linux (tested on Arch Linux)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Korean Fonts (Linux)

```bash
./install_korean_fonts.sh
```

## JSON Input Format

The input JSON file must be a UTF-8 encoded array of blog post entries:

```json
[
  {
    "sns_id": "your_email@naver.com",
    "sns_pw": "your_password",
    "sns_upload_cont": {
      "blog_title": "Your Blog Post Title",
      "blog_title_img": "https://example.com/header.jpg",
      "blog_top_word": "Introduction paragraph",
      "blog_top_word2": "Second intro paragraph",
      "blog_title_img2": "https://example.com/image2.jpg",
      "blog_basic": "Main content of your blog post",
      "blog_feature": "Feature highlights",
      "blog_title_img3": "https://example.com/image3.jpg",
      "site_title1": "Section 1 Title",
      "site_cont1": "Section 1 content",
      "site_img1": "https://example.com/section1.jpg",
      "site_quote": "An inspiring quote",
      "site_title2": "Section 2 Title",
      "site_cont2": "Section 2 content",
      "site_img2": "https://example.com/section2.jpg",
      "site_addr": "Address line 1",
      "site_addr2": "Address line 2",
      "site_cll_img": "https://example.com/call.jpg",
      "site_time": "Mon-Fri 9:00-18:00",
      "site_bus": "Business information",
      "site_tag": "tag1,tag2,tag3"
    }
  }
]
```

### Required Fields

| Field | Description |
|-------|-------------|
| `sns_id` | Naver account email |
| `sns_upload_cont.blog_title` | Blog post title |

### Optional Fields

| Field | Description |
|-------|-------------|
| `sns_pw` | Password (can use env override instead) |
| `blog_title_img`, `blog_title_img2`, `blog_title_img3` | Header images (must be http/https URLs) |
| `blog_top_word`, `blog_top_word2` | Introduction paragraphs |
| `blog_basic`, `blog_feature` | Main content sections |
| `site_title1`, `site_cont1`, `site_img1` | First content section |
| `site_title2`, `site_cont2`, `site_img2` | Second content section |
| `site_quote` | Blockquote text |
| `site_addr`, `site_addr2` | Address information |
| `site_cll_img` | Contact image |
| `site_time` | Business hours |
| `site_bus` | Business info |
| `site_tag` | Comma-separated tags |

## CLI Commands

### Validate Input

Validate a JSON file without posting:

```bash
./nblog validate input.json
./nblog validate input.json --quiet  # Errors only
```

### Post Blog Entries

```bash
# Post all entries
./nblog post input.json --all

# Post specific entry by index
./nblog post input.json --account-index 0

# Post entries for specific email
./nblog post input.json --filter-email user@naver.com

# Dry run (preview without posting)
./nblog post input.json --all --dry-run

# Save report to file
./nblog post input.json --all --out report.json

# Use external secrets file
./nblog post input.json --all --secrets-file secrets.json

# Run with visible browser
./nblog post input.json --all --no-headless

# Custom retry count
./nblog post input.json --all --retries 5
```

### System Health Check

```bash
./nblog doctor
./nblog doctor input.json  # Also check credentials
```

## Credential Security

**IMPORTANT: Never commit credentials to version control!**

### Option 1: Environment Variables (Recommended)

Set password via environment variable:

```bash
# Format: NBLOG_PW_<EMAIL_SANITIZED>
export NBLOG_PW_USER_AT_NAVER_COM=your_password
./nblog post input.json --all
```

Email sanitization rules:
- `@` → `_at_`
- `.` → `_`
- Uppercase

Example: `user@naver.com` → `NBLOG_PW_USER_AT_NAVER_COM`

### Option 2: External Secrets File

Create a separate secrets JSON file:

```json
{
  "user1@naver.com": "password1",
  "user2@naver.com": "password2"
}
```

Use with `--secrets-file`:

```bash
./nblog post input.json --all --secrets-file /secure/path/secrets.json
```

**Keep this file outside the repository!**

### Option 3: In JSON (Least Secure)

Include password directly in input JSON. Only use for testing.

### Credential Resolution Priority

1. Environment variable (`NBLOG_PW_*`)
2. Secrets file
3. JSON input

## Architecture

```
naver_blog_auto_write/
├── nblog                    # CLI entry point
├── cli/
│   └── main.py              # CLI commands and argument parsing
├── core/
│   ├── models/
│   │   └── blog_post.py     # Data models (BlogPostEntry, etc.)
│   ├── validation/
│   │   └── json_validator.py # JSON schema validation
│   └── rendering/
│       └── content_renderer.py # Content to HTML/text
├── automation/
│   └── naver_blog/
│       └── orchestrator.py  # Batch posting orchestration
├── adapters/
│   ├── browser/
│   │   └── driver_adapter.py # Selenium/CDP browser management
│   ├── secrets/
│   │   └── credential_manager.py # Secure credential handling
│   └── report/
│       └── reporter.py      # Report generation
├── src/                     # Legacy modules (login, blog writers)
│   ├── naver_login.py       # Naver login automation
│   ├── blog_writer.py       # Selenium blog writer
│   └── blog_writer_cdp.py   # CDP blog writer (recommended)
├── tests/
│   ├── unit/
│   └── integration/
└── examples/
    └── sample_input.json    # Sample input file
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `cli/main.py` | CLI entry point with argparse |
| `core/models` | Data models matching JSON schema |
| `core/validation` | JSON validation with detailed errors |
| `adapters/secrets` | Multi-source credential resolution |
| `adapters/report` | JSON and console reporting |
| `automation/orchestrator` | Batch posting workflow |

## Validation & Reporting

### Validation Rules

- **Required fields**: `sns_id`, `sns_upload_cont`, `blog_title`
- **URL validation**: Image fields must be `http://` or `https://`
- **Tag normalization**: Trailing commas removed, empty tags filtered

### Validation Output

```
Validation Report: input.json
============================================================
  Status: VALID
  Entries: 3

Warnings:
  [0].sns_upload_cont.site_tag: Tags have trailing comma (will be normalized)
============================================================
```

### Batch Report

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "duration_seconds": 45.2,
  "summary": {
    "total": 3,
    "successful": 2,
    "failed": 1,
    "skipped": 0
  },
  "results": [
    {
      "index": 0,
      "sns_id": "user@naver.com",
      "blog_title": "My Post",
      "success": true,
      "error_message": "",
      "timestamp": "2024-01-15T10:30:15"
    }
  ]
}
```

## Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_validation.py -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=core --cov=cli --cov-report=html
```

## Headless/Remote Operation

For running on servers without GUI:

```bash
# Headless mode (default)
./nblog post input.json --all

# Or explicitly
./nblog post input.json --all --headless
```

### SSH Remote Mode

The tool is optimized for headless operation on remote servers:

```bash
# Connect via SSH
ssh user@server

# Run in background with nohup
nohup ./nblog post input.json --all --out report.json &

# Check status
tail -f nohup.out
```

## Troubleshooting

### Browser Issues

```bash
# Check browser availability
./nblog doctor

# If Chrome not found
# Arch Linux:
sudo pacman -S chromium

# Ubuntu:
sudo apt install chromium-browser
```

### Login Failures

- Naver may require CAPTCHA for new logins
- Try running with `--no-headless` first to complete manual verification
- Consider using 2FA app codes

### Korean Font Issues

```bash
./install_korean_fonts.sh
```

## Legacy Single-Post Mode

The original `main.py` is still available for single posts:

```bash
# Interactive mode
python main.py

# Command line mode
python main.py --title "Title" --content "Content" --mode cdp
```

## Security Best Practices

1. **Never commit `.env` or secrets files**
2. **Use environment variables in CI/CD**
3. **Store secrets files outside the repo**
4. **Use read-only filesystem permissions for secrets**
5. **Rotate passwords periodically**

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Submit a pull request

Issues and feature requests: https://github.com/moon19ht/naver_blog_auto_write/issues
