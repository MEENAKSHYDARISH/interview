/**
 * Interview Application Logic
 * Handles Media, Speech Recognition, Synthesis, and API communication.
 */

class SpeechManager {
    constructor(onSpeechResult, onSpeechEnd, onVoiceStart, onVoiceEnd, onSpeechError) {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.onSpeechResult = onSpeechResult;
        this.onSpeechEnd = onSpeechEnd; // When user stops speaking and we have final text
        this.onVoiceStart = onVoiceStart; // AI starts speaking
        this.onVoiceEnd = onVoiceEnd; // AI stops speaking
        this.onSpeechError = onSpeechError; // Recognition start/runtime errors
        this.isListening = false;
        this.finalTranscript = '';
        this.interimTranscript = '';
        this._shouldAutoRestart = false;

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
            this.interimTranscript = interimTranscript;
            // Update UI with interim
            if (this.onSpeechResult) this.onSpeechResult((this.finalTranscript + interimTranscript).trim(), false);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            console.log('Voice recognition ended.');
            // Determine if we should process or restart
            // If we have text, trigger callback
            const combined = `${this.finalTranscript} ${this.interimTranscript}`.trim();
            const hasText = combined.length > 0;

            if (hasText) {
                if (this.onSpeechEnd) this.onSpeechEnd(combined);
            } else if (this._shouldAutoRestart) {
                setTimeout(() => this.startListening({ autoRestart: true }), 250);
            }

            this.finalTranscript = '';
            this.interimTranscript = '';
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            if (this.onSpeechError) this.onSpeechError(event.error || 'unknown-error');
            const combined = `${this.finalTranscript} ${this.interimTranscript}`.trim();
            if (combined.length > 0) {
                try {
                    if (this.recognition) this.recognition.stop();
                } catch (_) {}
                if (this.onSpeechEnd) this.onSpeechEnd(combined);
                this.finalTranscript = '';
                this.interimTranscript = '';
                return;
            }

            if (this._shouldAutoRestart && (event.error === 'no-speech' || event.error === 'aborted')) {
                setTimeout(() => this.startListening({ autoRestart: true }), 250);
            }
        };
    }

    startListening({ autoRestart = false } = {}) {
        if (!this.recognition) {
            console.warn("Speech recognition unavailable in this browser/context.");
            if (this.onSpeechError) this.onSpeechError('speech-recognition-unavailable');
            return;
        }
        if (this.isListening) return;
        this.finalTranscript = '';
        this.interimTranscript = '';
        this._shouldAutoRestart = autoRestart;
        try {
            this.recognition.start();
        } catch (e) {
            console.error("Recognition start failed", e);
            // This is commonly thrown if called too quickly, or blocked by browser policy.
            if (this.onSpeechError) this.onSpeechError(e?.name || 'recognition-start-failed');
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
            aiStatus: document.getElementById('aiStatus'),
            micLevel: document.getElementById('micLevel')
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
            () => this.setAvatarState('listening'),         // onVoiceEnd
            (err) => this.handleSpeechError(err)            // onSpeechError
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
        this.setMicLevelText("Mic ready");

        try {
            const res = await fetch('/api/interview/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    role: this.apiState.role,
                    type: this.apiState.type,
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
        // Ensure we enter speaking stage even if TTS events don't fire (autoplay policies can block).
        this.setStage('speaking');
        this.speechManager.speak(fullText);
        // Fallback: if TTS doesn't start/end properly, still begin listening shortly after question shows.
        setTimeout(() => {
            if (!this.speechManager.synthesis.speaking && !this.speechManager.isListening) {
                this.setAvatarState('listening');
            }
        }, 1200);
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
            this.setMicLevelText("Listening…");
            this.speechManager.startListening({ autoRestart: true });
        } else if (state === 'processing') {
            statusBadge.classList.add('status-processing');
            statusBadge.textContent = "Thinking...";
            aiStatus.textContent = "AI is thinking...";
            this.setMicLevelText("—");
        }
    }

    setMicLevelText(text) {
        if (this.ui.micLevel) this.ui.micLevel.textContent = text;
    }

    handleSpeechError(err) {
        // Surface common recognition issues in the UI so it's debuggable without devtools.
        const msg = `Mic error: ${err}`;
        console.warn(msg);
        this.setMicLevelText(msg);
        this.ui.aiStatus.textContent = "Microphone issue";
        // If recognition was blocked, retry after a short delay (often fixes rapid restart).
        if (err === 'InvalidStateError' || err === 'recognition-start-failed') {
            setTimeout(() => this.speechManager.startListening({ autoRestart: true }), 500);
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
