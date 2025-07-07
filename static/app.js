let currentSession = null;

// DOM elements
const sessionList = document.getElementById('session-list');
const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const newChatBtn = document.getElementById('new-chat');
const summaryBtn = document.getElementById('summary-btn');
const summaryModal = document.getElementById('summary-modal');
const summaryContent = document.getElementById('summary-content');
const closeSummary = document.getElementById('close-summary');
const sessionTitle = document.getElementById('session-title');

// Load sessions and select the first one
async function loadSessions(selectLast = false) {
    const res = await fetch('/sessions');
    const sessions = await res.json();
    sessionList.innerHTML = '';
    sessions.forEach((s, i) => {
        const li = document.createElement('li');
        li.textContent = `Chat ${i + 1}`;
        li.dataset.sessionId = s.session_id;
        if (currentSession === s.session_id) li.classList.add('active');
        li.onclick = () => switchSession(s.session_id);
        // Add delete button
        const delBtn = document.createElement('button');
        delBtn.className = 'delete-chat';
        delBtn.title = 'Delete chat';
        delBtn.innerHTML = '🗑️';
        delBtn.onclick = (e) => {
            e.stopPropagation();
            deleteSession(s.session_id);
        };
        li.appendChild(delBtn);
        sessionList.appendChild(li);
    });
    if (sessions.length > 0 && (!currentSession || selectLast)) {
        switchSession(sessions[sessions.length - 1].session_id);
    }
}

async function deleteSession(sessionId) {
    await fetch(`/sessions/${sessionId}`, { method: 'DELETE' });
    // If the deleted session was current, clear chat and switch
    if (currentSession === sessionId) {
        currentSession = null;
        chatWindow.innerHTML = '';
        sessionTitle.textContent = '';
    }
    await loadSessions();
}

// Switch to a session and load its history
async function switchSession(sessionId) {
    currentSession = sessionId;
    Array.from(sessionList.children).forEach(li => {
        li.classList.toggle('active', li.dataset.sessionId === sessionId);
    });
    sessionTitle.textContent = `Session: ${sessionId.slice(0, 8)}`;
    // Load chat history
    const res = await fetch('/sessions');
    const sessions = await res.json();
    const session = sessions.find(s => s.session_id === sessionId);
    if (!session) return;
    // Get full history from backend
    const histRes = await fetch('/sessions');
    const allSessions = await histRes.json();
    const idx = allSessions.findIndex(s => s.session_id === sessionId);
    if (idx === -1) return;
    // For demo, we keep history in memory on backend
    const hist = await fetch(`/summary/${sessionId}`);
    // But we want the full messages, not just summary
    // So we fetch from a hidden endpoint (or add to /sessions if needed)
    // For now, let's just keep a local cache
    // Instead, let's fetch the full session from the backend
    const full = await fetch(`/sessions`);
    // We'll need to add a /session/<id> endpoint for real use
    // For now, just reload the page to get the latest
    await loadChatHistory();
}

// Load chat history for the current session
async function loadChatHistory() {
    if (!currentSession) return;
    // Fetch the full history from the backend
    const res = await fetch(`/sessions/${currentSession}/history`);
    const history = await res.json();
    chatWindow.innerHTML = '';
    if (Array.isArray(history)) {
        history.forEach(entry => {
            addMessage(entry.message, 'user');
            addMessage(entry.response, 'bot');
        });
    }
    scrollChatToBottom();
}

// Start a new chat session
newChatBtn.onclick = async () => {
    await fetch('/sessions', { method: 'POST' });
    await loadSessions(true);
};

// Send a message
chatForm.onsubmit = async (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message || !currentSession) return;
    addMessage(message, 'user');
    chatInput.value = '';
    chatInput.disabled = true;
    // Send to backend
    const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: currentSession })
    });
    const data = await res.json();
    if (data.response) {
        addMessage(data.response, 'bot');
    } else {
        addMessage('Error: ' + (data.error || 'Unknown error'), 'bot');
    }
    chatInput.disabled = false;
    chatInput.focus();
    scrollChatToBottom();
};

// Add a message to the chat window
function addMessage(text, who) {
    const div = document.createElement('div');
    div.className = 'bubble ' + who;
    div.innerHTML = text;
    chatWindow.appendChild(div);
    scrollChatToBottom();
}

function scrollChatToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Show summary modal
summaryBtn.onclick = async () => {
    if (!currentSession) return;
    const res = await fetch(`/summary/${currentSession}`);
    const data = await res.json();
    summaryContent.textContent = JSON.stringify(data, null, 2);
    summaryModal.style.display = 'flex';
};
closeSummary.onclick = () => {
    summaryModal.style.display = 'none';
};

// Initial load
loadSessions(); 