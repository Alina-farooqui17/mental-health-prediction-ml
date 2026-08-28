const predictionForm = document.getElementById("predictionForm");
const loadingSection = document.getElementById("loadingSection");
const resultSection = document.getElementById("resultSection");
const mentalHealthScore = document.getElementById("mentalHealthScore");
const summaryText = document.getElementById("summaryText");
const loweringFactors = document.getElementById("loweringFactors");
const increasingFactors = document.getElementById("increasingFactors");
const predictButton = document.getElementById("predictButton");
const buttonText = document.getElementById("buttonText");

const chatButton = document.getElementById("chatButton");
const chatWindow = document.getElementById("chatWindow");
const closeChat = document.getElementById("closeChat");
const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendChatButton = document.getElementById("sendChatButton");

const PREDICT_API_URL = "http://127.0.0.1:8000/predict";
const CHAT_API_URL = "http://127.0.0.1:8000/chat";

let latestPrediction = null;

console.log("Solviera JavaScript loaded successfully!");

predictionForm.addEventListener("submit", async function (event) {
event.preventDefault();


console.log("Prediction form submitted!");

const formData = {
    Age: parseFloat(document.getElementById("Age").value),
    Gender: document.getElementById("Gender").value,
    Most_Used_Platform: document.getElementById("Most_Used_Platform").value,
    grouped_countries: document.getElementById("grouped_countries").value,
    Purpose_Of_Use: document.getElementById("Purpose_Of_Use").value,
    Academic_Level: document.getElementById("Academic_Level").value,

    Avg_Daily_Usage_Hours: parseFloat(
        document.getElementById("Avg_Daily_Usage_Hours").value
    ),

    Daily_Unlocks: parseFloat(
        document.getElementById("Daily_Unlocks").value
    ),

    Study_Hours: parseFloat(
        document.getElementById("Study_Hours").value
    ),

    Physical_Activity_Hours: parseFloat(
        document.getElementById("Physical_Activity_Hours").value
    ),

    Sleep_Hours_Per_Night: parseFloat(
        document.getElementById("Sleep_Hours_Per_Night").value
    ),

    Stress_Level: document.getElementById("Stress_Level").value
};

console.log("Sending prediction data:", formData);

resultSection.classList.add("hidden");
loadingSection.classList.remove("hidden");

loadingSection.scrollIntoView({
    behavior: "smooth"
});

predictButton.disabled = true;
buttonText.textContent = "Analyzing...";

try {
    const response = await fetch(
        PREDICT_API_URL,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(formData)
        }
    );

    console.log(
        "Prediction API status:",
        response.status
    );

    if (!response.ok) {
        let errorMessage = "Prediction failed.";

        try {
            const errorData = await response.json();

            errorMessage =
                errorData.detail ||
                JSON.stringify(errorData);

        } catch (jsonError) {
            errorMessage =
                "Server error: " + response.status;
        }

        throw new Error(errorMessage);
    }

    const result = await response.json();

    console.log("Prediction result:", result);

    latestPrediction = result;

    displayResults(result);

} catch (error) {
    console.error("Prediction error:", error);

    alert(
        "Unable to get prediction.\n\nError: " +
        error.message
    );

} finally {
    loadingSection.classList.add("hidden");

    predictButton.disabled = false;

    buttonText.textContent =
        "Analyze My Mental Wellness";
}


});

function displayResults(result) {


resultSection.classList.remove("hidden");

animateScore(
    Number(result.predicted_mental_health_score)
);

summaryText.textContent =
    result.summary ||
    "Your AI analysis has been completed.";

loweringFactors.innerHTML = "";
increasingFactors.innerHTML = "";

if (Array.isArray(result.factors_lowering_prediction)) {

    result.factors_lowering_prediction.forEach(
        function (factor) {

            const recommendationHTML =
                factor.recommendation
                    ? "<p class=\"factor-recommendation\">💡 " +
                      factor.recommendation +
                      "</p>"
                    : "";

            const factorHTML =
                "<div class=\"factor-item\">" +

                "<div class=\"factor-top\">" +

                "<span class=\"factor-name\">" +
                factor.factor +
                "</span>" +

                "<strong class=\"negative-impact\">" +
                Number(factor.impact).toFixed(4) +
                "</strong>" +

                "</div>" +

                "<p class=\"factor-description\">" +
                (factor.explanation || "") +
                "</p>" +

                recommendationHTML +

                "</div>";

            loweringFactors.insertAdjacentHTML(
                "beforeend",
                factorHTML
            );

        }
    );
}

if (Array.isArray(result.factors_increasing_prediction)) {

    result.factors_increasing_prediction.forEach(
        function (factor) {

            const factorHTML =
                "<div class=\"factor-item\">" +

                "<div class=\"factor-top\">" +

                "<span class=\"factor-name\">" +
                factor.factor +
                "</span>" +

                "<strong class=\"positive-impact\">" +
                "+" +
                Number(factor.impact).toFixed(4) +
                "</strong>" +

                "</div>" +

                "<p class=\"factor-description\">" +
                (factor.explanation || "") +
                "</p>" +

                "</div>";

            increasingFactors.insertAdjacentHTML(
                "beforeend",
                factorHTML
            );

        }
    );
}

setTimeout(function () {

    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}, 200);


}

function animateScore(finalScore) {


if (!Number.isFinite(finalScore)) {
    mentalHealthScore.textContent = "0.00";
    return;
}

let currentScore = 0;

const duration = 1200;
const intervalTime = 20;

const totalSteps =
    duration / intervalTime;

const increment =
    finalScore / totalSteps;

const animation = setInterval(
    function () {

        currentScore += increment;

        if (currentScore >= finalScore) {
            currentScore = finalScore;
            clearInterval(animation);
        }

        mentalHealthScore.textContent =
            currentScore.toFixed(2);

    },
    intervalTime
);


}

function startNewAnalysis() {


resultSection.classList.add("hidden");

predictionForm.scrollIntoView({
    behavior: "smooth",
    block: "start"
});


}

chatButton.addEventListener(
"click",
function () {


    chatWindow.classList.toggle("chat-open");

    if (
        chatWindow.classList.contains("chat-open")
    ) {
        chatInput.focus();
    }

}


);

closeChat.addEventListener(
"click",
function () {


    chatWindow.classList.remove("chat-open");

}


);

async function sendChatMessage() {


const message =
    chatInput.value.trim();

if (!message) {
    return;
}

addMessage(message, "user");

chatInput.value = "";

chatInput.disabled = true;
sendChatButton.disabled = true;

showTypingIndicator();

try {

    const response = await fetch(
        CHAT_API_URL,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message,
                prediction_context: latestPrediction
            })
        }
    );

    removeTypingIndicator();

    if (!response.ok) {

        let errorMessage =
            "Chatbot request failed.";

        try {

            const errorData =
                await response.json();

            errorMessage =
                errorData.detail ||
                JSON.stringify(errorData);

        } catch (jsonError) {

            errorMessage =
                "Server error: " + response.status;
        }

        throw new Error(errorMessage);
    }

    const result =
        await response.json();

    addMessage(
        result.response ||
        "I couldn't generate a response.",
        "bot"
    );

} catch (error) {

    console.error(
        "Chat error:",
        error
    );

    removeTypingIndicator();

    addMessage(
        "Sorry, I couldn't connect to Solviera right now. Please make sure the FastAPI server and Ollama are running.",
        "bot error"
    );

} finally {

    chatInput.disabled = false;
    sendChatButton.disabled = false;

    chatInput.focus();
}


}

sendChatButton.addEventListener(
"click",
sendChatMessage
);

chatInput.addEventListener(
"keydown",
function (event) {


    if (event.key === "Enter") {

        event.preventDefault();

        sendChatMessage();
    }

}


);

function addMessage(message, type) {


const messageElement =
    document.createElement("div");

messageElement.className =
    "chat-message " + type;

messageElement.textContent =
    message;

chatMessages.appendChild(
    messageElement
);

scrollChatToBottom();


}

function showTypingIndicator() {


removeTypingIndicator();

const typingElement =
    document.createElement("div");

typingElement.id =
    "typingIndicator";

typingElement.className =
    "chat-message bot typing";

typingElement.innerHTML =
    "<span></span>" +
    "<span></span>" +
    "<span></span>";

chatMessages.appendChild(
    typingElement
);

scrollChatToBottom();


}

function removeTypingIndicator() {


const typingIndicator =
    document.getElementById(
        "typingIndicator"
    );

if (typingIndicator) {
    typingIndicator.remove();
}


}

function scrollChatToBottom() {


chatMessages.scrollTo({
    top: chatMessages.scrollHeight,
    behavior: "smooth"
});


}

document.querySelectorAll(
".predict-btn, .chat-button"
).forEach(function (button) {


button.addEventListener(
    "click",
    function (event) {

        const ripple =
            document.createElement("span");

        ripple.classList.add("ripple");

        const rect =
            button.getBoundingClientRect();

        const size =
            Math.max(
                button.offsetWidth,
                button.offsetHeight
            );

        ripple.style.width =
            size + "px";

        ripple.style.height =
            size + "px";

        ripple.style.left =
            event.clientX -
            rect.left -
            size / 2 +
            "px";

        ripple.style.top =
            event.clientY -
            rect.top -
            size / 2 +
            "px";

        button.appendChild(ripple);

        setTimeout(
            function () {
                ripple.remove();
            },
            700
        );

    }
);


});
