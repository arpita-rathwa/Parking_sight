import { useEffect, useRef } from "react";

export const FloatingLights = () => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
    <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-blue-500/20 blur-[120px] mix-blend-screen animate-pulse duration-[8000ms]" />
    <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] rounded-full bg-purple-600/20 blur-[150px] mix-blend-screen animate-pulse duration-[6000ms] delay-700" />
    <div className="absolute top-[20%] left-[50%] -translate-x-1/2 w-[800px] h-[400px] rounded-full bg-indigo-500/10 blur-[100px] mix-blend-screen animate-pulse duration-[7000ms] delay-1000" />
  </div>
);

export const AnimatedCanvas = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let particles: { x: number; y: number; size: number; speedY: number; opacity: number }[] = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", resize);
    resize();

    for (let i = 0; i < 120; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 0.5,
        speedY: Math.random() * 0.5 + 0.1,
        opacity: Math.random() * 0.5 + 0.1,
      });
    }

    const drawGrid = () => {
      ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
      ctx.lineWidth = 1;
      const gridSize = 50;
      for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
      }
    };

    const drawLightTrails = (time: number) => {
      ctx.lineWidth = 2;
      for (let i = 0; i < 6; i++) {
        const y = canvas.height - 80 - i * 18;
        const x = (time * (i + 1) * 0.04) % (canvas.width + 200) - 100;
        const isWhite = i % 2 === 0;
        const grad = ctx.createLinearGradient(x, y, x + 120, y);
        grad.addColorStop(0, "rgba(255,255,255,0)");
        grad.addColorStop(0.5, isWhite ? "rgba(200,220,255,0.7)" : "rgba(255,60,60,0.6)");
        grad.addColorStop(1, "rgba(255,255,255,0)");
        ctx.strokeStyle = grad;
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 120, y); ctx.stroke();
      }
    };

    const render = (time: number) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      drawGrid();

      ctx.fillStyle = "#050812";
      ctx.beginPath();
      ctx.moveTo(0, canvas.height);
      ctx.lineTo(0, canvas.height - 200);
      ctx.lineTo(50, canvas.height - 200);
      ctx.lineTo(50, canvas.height - 350);
      ctx.lineTo(120, canvas.height - 350);
      ctx.lineTo(120, canvas.height - 250);
      ctx.lineTo(250, canvas.height - 250);
      ctx.lineTo(250, canvas.height - 400);
      ctx.lineTo(350, canvas.height - 400);
      ctx.lineTo(350, canvas.height - 150);
      ctx.lineTo(450, canvas.height - 150);
      ctx.lineTo(450, canvas.height - 450);
      ctx.lineTo(550, canvas.height - 450);
      ctx.lineTo(550, canvas.height - 250);
      ctx.lineTo(650, canvas.height - 250);
      ctx.lineTo(650, canvas.height - 300);
      ctx.lineTo(canvas.width, canvas.height - 300);
      ctx.lineTo(canvas.width, canvas.height);
      ctx.fill();

      ctx.fillStyle = "rgba(255, 255, 200, 0.18)";
      for (let i = 0; i < 18; i++) {
        const wx = 60 + i * 20;
        if (wx < 110) { ctx.fillRect(wx, canvas.height - 330, 5, 5); ctx.fillRect(wx, canvas.height - 310, 5, 5); }
      }

      drawLightTrails(time);

      particles.forEach((p) => {
        ctx.fillStyle = `rgba(100, 150, 255, ${p.opacity})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        p.y -= p.speedY;
        if (p.y < 0) { p.y = canvas.height; p.x = Math.random() * canvas.width; }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render(0);
    return () => { window.removeEventListener("resize", resize); cancelAnimationFrame(animationFrameId); };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 z-0 opacity-40 pointer-events-none" />;
};
