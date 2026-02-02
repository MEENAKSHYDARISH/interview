/**
 * Interview Application Logic
 * Handles Media, Speech Recognition, Synthesis, and API communication.
 */

class SpeechManager {
    constructor(onSpeechResult, onSpeechEnd, onVoiceStart, onVoiceEnd) {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.onSpeechResult = onSpeechResult;
        this.onSpeechEnd = onSpeechEnd; // When user stops speaking and we have final text
        this.onVoiceStart = onVoiceStart; // AI starts speaking
        this.onVoiceEnd = onVoiceEnd; // AI stops speaking
        this.isListening = false;
        this.finalTranscript = '';

        this._initRecognition();
    }

    _initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Your browser does not support Speech Recognition. Please use Chrome or Edge.");
            return;
        }
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false; // We want turn-based
        this.recognition.lang = 'en-US';
        this.recognition.interimResults = true;

        this.recognition.onstart = () => {
            this.isListening = true;
            console.log('Voice recognition activated.');
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    this.finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            // Update UI with interim
            if (this.onSpeechResult) this.onSpeechResult(this.finalTranscript + interimTranscript, false);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            console.log('Voice recognition ended.');
            // Determine if we should process or restart
            // If we have text, trigger callback
            if (this.finalTranscript.trim().length > 0) {
                if (this.onSpeechEnd) this.onSpeechEnd(this.finalTranscript.trim());
                this.finalTranscript = ''; // Reset
            } else {
                // Restart if logic requires continuous listening (handled by controller)
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
        };
    }

    startListening() {
        if (this.isListening) return;
        this.finalTranscript = '';
        try {
            this.recognition.start();
        } catch (e) {
            console.error("Recognition start failed", e);
        }
    }

    stopListening() {
        if (this.recognition) this.recognition.stop();
    }

    speak(text) {
        if (this.synthesis.speaking) {
            console.warn("Already speaking. Cancelling.");
            this.synthesis.cancel();
        }

        const utterThis = new SpeechSynthesisUtterance(text);
        utterThis.onstart = () => {
            if (this.onVoiceStart) this.onVoiceStart();
        };
        utterThis.onend = () => {
            if (this.onVoiceEnd) this.onVoiceEnd();
        };
        utterThis.onerror = (e) => {
            console.error("Speech synthesis error", e);
            if (this.onVoiceEnd) this.onVoiceEnd();
        };

        // Pick a nice voice if available
        const voices = this.synthesis.getVoices();
        // Prefer a female/Google voice if available for clarity
        const preferredVoice = voices.find(v => v.name.includes("Google US English") || v.name.includes("Samantha"));
        if (preferredVoice) utterThis.voice = preferredVoice;

        this.synthesis.speak(utterThis);
    }
}

class InterviewController {
    constructor() {
        this.ui = {
            startBtn: document.getElementById('startBtn'),
            finishBtn: document.getElementById('finishBtn'),
            overlay: document.getElementById('startOverlay'),
            userVideo: document.getElementById('userVideo'),
            avatar: document.getElementById('avatarVisualizer'),
            aiCaption: document.getElementById('aiCaption'),
            userCaption: document.getElementById('userCaption'),
            roleBadge: document.getElementById('roleBadge'),
            statusBadge: document.getElementById('statusBadge'),
            aiStatus: document.getElementById('aiStatus')
        };

        // Load config from sessionStorage if available (from Select Page)
        const storedConfig = sessionStorage.getItem('interviewConfig');
        const config = storedConfig ? JSON.parse(storedConfig) : {};

        this.apiState = {
            role: config.role || new URLSearchParams(window.location.search).get('role') || 'Software Engineer',
            type: config.type || new URLSearchParams(window.location.search).get('type') || 'Technical',
            resumeText: config.resumeText || "No resume provided.",
            conversationActive: false
        };

        this.speechManager = new SpeechManager(
            (text, final) => this.updateUserCaption(text), // onResult
            (text) => this.handleUserAnswer(text),          // onEnd (Process answer)
            () => this.setAvatarState('speaking'),          // onVoiceStart
            () => this.setAvatarState('listening')          // onVoiceEnd
        );

        this.init();
    }

    init() {
        this.ui.roleBadge.textContent = `Role: ${this.apiState.role}`;

        this.ui.startBtn.addEventListener('click', () => this.startInterview());
        this.ui.finishBtn.addEventListener('click', () => this.endInterview());

        // Pre-load voices
        window.speechSynthesis.getVoices();
    }

    async startInterview() {
        // 1. Get Camera
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            this.ui.userVideo.srcObject = stream;
        } catch (e) {
            alert("Camera/Mic access is required.");
            return;
        }

        // 2. Hide Overlay
        this.ui.overlay.style.opacity = '0';
        setTimeout(() => this.ui.overlay.style.display = 'none', 500);
        this.ui.finishBtn.disabled = false;

        // 3. Start API Session
        this.setStage('processing');
        this.updateAiCaption("Initializing interview component...", true);

        try {
            const res = await fetch('/api/interview/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    role: this.apiState.role,
                    difficulty: 'Medium',
                    resume_text: this.apiState.resumeText
                })
            });
            const data = await res.json();

            this.aiQueue = data; // { "question": "..." }
            this.playAiResponse(data);

        } catch (e) {
            console.error("API Error", e);
            this.updateAiCaption("Error connecting to server.");
        }
    }

    playAiResponse(data) {
        // Feedback first?
        const fullText = (data.feedback ? data.feedback + " " : "") + data.question;

        this.updateAiCaption(data.question);
        this.speechManager.speak(fullText);
    }

    setAvatarState(state) {
        // state: 'idle', 'speaking', 'listening', 'processing'
        const { avatar, statusBadge, aiStatus } = this.ui;

        avatar.classList.remove('speaking');
        statusBadge.className = 'badge';

        if (state === 'speaking') {
            avatar.classList.add('speaking');
            statusBadge.classList.add('status-speaking');
            statusBadge.textContent = "AI Speaking";
            aiStatus.textContent = "AI is asking...";
        } else if (state === 'listening') {
            statusBadge.classList.add('status-listening');
            statusBadge.textContent = "Listening...";
            aiStatus.textContent = "Your turn";

            // Trigger listening automatically after AI finishes
            this.speechManager.startListening();
        } else if (state === 'processing') {
            statusBadge.classList.add('status-processing');
            statusBadge.textContent = "Thinking...";
            aiStatus.textContent = "AI is thinking...";
        }
    }

    updateUserCaption(text) {
        this.ui.userCaption.textContent = text;
        this.ui.userCaption.classList.add('visible');
    }

    updateAiCaption(text, visible = true) {
        this.ui.aiCaption.textContent = text;
        if (visible) this.ui.aiCaption.classList.add('visible');
    }

    async handleUserAnswer(text) {
        console.log("User Answer:", text);
        this.setStage('processing');

        // Send to API
        try {
            const res = await fetch('/api/interview/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer: text })
            });
            const data = await res.json();
            this.playAiResponse(data);
        } catch (e) {
            console.error("API Error", e);
        }
    }

    setStage(stage) {
        this.setAvatarState(stage);
    }

    async endInterview() {
        if (confirm("Are you sure you want to end the interview?")) {
            this.speechManager.stopListening();
            this.speechManager.synthesis.cancel();

            this.updateAiCaption("Generating Performance Report...", true);
            this.setStage('processing');

            try {
                const res = await fetch('/api/interview/end', { method: 'POST' });
                const data = await res.json();

                if (data.status === 'success') {
                    window.location.href = data.redirect_url;
                } else {
                    alert("Error generating report: " + (data.error || "Unknown"));
                    window.location.href = '/report';
                }
            } catch (e) {
                console.error("End Interview Error", e);
                window.location.href = '/report';
            }
        }
    }
}

// Start
document.addEventListener('DOMContentLoaded', () => {
    new InterviewController();
});
