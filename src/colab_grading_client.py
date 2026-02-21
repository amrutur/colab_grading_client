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

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

from google.auth.transport.requests import Request
import google.auth
from google.colab import auth
from google.oauth2 import id_token

from google.genai import types

import random
import string

def generate_random_string(l:int)->str:
  '''Generate random string of length l
  using lower case ascii a-z and digits 0-9
  '''
  # Define the pool of characters for the random part
  random_chars = string.ascii_lowercase + string.digits # a-z and 0-9

  result_string = ''

  # Append 3 random characters from the pool
  for _ in range(l):
    result_string += random.choice(random_chars)
  
  return result_string


def authenticate():
    import requests
    import getpass
    from IPython.display import display, HTML
    
    login_url = f"{AI_TA_URL}/login"
    
    display(HTML(f"""
        <p><strong>Step 1:</strong> <a href="{login_url}" target="_blank">Click here to sign in with Google</a></p>
        <p><strong>Step 2:</strong> After signing in, copy the token shown on screen</p>
        <p><strong>Step 3:</strong> Paste the token below</p>
    """))
    
    token = getpass.getpass("Paste your token here: ")
    
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{AI_TA_URL}/whoami", headers=headers)
    
    if resp.status_code == 401:
        raise ValueError("Invalid token — please sign in again")
    
    user = resp.json()
    print(f"Authenticated as: {user['name']} ({user['email']})")
    
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session

def get_cell_output(cell):
  '''
  get the output of the cell and return as a json object.
  cell_output['text'] has a single string that concatenates all textlines in cell's output
  cell_output['inline_data']={'mime_type':mime_type,'data':data}


  Currently only mime_types of image/png and image/jpeg are supported
  '''

  cell_output  = {}

  if 'outputs' not in cell:
    #no output
    return cell_output

  for output in cell["outputs"]:
    if output["output_type"] == "stream":
      if 'text' not in cell_output:
        cell_output['text'] = "Code Output:\n"
      cell_output['text'] += ''.join(output["text"])
    elif output["output_type"] == "error":
      if 'error' in cell_output:
        cell_output['error'] += "Code Error:\n"
        cell_output['error'] += f"{output.ename}:{output.evalue}"+"\ntraceback="+''.join(output["traceback"])
    elif output["output_type"] == "execute_result":
      if 'text/plain' in output.get('data',{}):
        if 'text' not in cell_output:
          cell_output['text'] = "Code Output:\n"
        cell_output += ''.join(output["data"]["text/plain"])
      elif 'image/png' in output.get('data',{}):
        cell_output['inline_data'] = {'mime_type':'image/png',\
                                    'data': output["data"]["image/png"]}
      elif 'image/jpeg' in output('data',{}):
        cell_output['inline_data']={'mime_type':'image/jpeg',\
                                    'data':output["data"]["image/jpeg"]}
    elif output["output_type"] == "display_data":
      if "image/png" in output.get('data',{}):
        cell_output['inline_data'] = {'mime_type':'image/png',\
                                    'data': output["data"]["image/png"]}

      elif "image/jpeg" in output.get('data',{}):
        cell_output['inline_data']={'mime_type':'image/jpeg',\
                                    'data':output["data"]["image/jpeg"]}

  return cell_output

def parse_notebook(nb):
  '''
    Extract the questions cells, the answer cells, their output and the context cells
    (everything other than the question and answer cells)
    The context is auto-regressive (context for each question is all cells
    from beginnig till the question cell)

    Assumes the following structure for the notebook
    0 or more context cells (cell_type is code or markdown)
    1 or more question cells. has pattern starstarQ<qnum>:marks (cell_type is code or markdown)
    1 or more answer cells. has pattern hashhashAns either in code or markdowncell
    The answer cell might have one or more answer cells following it. 
    NOTE: The  output of only the last code based answer cell is captured. 
    1 chat cell. has pattern starstarChat ...
    1 ta interaction cell. is a code cell with showunderscoreteachingunderscoreassist button
  '''

  cells = nb['ipynb']['cells']
  nb_contexts = {}
  nb_questions = {}
  nb_answers = {}
  nb_tachat={}
  nb_outputs={}
  max_marks = 0.0

  #Pattern for marking a question cell with optional question number and marks
  #if qnum is missing - a randome number will be generated,
  qpat = r"\s*\*\*\s*[qQ]\s*(\d*).*?(?::?\s*?\(?)(\d+\s|\d+\.?\d+)?.*?\n(.*)"
  #pattern for an answer cell
  apat = r"\s*\#\#Ans.*?\n(.*)"
  #Pattern for marking the beginning of a chat cell
  chatpat = r"^(\*\*\s*[cC]hat).*\n(.*)"
  #Pattern for m:arking the button enabled cell
  tapat = r"^show_teaching_assist_button"

  #States
  CONTEXT=0
  QUESTION=1
  ANSWER=2

  TABUTTON=3

  #initial state starts assembling context for the question
  qnum = 0 #question number
  state = CONTEXT
  context = ""   #variable to accumuluate context (which is non-question/non-answer) between chat cells
  for i in range (len(cells)):
    cell = cells[i]
    cell_content=''.join(cell['source'])
    cell_output = get_cell_output(cell)
    qmatch = re.search(qpat, cell_content,re.DOTALL)
    if qmatch:
      #this is a question cell with one or more question cells following it
      qnum = qmatch.group(1)
      marks = qmatch.group(2)
      cell_content = qmatch.group(3)
      if qnum is None:
        qnum = random.randint(1000,9999)
      if qnum in nb_questions:
        print("Error: question {qnum} already exists")
        break 
      if marks is None:
        marks = 0       
      max_marks += marks
      #print(f"cell {i} is Question: qnum={qnum} source={cells[i]['source']}")
      nb_questions[str(qnum)]={'question':cell_content,'marks':marks}
      nb_answers[str(qnum)] = ""
      #Capture the context and reset for next chat segment
      nb_contexts[str(qnum)] = context
      context = ""
      state = QUESTION
      continue
    amatch = re.search(apat, cell_content,re.DOTALL)
    if amatch: 
      #this an answer cell with one or more answer cells following it
      cell_content = amatch.group(1) #remove the leading line which has
      #print(f"cell {i} is answer cell")
      if state == QUESTION:
        nb_answers[str(qnum)] = cell_content
        nb_outputs[str(qnum)] = cell_output
        state = ANSWER
      else:
        print("Error: No question has been asked for this answer!")
        #capture context and reset for next chat segment
        state = CONTEXT
      continue
    cmatch = re.search(chatpat, cell_content,re.DOTALL)
    if cmatch:
      #this is a chat
      #print(f"cell:{i} chat:{qnum}: is a chat cell")
      nb_tachat[str(qnum)] = cell_content
      #Capture the context and reset for next chat segment
      if context is not None:
        #context cells followed by chat button (instructor notebook)
        nb_contexts[str(qnum)] = context
        context = ""
      state = TABUTTON #anticipate the cell with TA assist  button
      continue
    tmatch = re.search(tapat, cell_content)
    if tmatch:
      #cell calls the AI tutor, dont capture anything
      state=CONTEXT
      continue
    if state == CONTEXT:
      context +=  cell_content
    elif state == QUESTION:
      #append cells to question till you hit a cell with Ans pattern
      nb_questions[str(qnum)]['question'] += cell_content
    elif state == ANSWER:
      #assemble the answers
      nb_answers[str(qnum)] +=  cell_content
      nb_outputs[str(qnum)] = cell_output #Note will override outputs of previous answer cells
    elif state == TABUTTON:
      #should not have reached here if the cell with ta button was present
      print("ERROR: missing code cell with show_teaching_assist_button for this chat box")
      state = CONTEXT
      context = ""

  return nb_contexts, nb_questions, nb_answers, nb_outputs, nb_tachat, max_marks

def ask_assist(session:requests.Session, 
               AI_TA_URL:str, 
               qnum:int, 
               notebook_id:str, 
               institution_id:str, 
               term_id:str, 
               course_id:str,
               WAIT_TIME:float = 2.0
               ):
  '''
  form the prompt and send it to the AI_TA server for
  an answer
  '''

  nb = _message.blocking_request('get_ipynb')
  context, questions, answers, outputs, ta_chat, _ = parse_notebook(nb)
  
  payload = {
    "qnum":qnum,
    "context": context[str(qnum)],
    "question": questions[str(qnum)],
    "answer": answers[str(qnum)],
    "output": outputs[str(qnum)],
    "ta_chat":ta_chat[str(qnum)],
    "notebook_id": notebook_id,
    "institution_id": institution_id,
    "term_id": term_id,
    "course_id":course_id
  }

  if AI_TA_URL is None:
    display(Markdown(prompt))
    print("AI Teaching Assistant url (AI_TA_URL) is not set")
    return
  try:
      print("Please wait, asking the AI TA ...")
      response = session.post(AI_TA_URL+"assist",json=payload, timeout=WAIT_TIME*60)

      if response.status_code == 200:
        data = response.json()
        print("AI TAssistant's response is: \n")
        display(Markdown(data['response']))
      else:
        print(f"Call to AI TAssistant failed with status code: {response.status_code}")
        print("Error message:", response.text)

  except requests.exceptions.Timeout:
    print(f"The AI TAssistant is taking too long. Please retry after some time.")
  except requests.exceptions.RequestException as e:
    print(f"ask_assist: An error occurred: {e}")

def submit_eval(session:requests.Session, 
                AI_TA_URL:str, 
                notebook_id: str,
                course_id: str, 
                term_id: str,
                institution_id:str,
                WAIT_TIME:float = 2.0):

  '''
  The notebook is parsed and submitted for evaluation.
  Evaluated notebooks will be shared via email separately.
  '''

  nb = _message.blocking_request('get_ipynb')
  context,questions,answers,outputs,_,_ = parse_notebook(nb)

  payload = {
      "notebook_id": notebook_id,
      "context": context,
      "questions": questions,
      "answers": answers,
      "outputs":outputs,
      "institution_id": institution_id,
      "term_id": term_id,
      "course_id": course_id,  
    }

  if AI_TA_URL is None:
    display(Markdown(prompt))
    print("ERROR: AI-TA URL is None")
    return
  try:
      response = session.post(AI_TA_URL+"eval",json=payload, timeout=WAIT_TIME*60)

      if response.status_code == 200:
        data = response.json()
        print("AI TAssistant's response is: \n")
        display(Markdown(data['response']))
      else:
        print(f"Call to AI TAssistant failed with status code: {response.status_code}")
        print("Error message:", response.text)

  except requests.exceptions.Timeout:
    print(f"The AI Teaching assistant is taking too long. Please retry after some time.")
  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

def upload_rubric(session:requests.Session, 
                  AI_TA_URL:str, 
                  notebook_id: str, 
                  course_id: str, 
                  term_id:str, 
                  institution_id:str, 
                  WAIT_TIME:float = 2.0):
  '''
  upload the context, question, answers to the server.
  The uploader needs to be authenticated as a instructor for the course.
  '''
  nb = _message.blocking_request('get_ipynb')
  context,questions,answers,outputs,_,max_marks = parse_notebook(nb)

  payload = {
      "notebook_id": notebook_id,
      "max_marks":max_marks,
      "context": context,
      "questions": questions,
      "answers": answers,
      "outputs":outputs,
      "institution_id": institution_id,
      "term_id": term_id,
      "course_id": course_id,  
    }

  if AI_TA_URL is None:
    display(Markdown(prompt))
    print("ERROR: AI-TA URL is None")
    return
  try:
      response = session.post(AI_TA_URL+"upload_rubric",json=payload, timeout=WAIT_TIME*60)

      if response.status_code == 200:
        data = response.json()
        print("AI TAssistant's response is: \n")
        display(Markdown(data['response']))
      else:
        print(f"Call to AI TAssistant failed with status code: {response.status_code}")
        print("Error message:", response.text)

  except requests.exceptions.Timeout:
    print(f"The AI Teaching assistant is taking too long. Please retry after some time.")
  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

def show_teaching_assist_button(session:requests.Session, 
                                AI_TA_URL:str, 
                                qnum:int,
                                notebook_id:str,
                                institution_id:str,
                                term_id:str,
                                course_id:str,
                                WAIT_TIME:float = 2.0):
    clear_output()
    # Create a button
    button = Button(description=f"Check/Help with question Q{qnum}!", button_style='info', layout=Layout(width='auto'))
    # Attach the function to the button's click event
    button.on_click(lambda b:ask_assist(session, AI_TA_URL, qnum, notebook_id, institution_id, term_id, course_id, WAIT_TIME))
    # Display the button in the notebook
    display(button)

def show_submit_eval_button(session:requests.Session,AI_TA_URL:str, user_name:str, user_email:str, course_id: str=None, notebook_id: str=None, rubric_link:str=None, WAIT_TIME:float = 2.0):
    clear_output()
    # Create a button
    button = Button(description=f"Submit my notebook!", button_style='info', layout=Layout(width='auto'))
    # Attach the function to the button's click event
    button.on_click(lambda b:submit_eval(session,AI_TA_URL, user_name, user_email, course_id, notebook_id, rubric_link, WAIT_TIME))
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


def submit_nb_eval(session:requests.Session, notebook_url, AI_TA_URL, rubric_link, course_id, notebook_id):
  '''
  Submit the notebook from the for evaluation to the GRADER.
  NEEDS TO BE FIXED.
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

  if AI_TA_URL is None:
    #display(Markdown(prompt))
    print("AI_TA_URL is not set")
    return False
  try:
      # Capture the actual request being sent
      #req = requests.Request('POST', AI_TA_URL, json=payload)
      #prepared = session.prepare_request(req)

      #print("URL:", prepared.url)
      #print("Headers:", prepared.headers)
      #print("Body:", prepared.body)

      #send to server
      response = session.post(AI_TA_URL+"eval",json=payload)

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

def fetch_graded_response(session:requests.Session, AI_TA_URL, notebook_id, student_id):
  '''
  Fetch the graded response from the GRADER
  '''
  payload = {
    "notebook_id": notebook_id,
    "student_id":student_id,
    "institution_id": institution_id,
    "term_id": term_id,
    "course_id": course_id,
  }

  if AI_TA_URL is None:
    #display(Markdown(prompt))
    print("AI_TA_URL is not set")
    return False
  try:
      response = session.post(AI_TA_URL+"fetch_grader_response",json=payload)

      if response.status_code == 200:
        data = response.json()
        print("AI TAssistant's response is: \n")
        return(data['grader_response'])
      else:
        print(f"Call to Assistant failed with status code: {response.status_code}")
        print("Error message:", response.text)
        return None

  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    return None

def fetch_marks_list(session:requests.Session, 
                     AI_TA_URL, 
                     institution_id:str, 
                     term_id:str, 
                     course_id:str, 
                     notebook_id: str):
  '''
  Fetch the list of students and their marks for notebook_id from the GRADER
  '''
  payload = {
    "institution_id": institution_id,
    "term_id": term_id,
    "course_id": course_id,
    "notebook_id": notebook_id,
  }

  if AI_TA_URL is None:
    #display(Markdown(prompt))
    print("Sorry Teaching Assistant is not available yet. Try again later")
    return False
  try:
      response = session.post(AI_TA_URL+"fetch_marks_list",json=payload)

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

def notify_student_grades(session:requests.Session, AI_TA_URL, institution_id: str, term_id: str, course_id: str, notebook_id, user_gmail)->bool:
  '''
  Send email to the student with the graded answer book
  '''
  payload = {
    "institution_id": institution_id,
    "term_id": term_id,
    "course_id": course_id,
    "notebook_id": notebook_id,
    "student_id": user_gmail
  }

  if AI_TA_URL is None:
    #display(Markdown(prompt))
    print("AI_TA_URL is empty")
    return False
  try:
      response = session.post(AI_TA_URL+"notify_student_grades",json=payload)

      if response.status_code == 200:
        print (response.json())
        return True
      else:
        print(f"Call to Assistant failed with status code: {response.status_code}")
        print("Error message:", response.text)
        return False

  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    return False