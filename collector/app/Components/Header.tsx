"use client";

import { useEffect, useState } from "react";

export default function Header() {
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
    <header className={getGlassmorphismClasses()}>
      <div className="mx-auto max-w-7xl px-6 py-4 sm:px-10 lg:px-16">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg">
              <span className="text-lg font-bold">C</span>
            </div>
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
