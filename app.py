import os
from flask import Flask, request, jsonify, render_template_string
from google import genai
from google.genai import types

app = Flask(__name__)

# Initialize Gemini Client securely
project_id = os.environ.get("PROJECT_ID")
client = genai.Client(http_options={'project': project_id})

auditor_persona = """
You are an expert Sustainability Auditor for the 'Carbon on the Chain' ecosystem. 
Your job is to verify corporate carbon emissions and validate eligibility for ERC-721 carbon credit certificates.
Be concise, professional, and focus on compliance.
"""

# HTML interface for the Judges
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Carbon Auditor AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 40px; display: flex; justify-content: center; }
        .chat-container { background: rgba(30,41,59,0.8); width: 100%; max-width: 600px; padding: 25px; border-radius: 16px; border: 1px solid #334155; box-shadow: 0 0 30px rgba(34, 211, 238, 0.1); }
        h2 { color: #22d3ee; margin-top: 0; display: flex; align-items: center; gap: 10px; }
        .chat-box { height: 400px; overflow-y: auto; background: #0b1120; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #1e293b; }
        .message { margin-bottom: 12px; padding: 10px 14px; border-radius: 10px; max-width: 85%; line-height: 1.4; }
        .user-msg { background: #334155; margin-left: auto; color: white; }
        .ai-msg { background: rgba(34, 211, 238, 0.1); color: #a5f3fc; border-left: 3px solid #22d3ee; }
        .input-area { display: flex; gap: 10px; }
        input { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #0b1120; color: white; outline: none; }
        button { padding: 12px 20px; border-radius: 8px; border: none; background: linear-gradient(135deg, #22d3ee, #4ade80); color: black; font-weight: 600; cursor: pointer; transition: 0.2s; }
        button:hover { transform: scale(1.05); }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>🤖 AI Carbon Auditor</h2>
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Hello! I am your AI Auditor. How can I assist you with emission verification today?</div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Ask about an organization's emissions..." onkeypress="if(event.key === 'Enter') sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const inputField = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const userText = inputField.value.trim();
            if (!userText) return;

            // Add user message
            chatBox.innerHTML += `<div class="message user-msg">${userText}</div>`;
            inputField.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            // Call Python backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: userText })
            });
            const data = await response.json();

            // Add AI message
            chatBox.innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    user_prompt = request.json.get('prompt', '')
    
    try:
        response = client.models.generate_content(
            model='gemini-3.1-pro',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=auditor_persona,
                temperature=0.2,
            )
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": f"Error communicating with AI: {str(e)}"})

if __name__ == '__main__':
    # This checks for Cloud Run's port, but defaults to YOUR port 5777 locally!
    port = int(os.environ.get('PORT', 5777))
    app.run(host='0.0.0.0', port=port)