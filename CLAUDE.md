# CLAUDE.md - AI Assistant Guide for colab_grading_client

## Project Overview

**colab_grading_client** is a Python client library designed to integrate Google Colab notebooks with AI-powered teaching and grading assistants. It provides client-side functions for students to submit work and receive assistance, and for instructors to manage grading workflows.

- **Repository**: https://github.com/amrutur/colab_grading_client
- **Version**: 0.1.4
- **License**: MIT
- **Python**: >=3.7
- **Author**: Bharadwaj Amrutur (amrutur@gmail.com)

## Architecture

### Project Structure

```
colab_grading_client/
├── src/
│   ├── __init__.py           # Package initialization, exports all functions
│   └── colab_grading_client.py  # Main implementation (all functionality)
├── pyproject.toml            # Package configuration & metadata
├── README.md                 # Basic project description
├── LICENSE                   # MIT License
└── .gitignore                # Standard Python gitignore
```

### Design Philosophy

This is a **single-module library** with all functionality in one file (`colab_grading_client.py`). The design prioritizes:
- Simplicity and ease of use in Colab notebooks
- Direct REST API communication with grading servers
- Integration with Google Colab's internal APIs (`google.colab._message`)
- Google Drive integration for notebook access

## Core Components

### 1. Notebook Cell Extraction Functions

These functions interact with Google Colab's internal API to extract content from notebook cells:

- **`get_cell_idx(cells, qnum:int)`** - Finds cell index containing question marker `**Q{qnum}**`
- **`get_question_cell(qnum:int)`** - Extracts question cell content and type
- **`get_answer_cell(qnum:int)`** - Extracts answer cell (assumes next cell after question)
- **`get_cells_to_evaluate()`** - Prints all cells for debugging
- **`form_prompt(q_id:str)`** - Combines question and answer into LLM prompt

**Convention**: Questions are marked with `**Q{number}**` pattern in markdown cells.

### 2. Student-Facing Functions

Functions that students call from their notebooks:

- **`login()`** - Displays login interface (HTML response from server)
- **`ask_assist(GRADER_URL, q_id, rubric_link, WAIT_TIME)`** - Get help on a specific question (WAIT_TIME in minutes, default 2.0)
- **`check_answer(GRADER_URL, q_id, course_id, notebook_id, rubric_link)`** - DEPRECATED, use `ask_assist`
- **`submit_eval(GRADER_URL, user_name, user_email, course_id, notebook_id, rubric_link, WAIT_TIME)`** - Submit notebook for grading (WAIT_TIME in minutes, default 2.0)

### 3. Instructor/Admin Functions

Functions for managing grading workflows:

- **`submit_nb_eval(notebook_url, GRADER_URL, rubric_link, course_id, notebook_id)`** - Submit any notebook by URL for evaluation
- **`fetch_graded_response(GRADER_URL, notebook_id, user_email)`** - Retrieve graded results
- **`fetch_student_list(GRADER_URL, notebook_id)`** - Get list of students and grades
- **`notify_student_grades(GRADER_URL, notebook_id, user_email)`** - Send email notification to student

### 4. Google Drive Integration

- **`get_file_id_from_share_link(share_link:str)`** - Extracts file ID from Drive share URLs
- **`download_colab_notebook(notebook_url)`** - Downloads notebook as JSON using Google Drive API
- **`get_user_info(nb)`** - Extracts `user_name` and `user_email` from notebook cells

**Pattern**: User info is expected in first code cell as:
```python
user_name = "Student Name"
user_email = "student@example.com"
```

### 5. UI Components (ipywidgets)

Interactive buttons for Colab notebooks:

- **`show_login_button()`** - Displays login button
- **`show_teaching_assist_button(GRADER_URL, q_id, rubric_link, WAIT_TIME)`** - Button to get help (WAIT_TIME in minutes, default 2.0)
- **`show_submit_eval_button(GRADER_URL, user_name, user_email, course_id, notebook_id, rubric_link, WAIT_TIME)`** - Button to submit (WAIT_TIME in minutes, default 2.0)

### 6. Utility Functions

- **`calculate_json_md5(data:Dict)`** - Deterministic MD5 hash of JSON data
  - Uses sorted keys, no whitespace for consistency
  - Used to verify notebook integrity

## API Communication

### REST API Endpoints

The client communicates with a grading server at `GRADER_URL`:

| Endpoint | Method | Purpose | Payload Fields |
|----------|--------|---------|----------------|
| `/assist` | POST | Get teaching assistance | `query`, `q_id`, `user_name`, `user_email`, `rubric_link` |
| `/eval` | POST | Submit for evaluation | `course_id`, `user_name`, `user_email`, `notebook_id`, `answer_notebook`, `answer_hash`, `rubric_link` |
| `/fetch_grader_response` | POST | Get graded results | `notebook_id`, `user_email` |
| `/fetch_student_list` | POST | Get student list/grades | `notebook_id` |
| `/notify_student_grades` | POST | Email student | `notebook_id`, `user_email` |

### Response Handling

- Success: Status 200, JSON with `response` field (markdown formatted)
- Failure: Non-200 status, error message in response text
- Displays using IPython `display(Markdown())` for rich formatting

## Dependencies

### Required Packages

```python
# Google Colab specific
from google.colab import _message  # Internal API for notebook access
from google.colab import auth      # OAuth authentication
from googleapiclient.discovery import build  # Google Drive API
from googleapiclient.http import MediaIoBaseDownload

# Standard library
import requests  # HTTP client
import json
import re
import hashlib
import io
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
- **Pattern matching**: Case-insensitive for question IDs
- **Global variables**: Used for `user_name`, `user_email` (checked with `globals()`)

### 2. Error Handling

- Try-except blocks for all network requests
- Graceful degradation with user-friendly error messages
- Prints errors to console rather than raising exceptions
- Timeout handling: `ask_assist` and `submit_eval` include a configurable timeout (WAIT_TIME in minutes, default 2.0) that prevents indefinite hanging
- Timeout exceptions caught separately with user-friendly message: "The teaching assistant is taking too long. Please retry after some time."
- User feedback messages displayed before requests: "Please wait, asking the grader..." or "Please wait, submitting to the grader..."

### 3. Display Patterns

- Use `display(Markdown())` for formatted responses
- Use `display(HTML())` for HTML content
- Use `print()` for debugging and status messages
- `clear_output()` before displaying buttons

### 4. Cell Extraction Patterns

- Questions marked with `**Q{number}**` in markdown
- Answers assumed to be in the cell immediately following the question
- Regex pattern: `r"\*\*Q"+f"{qnum}"+"\*\*"`

### 5. Security Considerations

- MD5 hashing for notebook integrity verification
- OAuth for Google Drive access
- No client-side credential storage
- Server-side authentication required

## Development Workflow

### Version Management

- Version defined in `pyproject.toml` under `[project]`
- Current: `0.1.4`
- Semantic versioning: MAJOR.MINOR.PATCH

### Git Workflow

Recent commit pattern shows:
1. Feature additions (new functions)
2. Parameter updates
3. Bug fixes
4. Version bumps

**Commit messages**: Short, descriptive, lowercase

### Build System

- **Build backend**: setuptools (PEP 517 compliant)
- **Configuration**: `pyproject.toml` (modern Python packaging)
- **Package structure**: Simple src-layout

### Building and Publishing

```bash
# Build distribution
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Common AI Assistant Tasks

### Task 1: Adding New API Endpoints

When adding support for a new server endpoint:

1. Define function with clear parameters
2. Build payload dictionary with required fields
3. Add optional fields conditionally
4. Use try-except for requests
5. Handle 200 vs error responses
6. Display results using Markdown/HTML

**Template**:
```python
def new_function(GRADER_URL:str, required_param:str, optional_param:str = None):
    payload = {
        "required_param": required_param
    }
    if optional_param is not None:
        payload['optional_param'] = optional_param

    if GRADER_URL is None:
        print("Sorry Teaching Assistant is not available yet")
        return

    try:
        response = requests.post(GRADER_URL+"endpoint", json=payload)
        if response.status_code == 200:
            data = response.json()
            display(Markdown(data['response']))
        else:
            print(f"Call failed with status code: {response.status_code}")
            print("Error message:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
```

### Task 2: Modifying Cell Extraction Logic

The cell extraction logic relies on:
- `google.colab._message.blocking_request('get_ipynb')` for notebook access
- Regex patterns for identifying questions
- Index-based navigation (answer = question_index + 1)

When modifying:
- Update regex in `get_cell_idx()` if question format changes
- Adjust index offset in `get_answer_cell()` if answer position changes
- Test with various cell structures

### Task 3: Updating Button UI

Button creation follows this pattern:
```python
def show_button_name(params):
    clear_output()  # Clean previous output
    button = Button(
        description="Button Text",
        button_style='info',
        layout=Layout(width='auto')
    )
    button.on_click(lambda b: function_to_call(params))
    display(button)
```

### Task 4: Version Updates

When releasing a new version:
1. Update version in `pyproject.toml` line 7
2. Commit with message like "updated version number"
3. Build and publish to PyPI
4. Tag release in git

### Task 5: Adding Documentation

Currently minimal documentation. When adding:
- Update `README.md` with usage examples
- Add docstrings to new functions (currently sparse)
- Consider adding `docs/` directory for detailed guides
- Create example notebooks in `examples/`

## Testing Considerations

**Current State**: No test suite present

**Recommended additions**:
- Unit tests for utility functions (`calculate_json_md5`, `get_file_id_from_share_link`)
- Mock tests for API functions
- Integration tests with test server
- Test fixtures for notebook structures

**Testing challenges**:
- Colab-specific APIs require mocking `google.colab._message`
- Google Drive integration requires auth
- UI components need IPython environment

## Important Notes for AI Assistants

### 1. Colab-Specific Code

This library is tightly coupled to Google Colab:
- Uses `google.colab._message` (internal, undocumented API)
- Requires IPython/Jupyter environment
- Cannot be used in standard Python scripts
- No local testing without Colab environment

### 2. Deprecated Functions

- `check_answer()` at line 176 is marked for deprecation
- Use `ask_assist()` instead
- When refactoring, ensure backward compatibility or add warnings

### 3. Global Variable Pattern

Functions check for global variables:
```python
if 'user_name' in globals():
    payload['user_name'] = user_name
```

This is intentional for Colab notebook context but should be documented as a code smell for standard Python.

### 4. Error Handling Philosophy

- Never raise exceptions to the user
- Always provide helpful error messages
- Graceful degradation when server unavailable
- Print, don't crash

### 5. Payload Construction

All API calls follow pattern:
1. Build dictionary with required fields
2. Conditionally add optional fields
3. Check if GRADER_URL exists
4. POST with `json=payload` (not `data=`)
5. Parse JSON response on success

### 6. Display Conventions

- Markdown for formatted text (grading feedback, responses)
- HTML for interactive content (login pages)
- Print for status/debugging
- Clear output before showing new buttons

## Future Considerations

### Potential Improvements

1. **Type Hints**: Add complete type annotations
2. **Testing**: Comprehensive test suite
3. **Documentation**: Detailed API docs and examples
4. **Configuration**: Config file support instead of passing GRADER_URL
5. **Async**: Consider async/await for API calls
6. **Validation**: Input validation for parameters
7. **Logging**: Structured logging instead of print statements
8. **Error Classes**: Custom exceptions for different error types

### Architecture Evolution

- Consider splitting into multiple modules as complexity grows
- Separate concerns: API client, UI, notebook utilities
- Add abstract base classes for extensibility
- Plugin system for custom grading rubrics

## Quick Reference

### File Locations
- Main code: `src/colab_grading_client.py`
- Package config: `pyproject.toml`
- Exports: `src/__init__.py`

### Key Line Numbers
- Cell extraction: Lines 71-104
- Prompt formation: Lines 106-124
- Student functions: Lines 126-206
- Submission: Lines 208-242
- Buttons: Lines 245-275
- Drive integration: Lines 277-342
- User info extraction: Lines 344-368
- Admin functions: Lines 370-511

### Common Patterns
- API calls: Try-except with status checking
- Notebook access: `_message.blocking_request('get_ipynb')`
- Question format: `**Q{number}**`
- User info: First code cell with `user_name` and `user_email`

## Current Development Branch

Working on: `claude/claude-md-mifravz5v1c7q2ad-01SRCKHkm4smD8fpuo4WWxon`

When making changes:
- Develop on the feature branch
- Commit with descriptive messages
- Push to origin with branch name
- Never force push without permission

---

**Last Updated**: 2025-11-26
**Based on Version**: 0.1.4
**For AI Assistants**: Follow these guidelines when analyzing or modifying this codebase
