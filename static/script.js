let currentQuestionIndex = 0;
let score = 0;
let answered = false;

const questionElement = document.getElementById("question");
const answerContainer = document.getElementById("answer-container");
const explanationElement = document.getElementById("explanation");
const scoreElement = document.getElementById("score");
const nextQuestionButton = document.getElementById("next-question");

function displayQuestion() {
    answered = false;
    fetch(`/get_question/${currentQuestionIndex}`)
        .then(response => response.json())
        .then(question => {
            if (question.error) {
                nextQuestionButton.textContent = "Submit";
                nextQuestionButton.style.display = "block";
                nextQuestionButton.addEventListener("click", () => {
                    window.location.href = `/result?score=${score}`;
                });
                return;
            }
            questionElement.textContent = question.question;
            answerContainer.innerHTML = "";
            question.answers.forEach((answer, index) => {
                const button = document.createElement("button");
                button.classList.add("answer-btn");
                button.textContent = answer;
                button.addEventListener("click", () => checkAnswer(index));
                answerContainer.appendChild(button);
            });
            explanationElement.textContent = "";
            nextQuestionButton.style.display = "none";
        });
}

function checkAnswer(selectedAnswer) {
    if (answered) {
        return;
    }
    answered = true;

    const buttons = answerContainer.querySelectorAll(".answer-btn");

    fetch("/check_answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ questionIndex: currentQuestionIndex, selectedAnswer: selectedAnswer })
    })
        .then(response => response.json())
        .then(data => {
            buttons.forEach((button, index) => {
                if (index === data.correctAnswer) {
                    button.classList.add("correct");
                } else if (index === selectedAnswer) {
                    button.classList.add("incorrect");
                }
                button.disabled = true;
            });

            if (data.isCorrect) {
                score++;
            }
            explanationElement.textContent = (data.isCorrect ? "Correct! " : "Incorrect! The correct answer was " + buttons[data.correctAnswer].textContent + ". ") + data.explanation;
            scoreElement.textContent = "Score: " + score;
            nextQuestionButton.style.display = "block";
        });
}

nextQuestionButton.addEventListener("click", () => {
    currentQuestionIndex++;
    displayQuestion();
});

displayQuestion();
