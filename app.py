from flask import Flask, request, jsonify
from flask_cors import CORS  # <-- Import CORS
from main import graph
import tempfile, os, base64

app = Flask(__name__)
CORS(app)

def read_attachments(files):
    statement_text = ""
    images_b64 = []
    dataset_url = None
    attachments = {}

    for filename, file_storage in files.items():
        ext = filename.lower()
        data = file_storage.read()
        attachments[filename] = data

        if ext.endswith(('.txt', '.md')):
            statement_text += data.decode('utf-8', errors='ignore') + "\n"
        elif ext.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            b64_str = base64.b64encode(data).decode('utf-8')
            images_b64.append(f"data:image/{ext.split('.')[-1]};base64,{b64_str}")
        elif ext.endswith(('.csv', '.xlsx')):
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, "wb") as f:
                f.write(data)
            dataset_url = file_path  # Save the path for the LLM agent

    return statement_text.strip(), images_b64, dataset_url, attachments


@app.route("/api/", methods=["POST"])
def analyze():
    statement_text, images_b64, dataset_url, attachments = read_attachments(request.files)

    if not statement_text:
        return jsonify({"error": "questions.txt or .md required for task description"}), 400

    initial_state = {
        "task": statement_text,
        "history": "",
        "observation": "",
        "instructor": "",
        "attachments": attachments,
        "images_b64": images_b64,
        "dataset_url": dataset_url
    }

    # Compile and invoke your LLM-based graph
    app_instance = graph.compile()
    try:
        result_state = app_instance.invoke(initial_state, config={"recursion_limit": 60})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(result_state.get("final_output", {}))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
