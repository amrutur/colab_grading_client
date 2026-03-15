# colab_grading_client

**A Python client library for integrating Google Colab notebooks with AI-powered teaching and grading assistants.**

[![PyPI version](https://badge.fury.io/py/colab-grading-client.svg)](https://badge.fury.io/py/colab-grading-client)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`colab_grading_client` provides client-side functions for students to submit work and receive AI-powered assistance in Google Colab notebooks, and for instructors to manage grading workflows. It seamlessly integrates with grading servers via REST APIs.

- **Repository**: https://github.com/amrutur/colab_grading_client
- **Version**: 1.0.7
- **License**: MIT
- **Python**: >=3.7
- **Author**: Bharadwaj Amrutur (amrutur@gmail.com)

## Installation

Install from PyPI:

```bash
pip install colab_grading_client
```

Or in a Colab notebook:

```python
!pip install colab_grading_client
```

## Quick Start

### For Students

```python
from colab_grading_client import ask_assist, submit_eval, show_clear_output_button
import requests

# Create a session
session = requests.Session()

# Get help on a specific question
ask_assist(session, AI_TA_URL, qnum=1, notebook_id="assignment1",
           institution_id="university", term_id="fall2026",
           course_id="cs101", WAIT_TIME=2.0)

# Clear large outputs before submission (if you have 3D visualizations, etc.)
show_clear_output_button()

# Submit your notebook for grading
submit_eval(session, AI_TA_URL, notebook_id="assignment1",
            course_id="cs101", term_id="fall2026",
            institution_id="university", WAIT_TIME=2.0)
```

### For Instructors

```python
from colab_grading_client import fetch_student_list, fetch_graded_response, notify_student_grades

# Get list of students who submitted
fetch_student_list(GRADER_URL, notebook_id="assignment1")

# Retrieve a specific student's graded results
fetch_graded_response(GRADER_URL, notebook_id="assignment1",
                      user_email="student@university.edu")

# Send email notification to student
notify_student_grades(GRADER_URL, notebook_id="assignment1",
                      user_email="student@university.edu")
```

## Features

### 🎓 Student Features

- **Interactive Assistance**: Get AI-powered help on specific questions using `ask_assist()`
- **Easy Submission**: Submit notebooks for grading with `submit_eval()`
- **UI Buttons**: Display interactive buttons for common actions
- **Large Output Handling**: Clear large cell outputs (3D visualizations, plots) before submission

### 👨‍🏫 Instructor Features

- **Batch Grading**: Submit any notebook by URL for evaluation
- **Student Management**: Fetch lists of students and their grades
- **Email Notifications**: Automatically notify students about their grades
- **Flexible Rubrics**: Support for custom grading rubrics via URLs

### 🔧 Technical Features

- **Notebook Parsing**: Automatic extraction of questions, answers, and context from notebooks
- **Pattern Matching**: Flexible regex patterns for question/answer identification
- **Error Handling**: Robust timeout handling and graceful error messages
- **Google Drive Integration**: Seamless access to Colab notebooks via Drive API
- **MD5 Verification**: Notebook integrity checking

## Notebook Structure

### Marking Questions

Questions should be marked with the `**Q{number}**` pattern:

```markdown
**Q1** (10 points)
What is the time complexity of binary search?
```

### Marking Answers

Answers should be marked with `##Ans` or `## Ans`:

```markdown
## Ans
The time complexity is O(log n) because...
```

### User Information

Include your information in the first code cell:

```python
user_name = "John Doe"
user_email = "john.doe@university.edu"
```

## Core Functions

### Student Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `ask_assist()` | Get AI help on a question | `session`, `AI_TA_URL`, `qnum`, `notebook_id`, `institution_id`, `term_id`, `course_id`, `WAIT_TIME` |
| `submit_eval()` | Submit notebook for grading | `session`, `AI_TA_URL`, `notebook_id`, `course_id`, `term_id`, `institution_id`, `WAIT_TIME` |
| `show_teaching_assist_button()` | Display help button | `session`, `AI_TA_URL`, `qnum`, `notebook_id`, `institution_id`, `term_id`, `course_id`, `WAIT_TIME` |
| `show_submit_eval_button()` | Display submit button | `session`, `AI_TA_URL`, `notebook_id`, `course_id`, `term_id`, `institution_id`, `WAIT_TIME` |
| `show_clear_output_button()` | Display clear output button | None |

### Instructor Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `submit_nb_eval()` | Submit notebook by URL | `notebook_url`, `GRADER_URL`, `rubric_link`, `course_id`, `notebook_id` |
| `fetch_graded_response()` | Get graded results | `GRADER_URL`, `notebook_id`, `user_email` |
| `fetch_student_list()` | Get student list/grades | `GRADER_URL`, `notebook_id` |
| `notify_student_grades()` | Email student notification | `GRADER_URL`, `notebook_id`, `user_email` |

### Utility Functions

| Function | Description |
|----------|-------------|
| `get_notebook()` | Retrieve current notebook JSON |
| `parse_notebook()` | Extract questions, answers, and context |
| `clear_large_outputs()` | Clear outputs and show instructions |
| `get_file_id_from_share_link()` | Extract file ID from Drive URLs |
| `download_colab_notebook()` | Download notebook via Drive API |

## API Endpoints

The client communicates with a grading server via REST API:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/assist` | POST | Get teaching assistance |
| `/eval` | POST | Submit for evaluation |
| `/fetch_grader_response` | POST | Get graded results |
| `/fetch_student_list` | POST | Get student list/grades |
| `/notify_student_grades` | POST | Email student |

## Handling Large Outputs

If you have large cell outputs (3D visualizations from Open3D, large plots, etc.), they can prevent the grading client from reading your notebook. Use the clear output feature:

```python
from colab_grading_client import show_clear_output_button, clear_large_outputs

# Option 1: Use the button
show_clear_output_button()

# Option 2: Call directly
clear_large_outputs()
```

Or manually: `Runtime > Restart and clear outputs`

## Architecture

### Project Structure

```
colab_grading_client/
├── src/
│   ├── __init__.py              # Package initialization
│   └── colab_grading_client.py  # Main implementation
├── pyproject.toml               # Package configuration
├── README.md                    # This file
├── LICENSE                      # MIT License
└── .gitignore                   # Python gitignore
```

### Design Philosophy

- **Single-module library**: All functionality in one file for simplicity
- **Colab-specific**: Designed exclusively for Google Colab environment
- **REST API communication**: Direct communication with grading servers
- **Graceful error handling**: User-friendly messages, no exceptions raised
- **Timeout protection**: Configurable timeouts prevent indefinite hanging

## Dependencies

```python
# Google Colab specific
from google.colab import _message, auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Standard library
import requests, json, re, hashlib, io
from typing import Any, Dict
from urllib.parse import quote

# IPython/Jupyter
from IPython.display import Latex, Markdown, HTML, display, clear_output
from ipywidgets import Button, Layout
```

**Note**: This library requires a Google Colab environment and will not work in standard Python scripts.

## Error Handling

The library provides robust error handling:

- **Timeout handling**: Configurable `WAIT_TIME` (default 2.0 minutes)
- **Network errors**: Graceful degradation with user-friendly messages
- **Missing questions**: Validates question numbers exist before submission
- **Large notebooks**: Automatic retry with exponential backoff
- **User feedback**: Status messages displayed before long operations

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/amrutur/colab_grading_client.git
cd colab_grading_client

# Build the package
rm -rf dist/
python -m build

# Install locally
pip install dist/*.whl
```

### Publishing to PyPI

Get API tokens from [pypi.org](https://pypi.org) and store in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-...
```

Then publish:

```bash
python -m build
twine upload --repository pypi dist/*
```

### Version Management

- Version is defined in `pyproject.toml` under `[project]`
- Current version: `1.0.7`
- Follows semantic versioning: MAJOR.MINOR.PATCH

## Code Conventions

### Naming Patterns

- Functions: `snake_case`
- Question IDs: `"Q{number}"` or `"q{number}"` (case-insensitive)
- Pattern matching: Flexible regex for question/answer markers

### Cell Extraction Patterns

- Questions: `**Q{number}**` in markdown cells
- Answers: `##Ans` or `## Ans` (case-insensitive, flexible spacing)
- Context: Any cells between questions/answers
- Chat cells: `**Chat**` pattern

### Display Conventions

- `display(Markdown())` for formatted responses
- `display(HTML())` for HTML content
- `print()` for status/debugging messages
- `clear_output()` before displaying buttons

## Important Notes

### Colab-Specific Code

This library is tightly coupled to Google Colab:
- Uses `google.colab._message` (internal, undocumented API)
- Requires IPython/Jupyter environment
- Cannot be tested locally without Colab

### Large Output Warning

Large cell outputs (3D visualizations, interactive widgets, large plots) can cause `get_notebook()` to fail or timeout. Always clear large outputs before submission:

- Use `show_clear_output_button()` for an interactive button
- Use `clear_large_outputs()` to clear programmatically
- Or manually: `Runtime > Restart and clear outputs`

### Deprecated Functions

- `check_answer()` is deprecated; use `ask_assist()` instead

## Testing

**Current State**: No automated test suite

**Testing Challenges**:
- Colab-specific APIs require mocking `google.colab._message`
- Google Drive integration requires authentication
- UI components need IPython environment

**Recommended Testing**:
- Unit tests for utility functions (`calculate_json_md5`, `get_file_id_from_share_link`)
- Mock tests for API functions
- Integration tests with test server

## Future Improvements

1. **Type Hints**: Complete type annotations throughout
2. **Testing**: Comprehensive test suite with mocks
3. **Documentation**: Detailed API docs and example notebooks
4. **Configuration**: Config file support for server URLs
5. **Async**: Consider async/await for API calls
6. **Validation**: Enhanced input validation
7. **Logging**: Structured logging instead of print statements
8. **Modular Architecture**: Split into multiple modules as complexity grows

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Test in a Colab environment
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/amrutur/colab_grading_client/issues)
- **Email**: amrutur@gmail.com

## Changelog

### v1.0.7 (2026-03-15)
- Added `show_clear_output_button()` and `clear_large_outputs()` for handling large cell outputs
- Improved error handling for large notebooks with timeout and retry logic
- Added guards in `ask_assist()` to prevent KeyError for missing questions
- Enhanced answer pattern matching to be more flexible (case-insensitive, flexible spacing)
- Fixed function definition detection in `parse_notebook()`

### v1.0.6
- Updated `parse_notebook()` to handle various cell patterns
- Improved context and chat cell detection

### v0.1.4
- Initial stable release
- Core functionality for student and instructor workflows
- Google Drive integration
- REST API communication

---

**Made with ❤️ for educators and students using Google Colab**
