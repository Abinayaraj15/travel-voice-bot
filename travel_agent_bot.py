from flask import Flask, request, jsonify, render_template_string, session
from dotenv import load_dotenv
import os
from openai import OpenAI

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = "super_secret_travel_key"

# -------------------------
# HTML + JavaScript
# -------------------------
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>🌍 Travel Agent Voice Bot</title>
    <style>
        body { font-family: Arial; background: #f4f4f9; margin: 30px; text-align: center; }
        .chatbox { width: 80%; max-width: 600px; margin: auto; text-align: left; }
        .bot, .user { padding: 10px; margin: 10px 0; border-radius: 8px; }
        .bot { background: #e8f0fe; }
        .user { background: #d1ffd6; text-align: right; }
        input { width: 75%; padding: 10px; margin-top: 10px; }
        button { padding: 10px 15px; margin: 5px; border: none; border-radius: 6px; cursor: pointer; }
        #speakBtn { background-color: #007bff; color: white; }
    </style>
</head>
<body>
<div class="chatbox">
    <h2>✈️ Travel Agent Voice Chatbot</h2>
    <div id="chat"></div>
    <input type="text" id="userInput" placeholder="Ask about trips, flights, hotels..." />
    <button onclick="sendMessage()">Send</button>
    <button id="speakBtn" onclick="startListening()">🎤 Speak</button>
</div>

<script>
let recognition;
let listening = false;

// Send typed message
async function sendMessage() {
    const input = document.getElementById('userInput');
    const msg = input.value.trim();
    if (!msg) return;
    addUserMessage(msg);
    input.value = '';
    await sendToServer(msg);
}

// Start voice recognition (auto-stop when user stops speaking)
function startListening() {
    if (!('webkitSpeechRecognition' in window)) {
        alert("❌ Your browser doesn't support voice recognition. Try Chrome!");
        return;
    }

    if (listening) return;

    recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;  // stops when silence detected
    recognition.interimResults = false;

    recognition.onstart = () => {
        listening = true;
        addBotMessage("🎧 Listening...");
    };

    recognition.onresult = async (event) => {
        const transcript = event.results[0][0].transcript;
        addUserMessage(transcript);
        await sendToServer(transcript);
    };

    recognition.onend = () => {
        listening = false; // automatically stops when user stops speaking
    };

    recognition.start();
}

// Send to backend and get AI reply
async function sendToServer(message) {
    const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });
    const data = await res.json();
    addBotMessage(data.reply);
    speakText(data.reply);
}

// Speak AI reply
function speakText(text) {
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'en-US';
    utter.pitch = 1;
    utter.rate = 1;
    window.speechSynthesis.speak(utter);
}

// Display messages
function addUserMessage(msg) {
    document.getElementById('chat').innerHTML += `<div class='user'>🧍‍♀️ You: ${msg}</div>`;
}
function addBotMessage(msg) {
    document.getElementById('chat').innerHTML += `<div class='bot'>🤖 Bot: ${msg}</div>`;
    // auto-scroll to latest message
    window.scrollTo(0, document.body.scrollHeight);
}
</script>
</body>
</html>
"""

# -------------------------
# Flask routes
# -------------------------
@app.route("/")
def index():
    return render_template_string(html_template)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if "history" not in session:
        session["history"] = [{
            "role": "system",
            "content": "You are a friendly travel agent assistant who helps customers plan trips, suggest destinations, book hotels, and answer travel questions clearly and politely."
        }]
    
    session["history"].append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=session["history"]
    )

    bot_reply = response.choices[0].message.content
    session["history"].append({"role": "assistant", "content": bot_reply})
    
    return jsonify({"reply": bot_reply})

# -------------------------
# Run Flask app
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
