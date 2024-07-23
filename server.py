from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from langchain_core.messages import BaseMessage
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
import os
from db_Model import ask_model, ocr_image, pdf_reader, send_to_mongodb, unsupported_file_type, check_extension, check_condition, check_value_of_image
from states.state import state, graph

config = RunnableConfig(recursion_limit=200)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
        
    state['fileName']=file.filename
    state['filePath']=os.path.join(UPLOAD_FOLDER, file.filename)

    if file:
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))

        graph.add_node("check_extension", check_extension)
        graph.add_node("check_condition", check_condition)
        graph.add_node("pdf_reader", pdf_reader)
        graph.add_node("ocr_image", ocr_image)
        graph.add_node("ask_model", ask_model)
        # graph.add_node("convert_to_json", convert_to_json) 
        graph.add_node("send_to_mongodb", send_to_mongodb)

        graph.set_entry_point("check_extension")
        graph.add_conditional_edges("check_condition", check_value_of_image, {True: "ocr_image", False: "pdf_reader"})
        graph.add_edge("check_extension", "check_condition")
        graph.add_edge("pdf_reader", "ask_model")
        graph.add_edge("ocr_image", "ask_model")
        # graph.add_edge("ask_model", "convert_to_json")
        graph.add_edge("ask_model", "send_to_mongodb")
        graph.add_edge("send_to_mongodb", END)
        print("compile")
        app=graph.compile()
        app.invoke(state)
        print("ending")

        return jsonify({'message': 'Data successfully processed', 'state': state}), 200

    return jsonify({'message': 'Allowed file types are image and pdf'}), 400

if __name__ == '__main__':
    app.run(port=4000, debug=True)
