"use client";

import { useEffect, useState } from "react";

export default function Header({ navOpacity = 1 }: { navOpacity?: number }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [backgroundType, setBackgroundType] = useState<'light' | 'dark' | 'gradient'>('light');

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      setIsScrolled(scrollY > 50);

      // Determine background type based on scroll position
      const sections = document.querySelectorAll('section');
      let currentBg: 'light' | 'dark' | 'gradient' = 'light';

      sections.forEach((section) => {
        const rect = section.getBoundingClientRect();
        if (rect.top <= 100 && rect.bottom >= 100) {
          const bg = window.getComputedStyle(section).backgroundColor;
          if (bg.includes('rgb(15, 23, 42)') || bg.includes('#0f172a')) {
            currentBg = 'dark';
          } else if (bg.includes('gradient')) {
            currentBg = 'gradient';
          } else {
            currentBg = 'light';
          }
        }
      });

      setBackgroundType(currentBg);
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial check

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const getGlassmorphismClasses = () => {
    const baseClasses = "fixed top-0 left-0 right-0 z-50 transition-all duration-300 ease-in-out";

    if (backgroundType === 'dark') {
      return `${baseClasses} bg-slate-900/60 backdrop-blur-xl border-b border-slate-700/30`;
    } else if (backgroundType === 'gradient') {
      return `${baseClasses} bg-white/5 backdrop-blur-xl border-b border-white/10`;
    } else {
      return `${baseClasses} bg-white/80 backdrop-blur-xl border-b border-slate-200/50`;
    }
  };

  const getTextClasses = () => {
    return backgroundType === 'dark' ? 'text-white' : 'text-slate-950';
  };

  return (
    <header className={getGlassmorphismClasses()} style={{ opacity: navOpacity, pointerEvents: navOpacity < 0.1 ? 'none' : 'auto', transition: 'opacity 0.3s ease' }}>
      <div className="mx-auto max-w-7xl px-6 py-4 sm:px-10 lg:px-16">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <style dangerouslySetInnerHTML={{__html: `
            @keyframes gentle-shake {
              0% { transform: rotate(-8deg); }
              15% { transform: rotate(-13deg) scale(1.15); }
              30% { transform: rotate(-4deg) scale(1.18); }
              45% { transform: rotate(-12deg) scale(1.15); }
              60% { transform: rotate(-5deg) scale(1.12); }
              75% { transform: rotate(-10deg) scale(1.06); }
              100% { transform: rotate(-8deg) scale(1); }
            }
            .logo-hover:hover {
              animation: gentle-shake 1s ease-in-out;
            }
          `}} />
          <div className="flex items-center gap-3">
            <img
              src="/bucket.svg"
              alt="Collector"
              className="h-8 w-8 logo-hover transition-transform duration-700 ease-in-out"
              style={{ transform: 'rotate(-8deg)' }}
            />
            <span className={`text-xl font-bold uppercase tracking-wide ${getTextClasses()}`}>
              Collector
            </span>
          </div>

          {/* Navigation */}
          <nav className="hidden items-center gap-8 md:flex">
            <a href="#optimizer" className={`text-sm font-medium transition hover:opacity-80 ${getTextClasses()}`}>
              Optimizer
            </a>
            <a href="#features" className={`text-sm font-medium transition hover:opacity-80 ${getTextClasses()}`}>
              Features
            </a>
            <a href="#about" className={`text-sm font-medium transition hover:opacity-80 ${getTextClasses()}`}>
              About
            </a>
          </nav>

          {/* Auth Buttons */}
          <div className="flex items-center gap-3">
            <button className={`text-sm font-medium transition-all duration-300 hover:scale-110 ${getTextClasses()}`}>
              Log in
            </button>
            <button className="rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:scale-110">
              Sign up
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
