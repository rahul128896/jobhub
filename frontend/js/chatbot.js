(function initChatbot() {
    const chatToggle = document.getElementById('chatbot-toggle');
    const chatWindow = document.getElementById('chatbot-window');
    const chatClose = document.getElementById('chatbot-close');
    const chatMessages = document.getElementById('chatbot-messages');
    const chatInput = document.getElementById('chatbot-input');
    const chatSend = document.getElementById('chatbot-send');

    if (!chatToggle || !chatWindow) return;

    chatToggle.addEventListener('click', () => {
        chatWindow.classList.toggle('open');
        if (chatWindow.classList.contains('open')) {
            chatInput.focus();
            if (chatMessages.children.length === 0) {
                appendMessage('bot', "Hi! I'm your AI Career Assistant. How can I help you today?");
            }
        }
    });

    chatClose.addEventListener('click', () => {
        chatWindow.classList.remove('open');
    });

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    chatSend.addEventListener('click', handleSend);

    chatInput.addEventListener('input', () => {
        chatSend.disabled = chatInput.value.trim().length === 0;
    });

    async function handleSend() {
        const message = chatInput.value.trim();
        if (!message) return;

        appendMessage('user', message);
        chatInput.value = '';
        chatSend.disabled = true;

        const typingId = showTypingIndicator();

        try {
            // Using absolute /api/chat path for all pages dynamically loaded from component logic
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            const data = await res.json();
            
            removeTypingIndicator(typingId);

            if (data.reply) {
                appendMessage('bot', data.reply);
            } else if (data.error) {
                appendMessage('bot', data.error);
            } else {
                appendMessage('bot', 'Sorry, I did not understand that.');
            }
        } catch (err) {
            removeTypingIndicator(typingId);
            appendMessage('bot', 'Network error. Please try again.');
        }
        
        chatSend.disabled = chatInput.value.trim().length === 0;
    }

    function appendMessage(sender, text) {
        const div = document.createElement('div');
        div.className = `chat-bubble ${sender}`;
        div.textContent = text;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const div = document.createElement('div');
        div.className = 'chat-bubble bot';
        div.id = id;
        div.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
})();
