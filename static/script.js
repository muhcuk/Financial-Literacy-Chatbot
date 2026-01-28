document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const userMessage = chatInput.value.trim();
        if (!userMessage) return;

        addMessage(userMessage, "user");
        chatInput.value = "";

        const botMessageContainer = addMessage("", "bot");
        const botParagraph = botMessageContainer.querySelector('p');
        
        try {
            const response = await fetch("/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage }),
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let streaming = true;

            while (streaming) {
                const { value, done } = await reader.read();
                if (done) {
                    streaming = false;
                    break;
                }
                const chunk = decoder.decode(value);
                botParagraph.textContent += chunk;
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        } catch (error) {
            botParagraph.textContent = "Sorry, an error occurred.";
            console.error("Error fetching response:", error);
        }
    });

    function addMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}`;
        const paragraph = document.createElement("p");
        paragraph.textContent = text;
        messageDiv.appendChild(paragraph);
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageDiv;
    }
});