"use client";
import React, { useEffect, useState, useRef } from 'react';

const lerp = (start: number, end: number, factor: number) => {
  return start + (end - start) * factor;
};

const Cursor: React.FC = () => {
  const [visible, setVisible] = useState(true);
  const [color, setColor] = useState<'white' | 'black'>('black');
  const actualPosition = useRef({ x: -50, y: -50 });
  const [position, setPosition] = useState({ x: -50, y: -50 });
  const animationFrameId = useRef<number | undefined>(undefined);

  const getLuminance = (rgb: string) => {
    const values = rgb.match(/\d+/g);
    if (!values || values.length < 3) return 255;
    const [r, g, b] = values.slice(0, 3).map(Number);
    return 0.299 * r + 0.587 * g + 0.114 * b;
  };

  useEffect(() => {
    const animate = () => {
      setPosition(prev => ({
        x: lerp(prev.x, actualPosition.current.x, 0.15),
        y: lerp(prev.y, actualPosition.current.y, 0.15)
      }));
      animationFrameId.current = requestAnimationFrame(animate);
    };

    const onMouseMove = (e: MouseEvent) => {
      actualPosition.current = { x: e.clientX, y: e.clientY };
      setVisible(true);

      const target = document.elementFromPoint(e.clientX, e.clientY) as HTMLElement | null;
      if (!target) return;

      const cursorThemeTarget = target.closest('[data-cursor-theme]') as HTMLElement | null;
      if (cursorThemeTarget?.dataset.cursorTheme === 'light') {
        setColor('white');
        return;
      }
      if (cursorThemeTarget?.dataset.cursorTheme === 'dark') {
        setColor('black');
        return;
      }

      let node: HTMLElement | null = target;
      let bgColor = '';

      while (node && node !== document.body) {
        const computed = window.getComputedStyle(node);
        const background = computed.backgroundColor;
        if (background && background !== 'rgba(0, 0, 0, 0)' && background !== 'transparent') {
          bgColor = background;
          break;
        }
        node = node.parentElement;
      }

      const luminance = bgColor ? getLuminance(bgColor) : 255;
      setColor(luminance > 150 ? 'black' : 'white');
    };

    const onMouseLeave = () => setVisible(false);

    document.addEventListener('mousemove', onMouseMove);
    document.body.addEventListener('mouseout', onMouseLeave);
    animationFrameId.current = requestAnimationFrame(animate);

    return () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.body.removeEventListener('mouseout', onMouseLeave);
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }
    };
  }, []);

  const cursorStyle: React.CSSProperties = {
    position: 'fixed',
    top: position.y,
    left: position.x,
    width: '15px',
    height: '15px',
    borderRadius: '50%',
    backgroundColor: color,
    pointerEvents: 'none',
    transform: 'translate(-50%, -50%)',
    zIndex: 9999,
    opacity: visible ? 1 : 0,
    transition: 'opacity 150ms ease, background-color 120ms ease',
  };

  return <div style={cursorStyle} />;
};

export default Cursor;