"use client";

import { Montagu_Slab } from "next/font/google";
import { useEffect, useRef, useState } from "react";

const montaguSlab = Montagu_Slab({
  subsets: ["latin"],
  weight: ["500", "600"],
});

export default function Header({ navOpacity = 1 }: { navOpacity?: number }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [backgroundType, setBackgroundType] = useState<'light' | 'dark' | 'gradient'>('light');
  const menuRef = useRef<HTMLDivElement | null>(null);

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

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleEscape);
    };
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
    return backgroundType === 'dark' ? 'text-white' : 'text-[#3e3d3c]';
  };

  const getDropdownPanelClasses = () => {
    if (backgroundType === 'dark') {
      return 'bg-slate-900';
    }
    if (backgroundType === 'gradient') {
      return 'bg-white';
    }
    return 'bg-white';
  };

  return (
    <header className={getGlassmorphismClasses()} style={{ opacity: navOpacity, pointerEvents: navOpacity < 0.1 ? 'none' : 'auto', transition: 'opacity 0.3s ease' }}>
      <div className="mx-auto max-w-7xl px-6 py-4 sm:px-10 lg:px-16">
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
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
            .menu-underline {
              position: relative;
              display: inline-flex;
              width: fit-content;
            }
            .menu-underline::after {
              content: '';
              position: absolute;
              left: 0;
              bottom: -5px;
              width: 100%;
              height: 2px;
              background: currentColor;
              transform: scaleX(0);
              transform-origin: left;
              transition: transform 300ms ease;
            }
            .menu-underline:hover::after,
            .menu-underline:focus-visible::after {
              transform: scaleX(1);
            }
          `}} />

          {/* Left dropdown navigation */}
          <div className="flex items-center justify-start">
            <div ref={menuRef} className="relative hidden lg:block">
              <button
                type="button"
                onClick={() => setIsMenuOpen((prev) => !prev)}
                aria-expanded={isMenuOpen}
                aria-controls="header-dropdown-nav"
                aria-label="Open section menu"
                className={`inline-flex h-14 w-14 items-center justify-center overflow-visible transition ${getTextClasses()}`}
              >
                <span className="relative block h-8 w-8" aria-hidden="true">
                  <span
                    className={`absolute left-1/2 top-[9px] h-[2.5px] w-6 -translate-x-1/2 bg-current origin-center transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${isMenuOpen ? 'top-[52%] -translate-y-1/2 rotate-45' : ''}`}
                  />
                  <span
                    className={`absolute left-1/2 top-[18px] h-[2.5px] w-6 -translate-x-1/2 bg-current origin-center transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${isMenuOpen ? 'top-[52%] -translate-y-1/2 -rotate-45' : ''}`}
                  />
                </span>
              </button>

              <div
                id="header-dropdown-nav"
                className={`absolute left-0 top-full mt-2 w-[184px] rounded-none px-5 pt-5 pb-7 shadow-[0_12px_30px_rgba(15,23,42,0.14)] backdrop-blur-xl transition-all duration-300 ${getDropdownPanelClasses()} ${isMenuOpen ? 'pointer-events-auto translate-y-0 opacity-100' : 'pointer-events-none -translate-y-2 opacity-0'}`}
              >
                <div className="mb-4 flex items-center gap-2">
                  <img
                    src="/bucket.svg"
                    alt="Collector"
                    className="h-5 w-5"
                  />
                  <span className={`text-xs font-bold uppercase tracking-[0.2em] transition-opacity duration-300 ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
                    Collector
                  </span>
                </div>
                <nav className="grid gap-5">
                  <a href="#optimizer" onClick={() => setIsMenuOpen(false)} className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
                    Optimizer
                  </a>
                  <a href="#features" onClick={() => setIsMenuOpen(false)} className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
                    Features
                  </a>
                  <a href="#about" onClick={() => setIsMenuOpen(false)} className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
                    About
                  </a>
                </nav>
              </div>
            </div>
          </div>

          {/* Center logo */}
          <div className="flex items-center justify-center gap-3 justify-self-center">
            <img
              src="/bucket.svg"
              alt="Collector"
              className="h-8 w-8 logo-hover transition-transform duration-700 ease-in-out"
              style={{ transform: 'rotate(-8deg)' }}
            />
            <span className={`text-xl font-bold uppercase tracking-wide transition-opacity duration-300 ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
              Collector
            </span>
          </div>

          {/* Auth Buttons */}
          <div className="flex items-center justify-end gap-3">
            <button className={`text-sm font-medium transition-all duration-300 hover:scale-110 ${getTextClasses()}`}>
              Log in
            </button>
            <button className="rounded-full bg-[#3e3d3c] px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:scale-110 hover:bg-[#2c2b2a]">
              Sign up
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
