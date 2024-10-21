// static/script.js

document.getElementById('send-button').addEventListener('click', function() {
    const userInput = document.getElementById('user-input').value;
    if (userInput) {
        addMessage('You: ' + userInput);
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userInput })
        })
        .then(response => response.json())
        .then(data => {
            if (data.response) {
                addMessage('Bot: ' + data.response);
            } else {
                addMessage('Bot: ' + data.error);
            }
        });
        document.getElementById('user-input').value = '';
    }
});

function addMessage(message) {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML += '<div>' + message + '</div>';
    messagesDiv.scrollTop = messagesDiv.scrollHeight; // Scroll to the bottom
}

