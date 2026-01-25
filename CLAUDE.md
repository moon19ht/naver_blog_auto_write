# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

네이버 블로그 자동 글쓰기 - Python-based automation tool for Naver blog posting with anti-detection features. Uses Selenium and Chrome DevTools Protocol (CDP) to bypass Naver's automation detection.

## Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env  # Then edit with Naver credentials

# Run (interactive mode)
python main.py

# Run (CLI mode)
python main.py --title "제목" --content "내용" --mode cdp

# Run via bash wrapper (handles display env for GUI)
./run.sh

# Korean fonts for Linux
./install_korean_fonts.sh
```

## Architecture

```
main.py (entry point)
├── src/config.py        → @dataclass configuration from .env
├── src/driver.py        → WebDriver factory (Chrome/Edge/Firefox, WSL support)
├── src/naver_login.py   → Login with clipboard bypass (pyperclip + pyautogui)
├── src/blog_writer.py   → Selenium-based posting (legacy)
└── src/blog_writer_cdp.py → CDP-based posting (recommended, 1400+ lines)
```

## Writing Modes

| Mode | File | Use Case |
|------|------|----------|
| CDP (recommended) | `blog_writer_cdp.py` | More stable, works headless, uses `Input.insertText` |
| Selenium | `blog_writer.py` | Simple cases, requires GUI for clipboard |

Mode selection: `WRITER_MODE=cdp` in `.env` or `--mode cdp` CLI flag

## Key Patterns

### CDP Command Execution
```python
def _execute_cdp(self, cmd: str, params: dict = None):
    return self.driver.execute_cdp_cmd(cmd, params)

# JavaScript evaluation
self._execute_cdp("Runtime.evaluate", {"expression": js_code, "returnByValue": True})

# Text input (bypasses automation detection)
self._execute_cdp("Input.insertText", {"text": text})
```

### Naver Editor iframe Handling
Naver blog uses nested iframes. Always switch context:
```python
iframe = self.wait.until(EC.presence_of_element_located((By.ID, "mainFrame")))
self.driver.switch_to.frame(iframe)
# ... work inside iframe ...
self.driver.switch_to.default_content()
```

### Clipboard-based Input (Login)
```python
pyperclip.copy(self.config.naver_id)
pyautogui.hotkey('ctrl', 'v')
```

## Configuration

Required `.env` variables:
- `NAVER_ID`, `NAVER_PW` - Credentials (required)
- `WRITER_MODE` - `cdp` (recommended) or `selenium`
- `HEADLESS` - `True` forces CDP mode (clipboard unavailable)
- `REMOTE_MODE` - `True` for SSH execution (auto-enables headless + CDP)

## Critical Constraints

1. **Headless mode**: Clipboard method doesn't work - forces CDP mode
2. **Alert handling**: Call `_handle_alert()` before/after major actions
3. **Retry logic**: `write_post()` supports `max_retries` parameter
4. **Post verification**: Use `_verify_post_published()` to confirm publication

## Debugging

HTML analysis scripts save page structure for reverse-engineering Naver UI:
- `analyze_blog.py`, `analyze_editor.py`, `analyze_iframe.py`
- Output files: `blog_page.html`, `editor_page.html`, `blog_iframe.html`
