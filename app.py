import os
import json
import re
import ast
import traceback
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__, template_folder='.')

def clean_and_parse_json(response_text):
    try:
        # 1. حذف تگ‌های کد مارک‌داون
        text = re.sub(r'```json\s*', '', response_text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        # 2. پیدا کردن محدوده JSON واقعی
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
        
        # 3. تلاش برای پارس کردن
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # اگر نشد، شاید به خاطر سینگل کوتیشن پایتونی است
            return ast.literal_eval(text)
            
    except Exception as e:
        print(f"FAILED TO PARSE: {text}")
        return {
            "error": True,
            "reason": "خطا در خواندن پاسخ هوش مصنوعی. لطفاً دوباره تلاش کنید.",
            "raw_text": str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set-api', methods=['POST'])
def set_api():
    data = request.json
    try:
        genai.configure(api_key=data.get('api_key'))
        model = genai.GenerativeModel(data.get('model_name'))
        model.generate_content("Hi")
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    try:
        genai.configure(api_key=data.get('api_key'))
        model = genai.GenerativeModel(data.get('model_name'))
        
        prompt = f"""
        Act as a Math Analyst.
        Target Formula: "{data.get('formula')}"
        Context: "{data.get('context')}"
        Output JSON ONLY: {{"is_graphable": true/false, "reason": "Persian explanation"}}
        """
        
        response = model.generate_content(prompt)
        return jsonify(clean_and_parse_json(response.text))
    except Exception as e:
        return jsonify({'is_graphable': False, 'reason': str(e)})

@app.route('/visualize', methods=['POST'])
def visualize():
    data = request.json
    api_key = data.get('api_key')
    model_name = data.get('model_name')
    formula = data.get('formula')
    context = data.get('context')

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        prompt = f"""
        You are the Gemini Core Engine.
        
        INPUTS:
        - Formula: "{formula}"
        - Context: "{context}"
        
        TASKS:
        1. Simulate data (X, Y) logically based on the context.
        2. Generate a Rich Explanation in PERSIAN (Farsi).
           - Use Markdown (headers `###`, bold `**`, lists `-`).
           - Use LaTeX for ALL math symbols enclosed in single dollar signs `$`. 
             Example: "The value of $x^2$ is important."
           - **IMPORTANT**: Do NOT use any HTML tags (like <span> or <div>) inside the JSON. Only Markdown and LaTeX.
        
        OUTPUT FORMAT (Strict JSON):
        {{
            "chart_type": "line", 
            "x_axis_label": "Label X (e.g. Time $t$)",
            "y_axis_label": "Label Y",
            "labels": [1, 2, 3],
            "datasets": [
                {{
                    "label": "Legend Name",
                    "data": [10, 20, 30],
                    "borderColor": "#00d2ff",
                    "borderWidth": 3,
                    "pointRadius": 4,
                    "tension": 0.4
                }}
            ],
            "explanation": "Your Markdown and LaTeX text here."
        }}
        """
        
        response = model.generate_content(prompt)
        result = clean_and_parse_json(response.text)
        
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)