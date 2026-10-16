const form = document.getElementById('complaintForm');
const resultElement = document.getElementById('result');

let mediaRecorder;
let audioChunks = [];

function sendWithLocation(formData, successMessage) {
    resultElement.textContent = "Fetching location and processing...";

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                formData.append('latitude', position.coords.latitude);
                formData.append('longitude', position.coords.longitude);
                await postToServer(formData, successMessage);
            },
            async (error) => {
                console.warn("Location permission denied or unavailable:", error.message);
                formData.append('latitude', 'Unknown');
                formData.append('longitude', 'Unknown');
                await postToServer(formData, successMessage);
            }
        );
    } else {
        formData.append('latitude', 'Unknown');
        formData.append('longitude', 'Unknown');
        postToServer(formData, successMessage);
    }
}

async function postToServer(formData, successMessage) {
    try {
        resultElement.textContent = successMessage;
        const response = await fetch('/complaint', {
            method: 'POST',
            body: formData
        });

        
        const textResponse = await response.text();
        let result;
        try {
            result = JSON.parse(textResponse);
        } catch (e) {
            
            console.error("Server HTML Error Response:", textResponse);
            resultElement.textContent = `Server Error (${response.status}): Check Render logs.`;
            return;
        }

        if (!response.ok) {
            resultElement.textContent = result.result || "Error processing request.";
            return;
        }

        
        resultElement.innerHTML = `
            <div>${result.result}</div>
            <br>
            <a href="/view-complaints" style="color: #ffe66d; font-weight: bold; text-decoration: underline;">
                📊 View Complaints Dashboard & Send to Official →
            </a>
        `;
    } catch (err) {
        console.error("Network or script error:", err);
        resultElement.textContent = "Error communicating with server.";
    }
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const complaintText = document.getElementById('complaintInput').value;

    const formData = new FormData();
    formData.append('complaint', complaintText);

    sendWithLocation(formData, "Processing text complaint with AI...");
});

const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');

if (recordBtn && stopBtn) {
    recordBtn.addEventListener('click', async () => {
        audioChunks = [];
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio', audioBlob, 'voice_complaint.webm');

                sendWithLocation(formData, "Processing voice recording with AI...");
            };

            mediaRecorder.start();
            recordBtn.disabled = true;
            stopBtn.disabled = false;
            resultElement.textContent = "Recording voice... Speak now.";
        } catch (err) {
            console.error("Microphone access denied or not supported:", err);
            resultElement.textContent = "Could not access microphone.";
        }
    });

    stopBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        recordBtn.disabled = false;
        stopBtn.disabled = true;
    });
}