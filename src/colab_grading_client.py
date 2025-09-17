'''
client side library for grading and scoring assistant for
colab notebooks. It connects with an grading assistant over rest API
'''

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

def get_cell_idx(cells,qnum:str):
  ''' returns the first cell index that has the string qnum contained in it'''
  for i,cell in enumerate(cells):
    for _,ele in enumerate(cell['source']):
      if qnum in ele:
        return i

def get_question_cell(qnum:str):
  '''get the contents of the question cell corresponding to the question qnum.
  return cell content of the cell and the cell type (code, markdown, raw)
  '''
  nb = _message.blocking_request('get_ipynb')
  cells = [cell for i,cell in enumerate(nb['ipynb']['cells'])]
  idx = get_cell_idx(cells,qnum)
  return cells[idx]['source'], cells[idx]['cell_type']


def get_answer_cell(qnum:str):
  '''get the contents of the answer cell corresponding to the question qnum.
  Assumption is that it is the next cell to the answer cell
  return cell content of the cell and the cell type (code, markdown, raw)
  '''
  nb = _message.blocking_request('get_ipynb')
  cells = [cell for i,cell in enumerate(nb['ipynb']['cells'])]
  idx = get_cell_idx(cells,qnum)
  return cells[idx+1]['source'], cells[idx+1]['cell_type']

def form_prompt(qnum:str):
  sentences,_ = get_question_cell(qnum)
  question = "The question asked is: "+" ".join(sentences)+"\n"
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

def check_answer(q_id:str):

  prompt = form_prompt(q_id)
  payload = {
    "query": prompt,
    "course_name":course_id,
    "notebook_name": notebook_id,
    "q_name":q_id,
    "url" : encoded_link
  }
  if GRADER_URL is None:
    display(Markdown(prompt))
    print("Sorry CP220-2025 Grader is not available yet")
    return
  try:
      response = requests.post(GRADER_URL+"query",json=payload)

      if response.status_code == 200:
        data = response.json()
        print("Grader's response is: \n")
        display(Markdown(data['response']))
      else:
        print(f"Call to grader failed with status code: {response.status_code}")
        print("Error message:", response.text)

  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

# @title Trial code to Login using your google account (not active yet)


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

# @title Check Answer
def show_teaching_assist_button(q_id:str):
    clear_output()
    # Create a button
    button = Button(description=f"Check my answer to question {q_id}!", button_style='info', layout=Layout(width='auto'))
    # Attach the function to the button's click event
    button.on_click(lambda b:check_answer(q_id))
    # Display the button in the notebook
    display(button)