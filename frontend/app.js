/* =====================================================
   API CONFIG
===================================================== */

const API_URL = "http://127.0.0.1:8000/chat";


/* =====================================================
   DOM ELEMENTS
===================================================== */

const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const chatBox = document.getElementById("chatBox");
const sendButton = document.getElementById("sendButton");


/* =====================================================
   MARKDOWN CONFIG
===================================================== */

if (typeof marked !== "undefined") {

    marked.setOptions({
        gfm: true,
        breaks: true
    });

}


/* =====================================================
   FORMAT AI RESPONSE
===================================================== */

function formatAnswer(text) {

    if (!text) {
        return "I don't have enough information to answer that.";
    }

    if (
        typeof marked === "undefined" ||
        typeof DOMPurify === "undefined"
    ) {
        return escapeHtml(text).replace(/\n/g, "<br>");
    }

    const html = marked.parse(text);

    return DOMPurify.sanitize(html);
}


/* =====================================================
   ESCAPE USER TEXT
===================================================== */

function escapeHtml(text) {

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


/* =====================================================
   ADD MESSAGE
===================================================== */

function addMessage(type, content, isMarkdown = false) {

    const message = document.createElement("div");

    message.className = `message ${type}`;

    const messageContent = document.createElement("div");

    messageContent.className = "message-content";


    if (isMarkdown) {

        messageContent.innerHTML = formatAnswer(content);

    } else {

        messageContent.innerHTML = escapeHtml(content);

    }


    message.appendChild(messageContent);

    chatBox.appendChild(message);


    /*
        Scroll to latest message
    */

    chatBox.scrollTop = chatBox.scrollHeight;


    return message;
}


/* =====================================================
   LOADING MESSAGE
===================================================== */

function addLoadingMessage() {

    const message = document.createElement("div");

    message.className = "message ai";

    message.innerHTML = `
        <div class="message-content">
            <span class="loading-text">
                Thinking...
            </span>
        </div>
    `;

    chatBox.appendChild(message);

    chatBox.scrollTop = chatBox.scrollHeight;

    return message;
}


/* =====================================================
   SEND QUESTION
===================================================== */

chatForm.addEventListener("submit", async (event) => {

    event.preventDefault();


    const question = questionInput.value.trim();


    if (!question) {
        return;
    }


    /*
        Add user message
    */

    addMessage(
        "user",
        question,
        false
    );


    /*
        Clear input
    */

    questionInput.value = "";


    /*
        Disable button
    */

    sendButton.disabled = true;

    sendButton.textContent = "...";


    /*
        Show loading
    */

    const loadingMessage = addLoadingMessage();


    try {

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })

        });


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data = await response.json();


        /*
            Remove loading message
        */

        loadingMessage.remove();


        /*
            Backend response
        */

        const answer =
            data.answer ||
            data.response ||
            "I don't have enough information to answer that.";


        /*
            Add AI response
        */

        addMessage(
            "ai",
            answer,
            true
        );


    } catch (error) {

        console.error("Chat error:", error);


        loadingMessage.remove();


        addMessage(
            "ai",
            "Sorry, I couldn't connect to the AI backend. Please make sure the FastAPI server is running.",
            false
        );

    } finally {

        sendButton.disabled = false;

        sendButton.textContent = "Send";

        questionInput.focus();

    }

});


/* =====================================================
   GSAP
===================================================== */

window.addEventListener("load", () => {

    if (typeof gsap === "undefined") {
        return;
    }


    /*
        Hero animation
    */

    gsap.from(".hero-content > *", {

        opacity: 0,

        y: 20,

        duration: 0.7,

        stagger: 0.08,

        ease: "power2.out"

    });


    gsap.from(".hero-terminal", {

        opacity: 0,

        x: 30,

        duration: 0.8,

        delay: 0.2,

        ease: "power2.out"

    });


    /*
        Navbar
    */

    gsap.from(".navbar", {

        y: -20,

        opacity: 0,

        duration: 0.5,

        ease: "power2.out"

    });

});

