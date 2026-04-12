export default function Footer() {
  return (
    <footer className="relative mt-20 bg-slate-50 border-t border-slate-200/50">
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes gentle-shake {
          0% { transform: rotate(0deg); }
          15% { transform: rotate(-5deg) scale(1.08); }
          30% { transform: rotate(4deg) scale(1.1); }
          45% { transform: rotate(-4deg) scale(1.08); }
          60% { transform: rotate(3deg) scale(1.05); }
          75% { transform: rotate(-2deg) scale(1.02); }
          100% { transform: rotate(0deg) scale(1); }
        }
        .footer-logo-hover:hover {
          animation: gentle-shake 1s ease-in-out;
        }
      `}} />
      {/* Glassmorphism overlay */}
      <div className="absolute inset-0 bg-white/60 backdrop-blur-sm" />

      <div className="relative mx-auto max-w-7xl px-6 py-12 sm:px-10 lg:px-16">
        <div className="grid gap-8 md:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <img
                src="/bucket.svg"
                alt="Collector"
                className="h-10 w-10 object-contain footer-logo-hover transition-transform duration-700 ease-in-out"
              />
              <span className="text-xl font-bold uppercase tracking-wide text-[#3e3d3c]">
                Collector
              </span>
            </div>
            <p className="text-slate-600 max-w-md">
              Modern water systems intelligence for teams moving infrastructure from concept to control.
            </p>
          </div>

          {/* Product */}
          <div>
            <h3 className="font-semibold text-[#3e3d3c] mb-4">Product</h3>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#rainuse-nexus" className="hover:text-slate-950 transition">RainUSE Nexus</a></li>
              <li><a href="#water-economics" className="hover:text-slate-950 transition">Water economics</a></li>
              <li><a href="#features" className="hover:text-slate-950 transition">Features</a></li>
              <li><a href="#about" className="hover:text-slate-950 transition">Platform</a></li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="font-semibold text-[#3e3d3c] mb-4">Company</h3>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#" className="hover:text-[#3e3d3c] transition">About</a></li>
              <li><a href="#" className="hover:text-[#3e3d3c] transition">Contact</a></li>
              <li><a href="#" className="hover:text-[#3e3d3c] transition">Privacy</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-200/50 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-sm text-slate-500">
            © 2024 Collector. All rights reserved.
          </p>
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-[#3e3d3c] transition">Terms</a>
            <a href="#" className="hover:text-[#3e3d3c] transition">Privacy</a>
            <a href="#" className="hover:text-[#3e3d3c] transition">Support</a>
          </div>
        </div>
      </div>
    </footer>
  );
}