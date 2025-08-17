from state import *
from utils import *
from langchain_openai import ChatOpenAI
import sys , traceback , io
from pathlib import Path

env = {}
vars = ""

microtasks_dir = Path("prompts/microtasks")

with open("prompts/planner.md", "r", encoding="utf-8") as f:
    planner_prompt = f.read()

with open("prompts/coder.md", "r", encoding="utf-8") as f:
    coder_prompt = f.read()

with open("prompts/feedback.md", "r", encoding="utf-8") as f:
    feedback_prompt = f.read()

with open("prompts/formatter.md", "r", encoding="utf-8") as f:
    formatter_prompt = f.read()


llm = ChatOpenAI(model="gpt-4o-mini")



def planner(state: State):
    response = llm.invoke(f"{planner_prompt} task: {state["task"]}")
    state["plan"] = response.content
    print(state["plan"])
    return state

def coder(state: State):
    global vars

    code = ""
    response = ""

    # Accumulate all microtask prompts
    add_inf = ""
    for file_path in microtasks_dir.glob("*.md"):
        with open(file_path, "r", encoding="utf-8") as f:
            add_inf += f.read() + "\n\n"

    try:
        # Keep trying until code is extracted
        while not code:
            observation = state.get('observation','')

            if len(observation) > 90000:
                observation = observation[:-30000]


            response = llm.invoke(
                f"{coder_prompt} \nAdditional information: {add_inf} "
                f"\nTask: {state.get('task','')} "
                f"\nPlan: {state.get('plan','')} "
                f"\nHistory: {state.get('history','')} "
                f"\nObservation: {state.get('observation','')}"
            )
            code = extract_code(response.content)

        if code is None or code.strip() == "":
            state["observation"] = (
                "Observation: Unknown Format, Return in correct format\n"
                "Thought: thought\nCode:\n```python\n\ncode```"
            )
            state["redo"] = True
            return state

        # Include attachments, images, dataset info in additional info
        if state.get("images_b64"):
            add_inf += "\nAttached Images (base64 previews):\n" + "\n".join(state["images_b64"]) + "\n\n"
        if state.get("dataset_url"):
            add_inf += f"\nDataset available at: {state['dataset_url']}\n\n"
        if state.get("attachments"):
            add_inf += "Attachments provided: " + ", ".join(state["attachments"].keys()) + "\n\n"

        print("LLM response:\n", response.content)
        #print("Extracted code:\n", code)
        #print("Label:", extract_type(response.content))

        # Execute code safely
        capture = io.StringIO()
        stdout_backup = sys.stdout
        stderr_backup = sys.stderr
        sys.stdout = capture
        sys.stderr = capture
        
        try:
            exec(code, env)
            vars = return_shared_env_summary(env)
        except Exception as e:
            # Capture any error, including JSONDecodeError inside code
            traceback.print_exc(file=capture)
            state["redo"] = True
            state["observation"] = f"Exception in executed code:\n{capture.getvalue()}"
            print(state["observation"])
            return state
        finally:
            output = capture.getvalue()
            sys.stdout = stdout_backup
            sys.stderr = stderr_backup

        # Determine type of code and set state
        code_type = extract_type(response.content)
        print("Label ",code_type)
        if code_type == "Code:":
            state["redo"] = True
            state["observation"] = f"Observation: {output}\n Saved variables: {vars}"
            print(state["observation"])
        elif code_type == "Final Code:":
            state["redo"] = False
            state["final_code"] = code
        else:
            state["redo"] = True
            state["observation"] = "Unknown Format"

    except Exception as e:
        # Catch any unexpected error (LLM call, streaming, etc.)
        capture = io.StringIO()
        traceback.print_exc(file=capture)
        state["observation"] = f"Unexpected error in coder:\n{capture.getvalue()}"
        state["redo"] = True

    # Update history safely
    delimiter = "\n---\n"
    history_steps = state.get("history", "").split(delimiter) if state.get("history") else []
    history_steps.append(response.content if response else "No response from LLM")
    if len(history_steps) > 5:
        history_steps = history_steps[2:]  # keep last 5 steps
    state["history"] = delimiter.join(history_steps)

    return state


def feedback(state: State):

    global vars
    add_inf = ""

    for file_path in microtasks_dir.glob("*.md"):
        with open(file_path, "r", encoding="utf-8") as f:
            prompt = f.read()
            add_inf += prompt + "\n\n"

    prompt = feedback_prompt + f"Task: {state['task']} \n Plan: {state['plan']} \n Additional Information:\n {add_inf} \n History: {state['history']} \n Observation (coder output & saved variables): {state['observation']} {vars}"
    response = llm.invoke(prompt)
    state['instructor'] = response.content.strip()
    #print("Feedback: ",state["instructor"])
    return state

def formatter(state: State):
    global vars
    vars = return_shared_env_summary(env)
    
    prompt = formatter_prompt + f"Task: {state['task']}\nFinal Code: {state['final_code']}\nSaved Variables: {vars}\n"

    while "return_saved_variables" not in env:
        response = llm.invoke(prompt)
        
        code = extract_code(response.content)
        print(f"Formatted Code: \n {code}")
    
        exec(code, env)

    state["final_output"] = env["return_saved_variables"]()
    return state


            




