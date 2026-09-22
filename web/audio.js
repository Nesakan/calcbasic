/**
 * Web Audio API synthesizer for vintage Casio clicks, tape motor hum, and 1200-baud FSK chirps.
 */
class CasioAudioSynthesizer {
    constructor() {
        this.ctx = null;
        this.enabled = true;
        this.motorNode = null;
        this.motorGain = null;
    }

    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) {
                this.ctx = new AudioCtx();
            }
        }
        if (this.ctx && this.ctx.state === "suspended") {
            this.ctx.resume();
        }
    }

    toggleSound() {
        this.enabled = !this.enabled;
        return this.enabled;
    }

    playClick() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = "sine";
        osc.frequency.setValueAtTime(800 + Math.random() * 200, this.ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(100, this.ctx.currentTime + 0.015);

        gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.015);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start();
        osc.stop(this.ctx.currentTime + 0.016);
    }

    playBeep(freq = 1000, duration = 0.08) {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = "square";
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

        gain.gain.setValueAtTime(0.05, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start();
        osc.stop(this.ctx.currentTime + duration);
    }

    playErrorBeep() {
        if (!this.enabled) return;
        this.playBeep(320, 0.12);
        setTimeout(() => this.playBeep(260, 0.18), 130);
    }

    /**
     * Synthesize authentic cassette tape FSK (Frequency Shift Keying) tone burst
     * Standard audio tones: 1200Hz and 2400Hz frequency hopping
     */
    playTapeChirp(durationMs = 800) {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const startTime = this.ctx.currentTime;
        const endTime = startTime + (durationMs / 1000);

        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = "sawtooth";

        // Frequency shift between 1200Hz and 2400Hz rapidly
        const hops = Math.floor(durationMs / 25);
        for (let i = 0; i < hops; i++) {
            const t = startTime + (i * 0.025);
            const freq = Math.random() > 0.5 ? 1200 : 2400;
            osc.frequency.setValueAtTime(freq, t);
        }

        gain.gain.setValueAtTime(0.03, startTime);
        gain.gain.setValueAtTime(0.03, endTime - 0.05);
        gain.gain.linearRampToValueAtTime(0.001, endTime);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(startTime);
        osc.stop(endTime);
    }
}
