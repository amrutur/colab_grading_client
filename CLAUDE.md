# CLAUDE.md - AI Assistant Guide for colab_grading_client

## Project Overview

**colab_grading_client** is a Python client library designed to integrate Google Colab notebooks with AI-powered teaching and grading assistants. It provides client-side functions for students to submit work and receive assistance, and for instructors to manage grading workflows.

- **Repository**: https://github.com/amrutur/colab_grading_client
- **Version**: 1.0.7
- **License**: MIT
- **Python**: >=3.7
- **Author**: Bharadwaj Amrutur (amrutur@gmail.com)

## Architecture

### Project Structure

```
colab_grading_client/
├── src/
│   ├── __init__.py              # Package initialization, exports all functions
│   └── colab_grading_client.py  # Main implementation (all functionality)
├── pyproject.toml               # Package configuration & metadata
├── README.md                    # User-facing documentation
├── CLAUDE.md                    # AI Assistant guide (this file)
├── LICENSE                      # MIT License
└── .gitignore                   # Standard Python gitignore
```

### Design Philosophy

This is a **single-module library** with all functionality in one file (`colab_grading_client.py`). The design prioritizes:
- Simplicity and ease of use in Colab notebooks
- Direct REST API communication with grading servers
- Integration with Google Colab's internal APIs (`google.colab._message`)
- Streaming responses for real-time feedback
- Session-based authentication

## Core Components

### 1. Authentication & Session Management

**`generate_random_string(l:int) -> str`**
- Generates random alphanumeric string of length `l`
- Used for creating session identifiers

**`authenticate(AI_TA_URL:str) -> requests.Session`**
- Creates authenticated session with the AI TA server
- Returns a `requests.Session` object for subsequent API calls
- IMPORTANT: All API calls (ask_assist, submit_eval) require a session object

### 2. Notebook Parsing Functions

**`get_cell_output(cell)`**
- Extracts output from a notebook cell
- Handles multiple output types (text, images, errors)
- Returns formatted string representation

**`get_notebook(max_retries:int=5, retry_delay:float=0.5)`**
- Retrieves current notebook JSON from Colab frontend
- Uses `_message.blocking_request('get_ipynb', timeout_sec=10)`
- Implements exponential backoff retry logic
- Handles timeouts for large notebooks (3D visualizations, etc.)
- Returns notebook dict or None on failure

**`split_the_answer(inp) -> list`**
- Splits answer into components with percentage weights
- Pattern: `##N%` followed by answer component text
- Returns list of `{'percent': int, 'component': str}` dicts
- Validates that percentages sum to 100
- Returns None on validation errors

**`parse_notebook(nb) -> tuple`**
- Main parsing function that extracts structured data from notebook
- Returns: `(contexts, questions, answers, outputs, ta_chat, max_marks)`
- All return values are dictionaries keyed by question number (as string)

**Patterns used:**
- **Question**: `**Q{number}** :{marks}` (marks optional, defaults to 10)
- **Answer**: `##Ans` or `## Ans` (case-insensitive, flexible spacing)
- **Chat**: `**Chat**` followed by text
- **TA Button**: `show_teaching_assist_button(` (excluding function definitions)

**States:**
- CONTEXT: Accumulating context cells
- QUESTION: Inside question cells
- ANSWER: Inside answer cells
- TABUTTON: Expecting TA button cell

### 3. Student-Facing Functions

**`ask_assist(session, AI_TA_URL, qnum, notebook_id, institution_id, term_id, course_id, WAIT_TIME=2.0)`**
- Get AI help on a specific question
- Validates question exists before making API call
- Uses streaming response (`stream=True`) for real-time feedback
- Handles heartbeat, progress, response, and error message types
- WAIT_TIME in minutes (default 2.0)
- Payload includes: context, question, answer, output, ta_chat

**`submit_eval(session, AI_TA_URL, notebook_id, institution_id, term_id, course_id, WAIT_TIME=2.0)`**
- Submit entire notebook for grading
- Uses streaming response for progress updates
- WAIT_TIME in minutes (default 2.0)
- Payload includes: contexts, questions, answers, outputs for all questions

**`upload_rubric(session, AI_TA_URL, notebook_id, institution_id, term_id, course_id)`**
- Upload grading rubric to the server
- Parses notebook and extracts questions/answers
- Used by instructors to set grading criteria

### 4. UI Components (ipywidgets)

**`show_teaching_assist_button(session, AI_TA_URL, qnum, notebook_id, institution_id, term_id, course_id, WAIT_TIME=2.0)`**
- Displays "Check/Help with question Q{qnum}!" button
- Button style: 'info' (blue)
- Calls `ask_assist()` on click

**`show_submit_eval_button(session, AI_TA_URL, notebook_id, institution_id, term_id, course_id, WAIT_TIME=2.0)`**
- Displays "Submit my notebook!" button
- Button style: 'info' (blue)
- Calls `submit_eval()` on click

**`show_clear_output_button()`**
- Displays "Clear Output" button
- Button style: 'warning' (yellow)
- Calls `clear_large_outputs()` on click
- Useful before submission when notebook has large outputs

**`clear_large_outputs()`**
- Clears current cell output
- Displays markdown instructions for clearing other outputs
- Warns about large outputs (3D visualizations, plots) that can cause submission failures

## API Communication

### REST API Endpoints

The client communicates with a grading server at `AI_TA_URL`:

| Endpoint | Method | Purpose | Streaming |
|----------|--------|---------|-----------|
| `/authenticate` | POST | Create session | No |
| `/assist` | POST | Get teaching assistance | Yes |
| `/eval` | POST | Submit for evaluation | Yes |
| `/upload_rubric` | POST | Upload grading rubric | No |

### Streaming Response Format

For `/assist` and `/eval` endpoints, responses are streamed as JSON lines:

```json
{"type": "heartbeat"}
{"type": "progress", "message": "Processing question 1..."}
{"type": "response", "response": "## Feedback\n..."}
{"type": "error", "detail": "Error message"}
```

### Response Handling Pattern

```python
resp = session.post(url, json=payload, timeout=WAIT_TIME*60, stream=True)
if resp.status_code != 200:
    print(f"Error: {resp.status_code} - {resp.text}")
    return

for line in resp.iter_lines():
    if not line:
        continue
    msg = json.loads(line)
    if msg["type"] == "heartbeat":
        continue  # keep alive
    elif msg["type"] == "progress":
        print(msg["message"])
    elif msg["type"] == "response":
        display(Markdown(msg["response"]))
    elif msg["type"] == "error":
        print(f"Error: {msg['detail']}")
```

## Dependencies

### Required Packages

```python
# Google Colab specific
from google.colab import _message, auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import google.auth
from google.auth.transport.requests import Request

# Standard library
import requests
import json
import re
import hashlib
import io
import time
import string
import random
from typing import Any, Dict
from urllib.parse import quote

# IPython/Jupyter
from IPython.display import Latex, Markdown, HTML, display, clear_output
from ipywidgets import Button, Layout
```

**Note**: This library is designed exclusively for Google Colab environments.

## Code Conventions

### 1. Naming Patterns

- **Functions**: `snake_case` (Python standard)
- **Question IDs**: Format `"Q{number}"` or `"q{number}"`
- **Pattern matching**: Case-insensitive for question IDs and answer markers
- **Session management**: All API calls require a `requests.Session` object

### 2. Error Handling

- Try-except blocks for all network requests
- Graceful degradation with user-friendly error messages
- Prints errors to console rather than raising exceptions
- Timeout handling: configurable WAIT_TIME (in minutes, default 2.0)
- Timeout exceptions caught separately with message: "The AI TAssistant is taking too long. Please retry after some time."
- User feedback messages: "Please wait, asking the AI TA..." or "Please wait, submitting to AI TA..."

### 3. Display Patterns

- Use `display(Markdown())` for formatted responses
- Use `display(HTML())` for HTML content (if needed)
- Use `print()` for status messages and debugging
- Buttons do NOT call `clear_output()` before display (commented out)

### 4. Cell Extraction Patterns

- Questions marked with `**Q{number}**` or `**Q{number}** :{marks}` in markdown
- Answers marked with `##Ans` or `## Ans` (case-insensitive, flexible spacing)
- Answer components marked with `##N%` where N is the percentage weight
- Regex pattern for questions: `r"\s*\*\*\s*[qQ]\s*(\d+)\s*:?\s*\(?(\d+\.\d|\d+)?.*?\n(.*)"`
- Regex pattern for answers: `r"\#\#\s*[aA]ns"`
- Regex pattern for chat: `r"\*\*\s*[cC]hat.*?(\n.*)"`
- Regex pattern for TA button: `r"show_teaching_assist_button\("` (must not be in function definition)

### 5. Security Considerations

- Session-based authentication with server
- OAuth for Google Drive access (if needed)
- No client-side credential storage
- Server-side authentication required for all operations

## Development Workflow

### Version Management

- Version defined in `pyproject.toml` under `[project]`
- Current: `1.0.7`
- Semantic versioning: MAJOR.MINOR.PATCH

### Git Workflow

Commit pattern:
1. Feature additions (new functions)
2. Bug fixes
3. Version bumps
4. Documentation updates

**Commit messages**: Short, descriptive, clear

### Build System

- **Build backend**: setuptools (PEP 517 compliant)
- **Configuration**: `pyproject.toml` (modern Python packaging)
- **Package structure**: Simple src-layout

### Building and Publishing

```bash
# Build distribution
rm -rf dist/
python -m build

# Upload to PyPI
twine upload --repository pypi dist/*
```

## Common AI Assistant Tasks

### Task 1: Adding New API Endpoints

When adding support for a new server endpoint:

1. Check if endpoint uses streaming or regular response
2. Define function with clear parameters including `session` and `AI_TA_URL`
3. Build payload dictionary with required fields
4. Add optional fields conditionally
5. Use try-except for requests
6. Handle streaming vs regular responses appropriately
7. Display results using Markdown/print

**Template for Streaming Endpoint**:
```python
def new_function(session:requests.Session, AI_TA_URL:str, required_param:str, WAIT_TIME:float = 2.0):
    nb = get_notebook()
    if nb is None:
        return

    # Parse and validate as needed

    payload = {
        "required_param": required_param
    }

    if AI_TA_URL is None:
        print("AI Teaching Assistant url (AI_TA_URL) is not set")
        return

    try:
        print("Please wait, processing...")
        resp = session.post(AI_TA_URL+"endpoint", json=payload, timeout=WAIT_TIME*60, stream=True)

        if resp.status_code != 200:
            print(f"Error: {resp.status_code} - {resp.text}")
            return

        for line in resp.iter_lines():
            if not line:
                continue
            msg = json.loads(line)
            if msg["type"] == "heartbeat":
                continue
            elif msg["type"] == "progress":
                print(msg["message"])
            elif msg["type"] == "response":
                display(Markdown(msg["response"]))
            elif msg["type"] == "error":
                print(f"Error: {msg['detail']}")

    except requests.exceptions.Timeout:
        print(f"Request is taking too long. Please retry after some time.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
```

### Task 2: Modifying Notebook Parsing Logic

The cell extraction logic relies on:
- `google.colab._message.blocking_request('get_ipynb', timeout_sec=10)` for notebook access
- Regex patterns for identifying questions, answers, chat cells
- State machine (CONTEXT, QUESTION, ANSWER, TABUTTON) for parsing flow
- `split_the_answer()` for parsing answer components with weights

When modifying:
- Update regex patterns in `parse_notebook()` if cell format changes
- Test with various cell structures
- Ensure state transitions are correct
- Validate that percentages sum to 100 in answer components

### Task 3: Updating Button UI

Button creation follows this pattern:
```python
def show_button_name(session:requests.Session, AI_TA_URL:str, params...):
    # Note: clear_output() is commented out to avoid clearing other outputs
    button = Button(
        description="Button Text",
        button_style='info',  # or 'warning' for clear button
        layout=Layout(width='auto')
    )
    button.on_click(lambda b: function_to_call(session, AI_TA_URL, params...))
    display(button)
```

### Task 4: Version Updates

When releasing a new version:
1. Update version in `pyproject.toml` line 7
2. Update version in README.md and CLAUDE.md
3. Add entry to CHANGELOG section in README.md
4. Commit with message like "bump version to X.Y.Z"
5. Build and publish to PyPI
6. Tag release in git

### Task 5: Handling Large Notebooks

Large cell outputs can cause `get_notebook()` to fail. The solution:
1. `get_notebook()` has 10-second timeout on `blocking_request`
2. Exponential backoff retry (5 attempts)
3. Helpful error messages about clearing outputs
4. `clear_large_outputs()` and `show_clear_output_button()` for users

Common causes:
- Open3D 3D visualizations
- Large matplotlib plots
- Interactive widgets
- Large data displays

## Important Notes for AI Assistants

### 1. Colab-Specific Code

This library is tightly coupled to Google Colab:
- Uses `google.colab._message` (internal, undocumented API)
- Requires IPython/Jupyter environment
- Cannot be used in standard Python scripts
- No local testing without Colab environment

### 2. Session Management is Critical

**BREAKING CHANGE**: All API functions now require a `session` parameter
- Old: `ask_assist(GRADER_URL, q_id, ...)`
- New: `ask_assist(session, AI_TA_URL, qnum, ...)`
- Sessions created via `authenticate(AI_TA_URL)`
- Sessions maintain state across API calls

### 3. Streaming Responses

API endpoints use streaming responses for real-time feedback:
- Set `stream=True` in requests
- Use `resp.iter_lines()` to process line by line
- Handle JSON message types: heartbeat, progress, response, error
- Display progress messages as they arrive

### 4. Error Handling Philosophy

- Never raise exceptions to the user
- Always provide helpful error messages
- Graceful degradation when server unavailable
- Print, don't crash

### 5. Question Number Validation

`ask_assist()` validates question existence before API call:
```python
qnum_str = str(qnum)
if qnum_str not in questions:
    print(f"Error: Question {qnum} not found in the notebook.")
    print("Make sure your question is marked with **Q{qnum}** pattern.")
    return
```

Use `.get()` for safe dictionary access:
```python
payload = {
    "context": context.get(qnum_str, ""),
    "question": questions.get(qnum_str, ""),
    ...
}
```

### 6. Answer Components

Answers can have weighted components:
```markdown
## Ans
##50%
This is the first part worth 50%
##50%
This is the second part worth 50%
```

`split_the_answer()` validates and parses these, returning structured data.

## Testing Considerations

**Current State**: No test suite present

**Recommended additions**:
- Unit tests for utility functions (`split_the_answer`, `generate_random_string`)
- Mock tests for API functions (mock `requests.Session`)
- Integration tests with test server
- Test fixtures for various notebook structures

**Testing challenges**:
- Colab-specific APIs require mocking `google.colab._message`
- Streaming responses need mock line iterators
- UI components need IPython environment

## Quick Reference

### File Locations
- Main code: `src/colab_grading_client.py`
- Package config: `pyproject.toml`
- Exports: `src/__init__.py`
- User docs: `README.md`
- AI guide: `CLAUDE.md` (this file)

### Current Functions (v1.0.7)

**Authentication:**
- `generate_random_string(l)`
- `authenticate(AI_TA_URL)`

**Notebook Parsing:**
- `get_cell_output(cell)`
- `get_notebook(max_retries, retry_delay)`
- `split_the_answer(inp)`
- `parse_notebook(nb)`

**Student Functions:**
- `ask_assist(session, AI_TA_URL, qnum, notebook_id, institution_id, term_id, course_id, WAIT_TIME)`
- `submit_eval(session, AI_TA_URL, notebook_id, institution_id, term_id, course_id, WAIT_TIME)`

**Instructor Functions:**
- `upload_rubric(session, AI_TA_URL, notebook_id, institution_id, term_id, course_id)`

**UI Components:**
- `show_teaching_assist_button(session, AI_TA_URL, qnum, notebook_id, institution_id, term_id, course_id, WAIT_TIME)`
- `show_submit_eval_button(session, AI_TA_URL, notebook_id, institution_id, term_id, course_id, WAIT_TIME)`
- `clear_large_outputs()`
- `show_clear_output_button()`

### Common Patterns
- API calls: Try-except with status checking, streaming support
- Notebook access: `_message.blocking_request('get_ipynb', timeout_sec=10)`
- Question format: `**Q{number}**` or `**Q{number}** :{marks}`
- Answer format: `##Ans` (flexible spacing, case-insensitive)
- Answer components: `##N%` where N is percentage
- Session requirement: All API calls need authenticated session

### Parameter Changes (Important!)

**Old API (deprecated):**
- `ask_assist(GRADER_URL, q_id, rubric_link, WAIT_TIME)`

**New API (current):**
- `ask_assist(session, AI_TA_URL, qnum, notebook_id, institution_id, term_id, course_id, WAIT_TIME)`

Key changes:
- Added `session` as first parameter
- Changed `GRADER_URL` to `AI_TA_URL`
- Changed `q_id` to `qnum` (integer, not string)
- Removed `rubric_link` parameter
- Added `notebook_id`, `institution_id`, `term_id`, `course_id` parameters

## Current Development Branch

Working on: `claude/claude-md-mifravz5v1c7q2ad-01SRCKHkm4smD8fpuo4WWxon`

When making changes:
- Develop on the feature branch
- Commit with descriptive messages
- Push to origin with branch name
- Never force push without permission

---

**Last Updated**: 2026-03-15
**Based on Version**: 1.0.7
**For AI Assistants**: Follow these guidelines when analyzing or modifying this codebase
