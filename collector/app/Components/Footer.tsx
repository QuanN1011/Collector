export default function Footer() {
  return (
    <footer className="relative mt-20 bg-slate-50 border-t border-slate-200/50">
      {/* Glassmorphism overlay */}
      <div className="absolute inset-0 bg-white/60 backdrop-blur-sm" />

      <div className="relative mx-auto max-w-7xl px-6 py-12 sm:px-10 lg:px-16">
        <div className="grid gap-8 md:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg">
                <span className="text-lg font-bold">C</span>
              </div>
              <span className="text-xl font-bold uppercase tracking-wide text-slate-950">
                Collector
              </span>
            </div>
            <p className="text-slate-600 max-w-md">
              Modern water systems intelligence for teams moving infrastructure from concept to control.
            </p>
          </div>

          {/* Product */}
          <div>
            <h3 className="font-semibold text-slate-950 mb-4">Product</h3>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#optimizer" className="hover:text-slate-950 transition">Pumping Optimizer</a></li>
              <li><a href="#features" className="hover:text-slate-950 transition">Features</a></li>
              <li><a href="#about" className="hover:text-slate-950 transition">Platform</a></li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="font-semibold text-slate-950 mb-4">Company</h3>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#" className="hover:text-slate-950 transition">About</a></li>
              <li><a href="#" className="hover:text-slate-950 transition">Contact</a></li>
              <li><a href="#" className="hover:text-slate-950 transition">Privacy</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-200/50 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-sm text-slate-500">
            © 2024 Collector. All rights reserved.
          </p>
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-slate-950 transition">Terms</a>
            <a href="#" className="hover:text-slate-950 transition">Privacy</a>
            <a href="#" className="hover:text-slate-950 transition">Support</a>
          </div>
        </div>
      </div>
    </footer>
  );
}