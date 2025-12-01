const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// Add message bubble
function addMessage(text, sender = "bot") {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("message", sender);

  const bubble = document.createElement("div");
  bubble.classList.add("message-content");
  bubble.textContent = text;

  msgDiv.appendChild(bubble);
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Call backend API (our Python app)
async function sendToServer(message) {
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message })
    });

    if (!response.ok) {
      throw new Error("Server error");
    }

    const data = await response.json();
    return data.reply;
  } catch (err) {
    console.error(err);
    return "Oops, something went wrong inside the server. Please try again later.";
  }
}

async function handleUserMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  // Show user message
  addMessage(text, "user");
  userInput.value = "";

  // Show temporary "thinking"
  addMessage("Thinking about your meal... 🤔", "bot");
  const thinkingBubble = chatBox.lastChild;

  // Ask backend
  const reply = await sendToServer(text);

  // Replace thinking bubble
  chatBox.removeChild(thinkingBubble);
  addMessage(reply, "bot");
}

sendBtn.addEventListener("click", handleUserMessage);

userInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleUserMessage();
  }
});
