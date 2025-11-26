'''
Client side library for grading and scoring assistant for
colab notebooks. It connects with an grading assistant over rest API

(c) Bharadwaj Amrutur
'''
# @title Dont Edit. Some functions to help with uploading and evaluation.
import requests
from urllib.parse import quote
from google.colab import _message
import json
from IPython.display import Latex, Markdown, HTML
import requests
from ipywidgets import Button, Layout
from IPython.display import display, clear_output
import json # Import json for pretty printing
from ipywidgets import Button, Layout
from IPython.display import display, clear_output
import re
import hashlib
from typing import Any, Dict
import re

from google.colab import auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import json
import io


def calculate_json_md5(data: Dict[str, Any]) -> str:
    """
    Calculates the MD5 hash of a JSON-compatible Python dictionary.

    Crucially, this function serializes the dictionary in a deterministic
    way (sorted keys, no separators, no whitespace) to ensure the hash
    is the same every time, regardless of Python version or runtime.

    Args:
        data (Dict[str, Any]): The JSON-compatible Python dictionary.

    Returns:
        str: The hexadecimal MD5 hash string.
    """

    # 1. Serialize the data into a canonical JSON string
    #    - sort_keys=True: Ensures keys are ordered alphabetically.
    #    - separators=(',', ':'): Removes extra whitespace/indentation.
    #    - ensure_ascii=True: Ensures consistency in string representation.
    try:
        json_string = json.dumps(
            data,
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=True
        )
    except TypeError as e:
        # Handle cases where the dictionary contains non-serializable objects (like objects or functions)
        print(f"Error serializing JSON data: {e}")
        return ""

    # 2. Encode the string to bytes (MD5 works on bytes, not strings)
    #    - Using 'utf-8' is standard for consistent hashing.
    data_bytes = json_string.encode('utf-8')

    # 3. Calculate the MD5 hash
    md5_hash = hashlib.md5(data_bytes).hexdigest()

    return md5_hash

def get_cell_idx(cells,qnum:int):
  ''' returns the first cell index that has the string qnum contained in it'''
  qpat = r"\*\*Q"+f"{qnum}"+"\*\*"
  for i,cell in enumerate(cells):
    for _,ele in enumerate(cell['source']):
      if re.search(qpat,ele):
        return i

def get_question_cell(qnum:int):
  '''get the contents of the question cell corresponding to the question qnum.
  return cell content of the cell and the cell type (code, markdown, raw)
  '''
  nb = _message.blocking_request('get_ipynb')
  cells = [cell for i,cell in enumerate(nb['ipynb']['cells'])]
  idx = get_cell_idx(cells,qnum)
  return cells[idx]['source'], cells[idx]['cell_type']


def get_answer_cell(qnum:int):
  '''get the contents of the answer cell corresponding to the question qnum.
  Assumption is that it is the next cell to the answer cell
  return cell content of the cell and the cell type (code, markdown, raw)
  '''
  nb = _message.blocking_request('get_ipynb')
  cells = [cell for i,cell in enumerate(nb['ipynb']['cells'])]
  idx = get_cell_idx(cells,qnum)
  return cells[idx+1]['source'], cells[idx+1]['cell_type']

def get_cells_to_evaluate():
  nb = _message.blocking_request('get_ipynb')
  cells = [cell for i,cell in enumerate(nb['ipynb']['cells'])]
  for i,cell in enumerate(cells):
    print(i, cell['source'])


def form_prompt(q_id:str):
  '''
  Form the prompt for LLM by extracting the 
  question from the cell containing q_id
  and the answer from the cell after it
  '''
  qpat = "[qQ](\d+)"
  qmat=re.search(qpat,q_id)
  if qmat is not None:
    qnum = int(qmat.group(1))
  else:
    print(f"Invalid format for question id {q_id}")
    return
  sentences,_ = get_question_cell(qnum)
  question = "The assignment question is: "+" ".join(sentences)+"\n"
  sentences,_ = get_answer_cell(qnum)
  answer = "The student's answer is: "+" ".join(sentences)+"\n"
  prompt = question+answer
  return prompt

def login():
  '''Log in to the app using google credentials'''

  try:
      response = requests.get(GRADER_URL)
      response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

      content_type = response.headers.get('Content-Type', '') # Use .get for safety
      print(f"Content-Type: {content_type}\n")
      display(HTML(response.text))

  except requests.exceptions.RequestException as e:
      print(f"An error occurred: {e}")

def ask_assist(GRADER_URL:str, q_id:str,rubric_link:str = None, WAIT_TIME:float = 2.0):

  prompt = form_prompt(q_id)

  payload = {
    "query": prompt,
    "q_id":q_id
  }
  if 'user_name' in globals(): #variable has been set
    payload['user_name'] = user_name

  if 'user_email' in globals(): #variable has been set
    payload['user_email'] = user_email

  if rubric_link is not None:
    payload['rubric_link'] = rubric_link

  if GRADER_URL is None:
    display(Markdown(prompt))
    print("Sorry Teaching Assistant is not available yet")
    return
  try:
      print("Please wait, asking the grader...")
      response = requests.post(GRADER_URL+"assist",json=payload, timeout=WAIT_TIME*60)

      if response.status_code == 200:
        data = response.json()
        print("Assistant's response is: \n")
        display(Markdown(data['response']))
      else:
        print(f"Call to assistant failed with status code: {response.status_code}")
        print("Error message:", response.text)

  except requests.exceptions.Timeout:
    print(f"The teaching assistant is taking too long. Please retry after some time.")
  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")


def check_answer(GRADER_URL:str, q_id:str, course_id:str, notebook_id:str, rubric_link:str = None):

  '''This function will be deprecated soon'''

  prompt = form_prompt(q_id)
  payload = {
    "query": prompt,
    "course_id":course_id,
    "notebook_id": notebook_id,
    "q_name":q_id
  }
  if rubric_link is not None:
    payload['rubric_link'] = rubric_link

  if GRADER_URL is None:
    display(Markdown(prompt))
    print("Sorry Teaching Assistant is not available yet")
    return
  try:
      response = requests.post(GRADER_URL+"assist",json=payload)

      if response.status_code == 200:
        data = response.json()
        print("Assistant's response is: \n")
        display(Markdown(data['response']))
      else:
        print(f"Call to assistant failed with status code: {response.status_code}")
        print("Error message:", response.text)

  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

def submit_eval(GRADER_URL:str, user_name:str, user_email:str, course_id: str=None, notebook_id: str=None,rubric_link:str = None, WAIT_TIME:float = 2.0):

  answer_notebook = _message.blocking_request('get_ipynb')
  #answer_notebook = nb['ipynb']['cells']
  answer_hash = calculate_json_md5(answer_notebook)
  #answer_notebook_string = json.dumps(answer_notebook)

  payload = {
    "course_id": course_id,
    "user_name": user_name,
    "user_email":user_email,
    "notebook_id": notebook_id,
    "answer_notebook": answer_notebook,
    "answer_hash":answer_hash,
    "rubric_link":rubric_link
  }

  if GRADER_URL is None:
    display(Markdown(prompt))
    print("Sorry Teaching Assistant is not available yet. Try again later")
    return
  try:
      print("Please wait, submitting to the grader...")
      response = requests.post(GRADER_URL+"eval",json=payload, timeout=WAIT_TIME*60)

      if response.status_code == 200:
        data = response.json()
        print("Assistant's response is: \n")
        display(Markdown(data['response']))
      else:
        print(f"Call to Assistant failed with status code: {response.status_code}")
        print("Error message:", response.text)

  except requests.exceptions.Timeout:
    print(f"The teaching assistant is taking too long. Please retry after some time.")
  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")



# Define a function to be called when the button is clicked
def on_login_button_clicked(b):
  login()

# Attach the function to the button's click event
def show_login_button ():
  clear_output()
  # Create a button
  button = Button(description="Login", button_style='info', layout=Layout(width='auto'))

  button.on_click(on_login_button_clicked)
  # Display the button in the notebook
  display(button)

def show_teaching_assist_button(GRADER_URL:str, q_id:str,rubric_link:str=None, WAIT_TIME:float = 2.0):
    clear_output()
    # Create a button
    button = Button(description=f"Check/Help with question {q_id}!", button_style='info', layout=Layout(width='auto'))
    # Attach the function to the button's click event
    button.on_click(lambda b:ask_assist(GRADER_URL, q_id, rubric_link, WAIT_TIME))
    # Display the button in the notebook
    display(button)

def show_submit_eval_button(GRADER_URL:str, user_name:str, user_email:str, course_id: str=None, notebook_id: str=None, rubric_link:str=None, WAIT_TIME:float = 2.0):
    clear_output()
    # Create a button
    button = Button(description=f"Submit my notebook!", button_style='info', layout=Layout(width='auto'))
    # Attach the function to the button's click event
    button.on_click(lambda b:submit_eval(GRADER_URL, user_name, user_email, course_id, notebook_id, rubric_link, WAIT_TIME))
    # Display the button in the notebook
    display(button)

def get_file_id_from_share_link(share_link: str) -> str or None:
    """
    Extracts the file ID from a Google Drive share link.

    Args:
        share_link: The Google Drive share link.

    Returns:
        The file ID as a string, or None if the link is invalid.
    """
    try:
        # Split the link by '/'
        parts = share_link.split('/')

        #print('from get_file_id_from_share_link', parts)

        # Find the index of 'd' or 'drive' which usually precedes the file ID
        if 'd' in parts:
            d_index = parts.index('d')
        elif 'drive' in parts:
            d_index = parts.index('drive')
        else:
            raise IndexError

        # The file ID is usually the next part after 'd'
        file_id = parts[d_index + 1]
        subparts = file_id.split('?')
        file_id = subparts[0]
        subparts = file_id.split('#')
        file_id = subparts[0]


        return file_id
    except ValueError:
        print("Invalid share link format.")
        return None
    except IndexError:
        print("Could not extract file ID from the share link.")
        return None

def download_colab_notebook(notebook_url):
    """Download a Colab notebook as JSON"""
    # Authenticate
    auth.authenticate_user()

    # Build service
    drive_service = build('drive', 'v3')

    file_id=get_file_id_from_share_link(notebook_url)

    # Download file
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%")

    # Parse JSON
    fh.seek(0)
    notebook_json = json.loads(fh.read().decode('utf-8'))

    return notebook_json


def get_user_info(nb):
  '''
  Extract user_name and user_email from the notebook.
  This is in the first code cell
  '''
  user_name = None
  user_email = None
  cells =  nb['cells']
  pat = r".*\s+user_name\s*=\s*[\"\'](.+)[\"\']\s+user_email\s*=\s*[\"\'](.*)[\"\']"
  cell_no = 0
  for cell in cells:
    if cell['cell_type'] == 'code' :
      #check whether this code cell defines these two
      txt = ' '.join(cell['source'][0:])
      #txt = cell['source'][1]
      print(f"Cell {cell_no}:"+txt.replace('\n', ' '))
      mat = re.match(pat, txt)
      if mat:
        user_name = mat.group(1)
        user_email = mat.group(2)
        #found in this code cell. So exit the for loop
        break
    cell_no += 1
  return user_name, user_email


def submit_nb_eval(notebook_url, GRADER_URL, rubric_link, course_id, notebook_id):
  '''
  Submit the notebook for evaluation to the GRADER
  '''
  answer_notebook = download_colab_notebook(notebook_url)
  if answer_notebook is None:
    print("Cant access notebook")
    return False


  user_name, user_email = get_user_info(answer_notebook)
  answer_hash = calculate_json_md5(answer_notebook)


  payload = {
    "course_id": course_id,
    "user_name": user_name,
    "user_email":user_email,
    "notebook_id": notebook_id,
    "answer_notebook": answer_notebook,
    "answer_hash":answer_hash,
    "rubric_link":rubric_link
  }
  #payload_str=json.dumps(payload,indent=4)
  #print(payload_str)
  print(f"Length of notebook = {len(json.dumps(payload['answer_notebook'],indent=4))}")

  if GRADER_URL is None:
    #display(Markdown(prompt))
    print("Sorry Teaching Assistant is not available yet. Try again later")
    return False
  try:

      # Capture the actual request being sent
      session = requests.Session()
      req = requests.Request('POST', GRADER_URL, json=payload)
      prepared = session.prepare_request(req)

      print("URL:", prepared.url)
      print("Headers:", prepared.headers)
      print("Body:", prepared.body)

      #send to server
      response = requests.post(GRADER_URL+"eval",json=payload)

      if response.status_code == 200:
        data = response.json()
        print("Assistant's response is: \n")
        display(Markdown(data['response']))
        return True
      else:
        print(f"Call to Assistant failed with status code: {response.status_code}")
        print("Error message:", response.text)
        return False

  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    return False

def fetch_graded_response(GRADER_URL, notebook_id, user_email):
  '''
  Fetch the graded response from the GRADER
  '''
  payload = {
    "notebook_id": notebook_id,
    "user_email": user_email
  }

  if GRADER_URL is None:
    #display(Markdown(prompt))
    print("Sorry Teaching Assistant is not available yet. Try again later")
    return False
  try:
      response = requests.post(GRADER_URL+"fetch_grader_response",json=payload)

      if response.status_code == 200:
        data = response.json()
        print("Assistant's response is: \n")
        return(data['grader_response'])
      else:
        print(f"Call to Assistant failed with status code: {response.status_code}")
        print("Error message:", response.text)
        return None

  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    return None

def fetch_student_list(GRADER_URL, notebook_id):
  '''
  Fetch the student list and the marks for notebook_id from the GRADER
  '''
  payload = {
    "notebook_id": notebook_id,
  }

  if GRADER_URL is None:
    #display(Markdown(prompt))
    print("Sorry Teaching Assistant is not available yet. Try again later")
    return False
  try:
      response = requests.post(GRADER_URL+"fetch_student_list",json=payload)

      if response.status_code == 200:
        data = response.json()
        return(data['response'])
      else:
        print(f"Call to Assistant failed with status code: {response.status_code}")
        print("Error message:", response.text)
        return None

  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    return None

def notify_student_grades(GRADER_URL, notebook_id, user_email):
  '''
  Send email to the student with the graded answer book
  '''
  payload = {
    "notebook_id": notebook_id,
    "user_email": user_email
  }

  if GRADER_URL is None:
    #display(Markdown(prompt))
    print("Sorry Teaching Assistant is not available yet. Try again later")
    return False
  try:
      response = requests.post(GRADER_URL+"notify_student_grades",json=payload)

      if response.status_code == 200:
        print (response.json())
        return True
      else:
        print(f"Call to Assistant failed with status code: {response.status_code}")
        print("Error message:", response.text)
        return False

  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    return None
