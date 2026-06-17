class VoiceCommandSystem {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.init();
    }

    init() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error("Voice Recognition not supported in this browser.");
            return;
        }
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.lang = 'en-US';
        
        this.recognition.onresult = (event) => {
            const command = event.results[0][0].transcript.toLowerCase();
            console.log("Voice Command Detected:", command);
            this.executeCommand(command);
        };
    }

    async executeCommand(cmd) {
        const terminalInput = document.getElementById('terminal-input');
        if (!terminalInput) return;

        // Map voice to terminal commands
        let mappedCmd = cmd;
        if (cmd.includes("awaken") || cmd.includes("arise")) mappedCmd = "/arise";
        if (cmd.includes("sleep") || cmd.includes("rest")) mappedCmd = "/rest";
        if (cmd.includes("status")) mappedCmd = "/status";
        
        // Simulate typing in terminal
        terminalInput.value = mappedCmd;
        terminalInput.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter' }));
    }

    toggleListening() {
        if (this.isListening) {
            this.recognition.stop();
            this.isListening = false;
        } else {
            this.recognition.start();
            this.isListening = true;
        }
    }
}

const voiceSystem = new VoiceCommandSystem();
