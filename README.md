# colab_grading_client

**A Python client library for integrating Google Colab notebooks with AI-powered teaching and grading assistants.**

[![PyPI version](https://badge.fury.io/py/colab-grading-client.svg)](https://badge.fury.io/py/colab-grading-client)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`colab_grading_client` provides client-side functions for students to submit work and receive AI-powered assistance in Google Colab notebooks, and for instructors to manage grading workflows. It seamlessly integrates with grading servers via REST APIs.

- **Repository**: https://github.com/amrutur/colab_grading_client
- **Version**: 1.0.26
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
from colab_grading_client import show_teaching_assist_button, show_submit_eval_button, show_clear_output_button, authenticate
import requests

# Create a session
session = authenticate()

# Get help on a specific question
show_teaching_assist_button(session, AI_TA_URL, qnum=1, notebook_id="assignment1",
           institution_id="university", term_id="fall2026",
           course_id="cs101", WAIT_TIME=2.0)

# Clear large outputs before submission (if you have 3D visualizations, etc.)
show_clear_output_button()

# Submit your notebook for grading
show_submit_eval_button(session, AI_TA_URL, notebook_id="assignment1",
            course_id="cs101", term_id="fall2026",
            institution_id="university", WAIT_TIME=2.0)
```

### For Instructors

```python
from colab_grading_client import show_teaching_assist_button, upload_rubric, authenticate


session = authenticate(AI_TA_URL)

# Get help on a specific question
show_teaching_assist_button(session, AI_TA_URL, qnum=1, notebook_id="assignment1",
           institution_id="university", term_id="fall2026",
           course_id="cs101", WAIT_TIME=2.0)


upload_rubric(session, AI_TA_URL, notebook_id="assignment1", course_id="cs101",
           term_id="fall2026", institution_id="university" 
           )
```

## Features

### 🎓 Student Features

- **Interactive Assistance**: Get AI-powered help on specific questions using `ask_assist()`
- **Large Output Handling**: Clear large cell outputs (3D visualizations, plots) before submission

### 👨‍🏫 Instructor Features

- **Interactive Help with rubric**: Help with rubric questions and answers

### 🔧 Technical Features

- **Notebook Parsing**: Automatic extraction of questions, answers, and context from notebooks
- **Pattern Matching**: Flexible regex patterns for question/answer identification
- **Error Handling**: Robust timeout handling and graceful error messages

## Notebook Structure

### Marking Questions

Questions should be marked with the `**Q{number}: marks**` pattern:

```markdown
**Q1: 10**
What is the time complexity of binary search?
```

### Marking Answers

The first of a sequence of answer cells should  `##Ans` or `## Ans`

```markdown
##Ans

The time complexity is O(log n) because...
```

For rubric answer, the answer components can have percentages 

```markdown
##Ans

##40%
The time complexity is O(log n) because...

##60%
The reason is ....
```

### Server access information

Include this in a cell at the top of the notebook:

```python
#@title Please run this cell to install the client to access the AI-TA
I_TA_URL="https://ai-ta-326056429620.asia-south1.run.app/"
course_id="cp260"
notebook_id = "Midterm"
institution_id="IISc"
term_id = "2025-26"
!pip install colab-grading-client==1.0.26
import colab_grading_client as ta
```

### Authentication

Include this in a cell and run to authenticate:

```python
# @title Please run this cell to authenticate yourself using your gmail credentials. A separate window will open for this. copy the token and paste in the text box below and press enter key to complete the authentication. Sometimes text box doesnt display - in which case rerun the cell.
session=ta.authenticate(AI_TA_URL)
```
This will output: 
```markdown
Step 1: Click here to sign in with Google
Step 2: After signing in, copy the token shown on screen
Step 3: Paste the token below
Paste your token here: ··········
```
On clicking the signing - it will open a new window where after authentication with google,
a JWT token will be printed. This can be copied and pasted into the text box below step 3
to complete the authentication process.


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
|`upload_rubric`|upload the rubric to server|`session`,`AI_TA_URL`,`notebook_id`, `course_id`, `term_id`, `institution_id`, `WAIT_TIME` |

### Utility Functions

| Function | Description |
|----------|-------------|
| `get_notebook()` | Retrieve current notebook JSON |
| `parse_notebook()` | Extract questions, answers, and context |
| `clear_large_outputs()` | Clear outputs and show instructions |

## API Endpoints

The client communicates with a grading server via REST API:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/assist` | POST | Get teaching assistance |
| `/eval` | POST | Submit for evaluation |

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
