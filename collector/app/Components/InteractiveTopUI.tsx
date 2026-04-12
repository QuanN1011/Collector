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

    const drawGrid = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Light background gradient
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
      gradient.addColorStop(0, 'rgba(248, 250, 252, 0.05)'); // slate-50 with very low opacity
      gradient.addColorStop(0.5, 'rgba(241, 245, 249, 0.03)'); // slate-100 with very low opacity
      gradient.addColorStop(1, 'rgba(248, 250, 252, 0.05)'); // slate-50 with very low opacity

      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Set up grid properties
      const gridSize = 60;
      const lineWidth = 0.8;
      const maxOffset = 15;

      // Draw vertical lines with smooth offset based on mouse proximity
      for (let x = 0; x <= canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.15)'; // slate-400 with low opacity
        ctx.lineWidth = lineWidth;

        for (let y = 0; y <= canvas.height; y += 5) {
          const distance = Math.sqrt((x - mousePos.x) ** 2 + (y - mousePos.y) ** 2);
          const influence = Math.max(0, 1 - distance / 200); // Influence radius of 200px
          const offsetX = Math.sin(y * 0.01 + Date.now() * 0.001) * maxOffset * influence;

          if (y === 0) {
            ctx.moveTo(x + offsetX, y);
          } else {
            ctx.lineTo(x + offsetX, y);
          }
        }
        ctx.stroke();
      }

      // Draw horizontal lines with smooth offset based on mouse proximity
      for (let y = 0; y <= canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.15)'; // slate-400 with low opacity
        ctx.lineWidth = lineWidth;

        for (let x = 0; x <= canvas.width; x += 5) {
          const distance = Math.sqrt((x - mousePos.x) ** 2 + (y - mousePos.y) ** 2);
          const influence = Math.max(0, 1 - distance / 200); // Influence radius of 200px
          const offsetY = Math.sin(x * 0.01 + Date.now() * 0.001) * maxOffset * influence;

          if (x === 0) {
            ctx.moveTo(x, y + offsetY);
          } else {
            ctx.lineTo(x, y + offsetY);
          }
        }
        ctx.stroke();
      }

      // Draw diagonal accent lines
      const numDiagonals = 8;
      for (let i = 0; i < numDiagonals; i++) {
        const startX = (canvas.width / numDiagonals) * i;
        const startY = 0;
        const endX = startX + canvas.width * 0.4;
        const endY = canvas.height;

        ctx.beginPath();
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.08)'; // slate-400 with very low opacity
        ctx.lineWidth = 0.5;

        const steps = 50;
        for (let j = 0; j <= steps; j++) {
          const t = j / steps;
          const currentX = startX + (endX - startX) * t;
          const currentY = startY + (endY - startY) * t;

          const distance = Math.sqrt((currentX - mousePos.x) ** 2 + (currentY - mousePos.y) ** 2);
          const influence = Math.max(0, 1 - distance / 150);
          const waveOffset = Math.sin(t * Math.PI * 2 + Date.now() * 0.002) * 8 * influence;

          const offsetX = Math.cos(Math.atan2(endY - startY, endX - startX)) * waveOffset;
          const offsetY = Math.sin(Math.atan2(endY - startY, endX - startX)) * waveOffset;

          if (j === 0) {
            ctx.moveTo(currentX + offsetX, currentY + offsetY);
          } else {
            ctx.lineTo(currentX + offsetX, currentY + offsetY);
          }
        }
        ctx.stroke();
      }
    };

    const animate = () => {
      drawGrid();
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
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0"
      style={{ zIndex: 1 }}
    />
  );
};

export default InteractiveTopUI;