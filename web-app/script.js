const messageContainer = document.getElementById('messageContainer');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');

let isProcessing = false;

sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    if (isProcessing) return;
    
    const userMessage = userInput.value.trim();
    if (userMessage) {
        isProcessing = true;
        sendButton.disabled = true;
        
        appendMessage('user', userMessage);
        userInput.value = '';

        const botMessageElement = appendMessage('bot', '');

        try {
            const response = await fetch('https://1oxv8ue0g4.execute-api.us-east-2.amazonaws.com/dev/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ input: userMessage })
            });

            if (response.ok) {
                const data = await response.json();
                const botMessage = data.body ? JSON.parse(data.body).Answer : 'No response received';
                botMessageElement.textContent = botMessage;
            } else {
                throw new Error('Error occurred while fetching the response from the API');
            }
        } catch (error) {
            botMessageElement.textContent = 'An error occurred: ' + error.message;
        } finally {
            isProcessing = false;
            sendButton.disabled = false;
        }
    }
}

function appendMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    const textElement = document.createElement('div');
    textElement.classList.add('text');
    textElement.textContent = message;
    messageElement.appendChild(textElement);

    messageContainer.appendChild(messageElement);
    messageContainer.scrollTop = messageContainer.scrollHeight;

    return textElement;
}