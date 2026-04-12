"use client";
import React, { useEffect, useRef, useState } from 'react';

const InteractiveTopUI: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
    };

    const drawTopography = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const lineCount = 12;
      const amplitude = 24;
      const spacing = canvas.height / (lineCount + 1.5);
      const time = performance.now() * 0.001;

      for (let i = 0; i < lineCount; i += 1) {
        const baseY = spacing * (i + 1);
        const sway = Math.sin(time * 0.8 + i * 0.5) * 16;
        const offsetIntensity = 1 - Math.abs(mousePos.y - baseY) / canvas.height;
        ctx.beginPath();
        ctx.strokeStyle = i % 2 === 0 ? 'rgba(14, 165, 233, 0.24)' : 'rgba(29, 78, 216, 0.16)';
        ctx.lineWidth = 1.4;
        ctx.lineJoin = 'round';

        for (let x = 0; x <= canvas.width; x += 24) {
          const wave = Math.sin((x / canvas.width) * Math.PI * 2 + time + i) * amplitude;
          const mouseShift = Math.sin((mousePos.x / canvas.width) * Math.PI + time * 0.7) * 8 * offsetIntensity;
          const y = baseY + wave + sway * 0.15 + mouseShift;

          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      }

      const nodes = [
        { x: canvas.width * 0.18, y: canvas.height * 0.55 },
        { x: canvas.width * 0.66, y: canvas.height * 0.34 },
        { x: canvas.width * 0.88, y: canvas.height * 0.7 },
      ];

      nodes.forEach((node, index) => {
        const pulse = 1 + Math.sin(time * 2 + index * 1.7) * 0.2;
        ctx.beginPath();
        ctx.fillStyle = 'rgba(14, 165, 233, 0.18)';
        ctx.arc(node.x, node.y, 12 * pulse, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
        ctx.lineWidth = 2;
        ctx.arc(node.x, node.y, 18 * pulse, 0, Math.PI * 2);
        ctx.stroke();
      });
    };

    const animate = () => {
      drawTopography();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    window.addEventListener('mousemove', handleMouseMove);
    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [mousePos]);

  return (
    <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 1 }}>
      <canvas
        ref={canvasRef}
        className="absolute inset-0"
      />
    </div>
  );
};

export default InteractiveTopUI;
