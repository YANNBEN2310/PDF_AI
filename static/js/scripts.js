function checkEnter(event) {
    if (event.keyCode === 13) {
        sendMessage();
    }
}

function sendMessage() {
    const userInput = document.getElementById('userInput').value;
    if (userInput.trim() === "") return;

    addMessage(userInput, 'user');

    document.getElementById('loader').style.display = 'block';

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: userInput, pdf_path: pdfPath })
    })
    .then(response => response.json())
    .then(data => {
        addMessage(data.answer, 'bot');
        document.getElementById('loader').style.display = 'none';
    })
    .catch(error => {
        addMessage("Error: " + error, 'bot');
        document.getElementById('loader').style.display = 'none';
    });

    document.getElementById('userInput').value = "";
}

function addMessage(text, sender) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender);
    messageDiv.innerText = text;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
