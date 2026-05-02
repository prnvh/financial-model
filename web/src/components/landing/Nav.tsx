import { Search, Menu } from "lucide-react";

export const Nav = ({ variant = "dark" }: { variant?: "dark" | "light" }) => {
  const dark = variant === "dark";
  return (
    <header className={`absolute top-0 inset-x-0 z-40 ${dark ? "bg-night/30 backdrop-blur-sm" : "bg-paper/60 backdrop-blur-sm"} border-b ${dark ? "border-white/10" : "border-ink/10"}`}>
      <div className="max-w-[1600px] mx-auto px-6 lg:px-10 h-16 flex items-center justify-between">
        <a href="#" className={`flex items-center gap-2 ${dark ? "text-white" : "text-ink"}`}>
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden>
            <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
            <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.5" />
          </svg>
          <span className="text-[15px] font-medium tracking-tight">Mnemosys</span>
        </a>
        <div className="flex items-center gap-2">
          <a
            href="#cta"
            className={`text-[13px] font-medium px-4 h-9 inline-flex items-center rounded-full transition-colors ${
              dark
                ? "bg-white text-night hover:bg-white/90"
                : "bg-ink text-paper hover:bg-ink/90"
            }`}
          >
            Get Started
          </a>
          <button
            aria-label="Search"
            className={`h-9 w-9 rounded-full border flex items-center justify-center transition-colors ${
              dark ? "border-white/30 text-white hover:bg-white/10" : "border-ink/30 text-ink hover:bg-ink/5"
            }`}
          >
            <Search className="h-4 w-4" />
          </button>
          <button
            aria-label="Menu"
            className={`h-9 w-9 rounded-full border flex items-center justify-center transition-colors ${
              dark ? "border-white/30 text-white hover:bg-white/10" : "border-ink/30 text-ink hover:bg-ink/5"
            }`}
          >
            <Menu className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
