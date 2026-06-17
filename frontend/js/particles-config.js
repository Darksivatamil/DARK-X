class ParticleSystem {
    constructor() {
        this.canvas = document.getElementById('bg-particles');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticle() {
        return {
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            size: Math.random() * 1.5 + 0.5,
            speedX: (Math.random() - 0.5) * 0.3,
            speedY: -Math.random() * 0.5 - 0.1,
            opacity: Math.random() * 0.3 + 0.1,
        };
    }

    update() {
        if (this.particles.length < 60) this.particles.push(this.createParticle());
        this.particles.forEach((p, i) => {
            p.x += p.speedX;
            p.y += p.speedY;
            if (p.y < 0) this.particles[i] = this.createParticle();
        });
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.particles.forEach(p => {
            this.ctx.globalAlpha = p.opacity;
            this.ctx.fillStyle = '#7c3aed';
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            this.ctx.fill();
        });
    }

    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

const Effects = {
    flash() {
        const f = document.createElement('div');
        f.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:white;z-index:9999;pointer-events:none;opacity:1;transition:opacity 0.4s';
        document.body.appendChild(f);
        setTimeout(() => f.style.opacity = '0', 10);
        setTimeout(() => f.remove(), 500);
    },
};
