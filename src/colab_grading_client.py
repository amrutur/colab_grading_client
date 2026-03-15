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
import time

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


def authenticate(AI_TA_URL:str)->requests.Session:
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
    session.user_info = user
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
      if 'text/plain' in output.get(')data',{}):
        if 'text' not in cell_output:
          cell_output['text'] = "Code Output:\n"
        cell_output['text'] += ''.join(output["data"]["text/plain"])
      elif 'image/png' in output.get('data',{}):
        cell_output['inline_data'] = {'mime_type':'image/png',\
                                    'data': output["data"]["image/png"]}
      elif 'image/jpeg' in output.get('data',{}):
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

def get_notebook(max_retries:int = 5, retry_delay:float = 0.5):
  '''
  Get the current notebook's JSON from the Colab frontend.
  Retries a few times if the frontend connection is not ready.
  Returns the notebook dict or None if all retries fail.

  Note: Large cell outputs (e.g., 3D visualizations, large plots) can cause
  the request to fail. Consider clearing outputs before submission if this occurs.
  '''
  for attempt in range(max_retries):
    try:
      nb = _message.blocking_request('get_ipynb', timeout_sec=10)
      if nb is not None:
        return nb
    except Exception as e:
      # blocking_request can raise exceptions for timeouts or oversized responses
      if attempt == max_retries - 1:
        print(f"Warning: Failed to retrieve notebook - {type(e).__name__}: {e}")
        print("If you have large cell outputs (3D visualizations, large plots), try:")
        print("  1. Runtime > Restart and clear outputs")
        print("  2. Or clear specific cell outputs before submitting")
        return None

    if attempt < max_retries - 1:
      # Exponential backoff: 0.5s, 1s, 2s, 4s
      delay = retry_delay * (2 ** attempt)
      print(f"Waiting for notebook to load, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
      time.sleep(delay)

  print("Error: Could not access the notebook. Please ensure the notebook is fully loaded and try again.")
  print("If you have large cell outputs (3D visualizations, large plots), try clearing them first.")
  return None
def split_the_answer(inp):
  '''
  split the answer into answer components, along with the percentages
  Each component is preceded by hashnumberpercent followed by the answer component text. If there are no components, the entire answer is considered as one component with 100 percent.

  return a list of json with 'percent':percent, 'component':component string
  '''

  spat = r'\s*\#\#\s*(\d+)\s*\%\s*'
  ans_comp=re.split(spat,inp)

  answer_parts=[]
  if (len(ans_comp) == 1):
    answer_parts.append({'percent':100,'component':ans_comp[0]})
    return answer_parts

  if (len(ans_comp[1:]) %2 != 0):
    print('ERROR: Missing answer components')
    return None

  i=1
  fraction_till_now = 0.0
  while i <len(ans_comp[1:]):
    k = ans_comp[i]
    if (re.match(r'\d+',k)):
      fraction_till_now += int(k)
      answer_parts.append({'percent':int(k),'component':ans_comp[i+1]})
      i +=2
    else:
      print("ERROR: Missing marks percent")
      return None

  if fraction_till_now != 100.0:
    print('ERROR: percents dont add up to 100')
    return None

  return answer_parts

def parse_notebook(nb):
  '''
    Extract the questions cells, the answer cells, their output and the context cells
    (everything other than the question and answer cells)
    The context is auto-regressive (context for each question is all cells
    from beginning till the question cell)

    Assumes the following structure for the notebook
    0 or more context cells (cell_type is code or markdown)
    1 or more question cells. has pattern starstarQ<qnum>:marks (cell_type is code or markdown)
    1 or more answer cells. has pattern hashhashAns either in code or markdowncell
    The rubric answer might have components indicating fractional marks in percentage as hashinteerpercentage followed by the answer component.
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
  #if qnum is missing - a random number will be generated,
  qpat = r"\s*\*\*\s*[qQ]\s*(\d+)\s*:?\s*\(?(\d+\.\d|\d+)?.*?\n(.*)"
  #pattern for an answer cell
  apat = r"\#\#\s*[aA]ns"
  apat1 = r"\s*\#\#\s*[aA]ns.*?\n(.*)"
  #Pattern for marking the beginning of a chat cell
  chatpat = r"\*\*\s*[cC]hat.*?(\n.*)"
  #Pattern for m:arking the button enabled cell
  tapat = r"show_teaching_assist_button\("
  #pattern to identify a function definition in a cell
  fdefpat = r"\s*def"

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
        marks = 10  #set default marks to 10 if not specified     
      max_marks += float(marks)
      #print(f"cell {i} is Question: qnum={qnum} source={cells[i]['source']}")
      nb_questions[str(qnum)]={'question':cell_content,'marks':float(marks)}
      nb_answers[str(qnum)] = ""
      #Capture the context and reset for next chat segment
      nb_contexts[str(qnum)] = context
      context = ""
      state = QUESTION
      continue
    amatch = re.search(apat, cell_content) #cell with answer pattern
    if amatch: 
      #this an answer cell with one or more answer cells following it
      amatch1 = re.search(apat1,cell_content,re.DOTALL)
      if amatch1:
        cell_content = amatch1.group(1) #remove the leading line which has
      else:
        cell_content = "" #no content in answer cell, just the pattern line
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
      if context != "":
        #context cells followed by chat button (instructor notebook)
        nb_contexts[str(qnum)] = context
        context = ""
      state = TABUTTON #anticipate the cell with TA assist  button
      continue
    tmatch = re.search(tapat, cell_content)
    fnomatch = not re.search(fdefpat, cell_content)
    if fnomatch and tmatch:
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

  for k in nb_answers:
    splt = split_the_answer(nb_answers[k])
    if splt is None:
      print(f"ERROR: Check answer for question number: {k}")
      return None
    else:
      nb_answers[k]=splt

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

  nb = get_notebook()
  if nb is None:
    return
  context, questions, answers, outputs, ta_chat, _ = parse_notebook(nb)

  # Check if qnum exists in the parsed notebook
  qnum_str = str(qnum)
  if qnum_str not in questions:
    print(f"Error: Question {qnum} not found in the notebook.")
    print("Make sure your question is marked with **Q{qnum}** pattern.")
    return

  payload = {
    "qnum":qnum,
    "context": context.get(qnum_str, ""),
    "question": questions.get(qnum_str, ""),
    "answer": answers.get(qnum_str, ""),
    "output": outputs.get(qnum_str, ""),
    "ta_chat": ta_chat.get(qnum_str, ""),
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
      resp = session.post(AI_TA_URL+"assist",json=payload, timeout=WAIT_TIME*60, stream=True)
      if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return
      for line in resp.iter_lines():
        if not line:
          continue
        msg = json.loads(line)
        if msg["type"] == "heatbeat":
          continue #keep alive, ignore
        elif msg["type"] == "progress":
          print(msg["message"])
        elif msg["type"] == "response":
          display(Markdown(msg["response"])) #final answer
        elif msg["type"] == "error":
          raise Exception(msg["detail"])
  except requests.exceptions.Timeout:
    print(f"The AI TAssistant is taking too long. Please retry after some time.")
  except requests.exceptions.RequestException as e:
    print(f"ask_assist: An error occurred: {e}")

def submit_eval(session:requests.Session, 
                AI_TA_URL:str, 
                notebook_id: str,
                institution_id: str, 
                term_id: str,
                course_id: str,
                WAIT_TIME:float = 2.0):

  '''
  The notebook is parsed and submitted for evaluation.
  Evaluated notebooks will be shared via email separately.
  '''

  nb = get_notebook()
  if nb is None:
    return
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
      print("Please wait, submitting to AI TA ...")

      resp = session.post(AI_TA_URL+"eval",json=payload, timeout=WAIT_TIME*60, stream=True)

      if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return
      for line in resp.iter_lines():
        if not line:
          continue
        msg = json.loads(line)
        if msg["type"] == "heatbeat":
          continue #keep alive, ignore
        elif msg["type"] == "progress":
          print(msg["message"])
        elif msg["type"] == "response":
          display(Markdown(msg["response"]))
        elif msg["type"] == "error":
          print(f"Error: {msg['detail']}")


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
  nb = get_notebook()
  if nb is None:
    return
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
    #clear_output()
    # Create a button
    button = Button(description=f"Check/Help with question Q{qnum}!", button_style='info', layout=Layout(width='auto'))
    # Attach the function to the button's click event
    button.on_click(lambda b:ask_assist(session, AI_TA_URL, qnum, notebook_id, institution_id, term_id, course_id, WAIT_TIME))
    # Display the button in the notebook
    display(button)

def show_submit_eval_button(session:requests.Session, 
                                AI_TA_URL:str, 
                                notebook_id:str,
                                institution_id:str,
                                term_id:str,
                                course_id:str,
                                WAIT_TIME:float = 2.0):
    # Create a button
    button = Button(description=f"Submit my notebook!", button_style='info', layout=Layout(width='auto'))
    # Attach the function to the button's click event
    button.on_click(lambda b:submit_eval(session,AI_TA_URL,notebook_id, institution_id, term_id, course_id, WAIT_TIME))
    # Display the button in the notebook
    display(button)

def clear_large_outputs():
    """
    Clears the current cell's output and provides instructions for clearing all outputs.

    Large outputs (like 3D visualizations, large plots) can prevent the grading client
    from reading the notebook. This function helps users clear those outputs.
    """
    clear_output(wait=False)
    display(Markdown("""
### ✅ Current cell output cleared!

If you have **large outputs** from other cells (3D visualizations, plots), you can:

1. **Clear all outputs**: Go to `Runtime > Restart and clear outputs`
2. **Clear specific cell**: Click the three dots on a cell output and select "Clear output"

**Large outputs can cause submission errors**, especially from:
- Open3D 3D visualizations
- Large matplotlib plots
- Interactive widgets
- Large data displays

After clearing, you can safely use `ask_assist()` or `submit_eval()`.
    """))

def show_clear_output_button():
    """
    Displays a button to clear large outputs that might interfere with notebook submission.

    Useful to call before ask_assist() or submit_eval() if you have large cell outputs.
    """
    #clear_output()
    # Create a button
    button = Button(description="Clear Output", button_style='warning', layout=Layout(width='auto'))
    # Attach the function to the button's click event
    button.on_click(lambda b: clear_large_outputs())
    # Display the button in the notebook
    display(button)