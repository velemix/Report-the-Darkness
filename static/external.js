const form = document.getElementById('complaintForm');
const resultElement = document.getElementById('result');

let mediaRecorder;
let audioChunks = [];

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const complaint = document.getElementById('complaintInput').value;

    resultElement.textContent = "Processing text complaint...";

    const response = await fetch('/complaint', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ complaint })
    });

    const result = await response.json();
    resultElement.textContent = result.result;
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
                resultElement.textContent = "Processing voice recording with AI...";
                
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio', audioBlob, 'voice_complaint.webm');

                const response = await fetch('/complaint', {
                    method: 'POST',
                    body: formData 
                });

                const result = await response.json();
                resultElement.textContent = result.result;
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