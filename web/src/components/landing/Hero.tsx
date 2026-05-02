import { Nav } from "./Nav";
import { ArrowDown } from "lucide-react";
import { useEffect, useState } from "react";

const HERO_MARK_TEXT = "{ MN }";

const TypingMark = () => {
  const [visibleChars, setVisibleChars] = useState(HERO_MARK_TEXT.length);
  const [isDeleting, setIsDeleting] = useState(true);

  useEffect(() => {
    const isFull = visibleChars === HERO_MARK_TEXT.length;
    const isEmpty = visibleChars === 0;
    const delay = isFull ? 1300 : isEmpty ? 450 : isDeleting ? 95 : 125;

    const timeout = window.setTimeout(() => {
      if (isFull) {
        setIsDeleting(true);
        setVisibleChars((count) => count - 1);
        return;
      }

      if (isEmpty) {
        setIsDeleting(false);
        setVisibleChars(1);
        return;
      }

      setVisibleChars((count) => count + (isDeleting ? -1 : 1));
    }, delay);

    return () => window.clearTimeout(timeout);
  }, [isDeleting, visibleChars]);

  return (
    <span className="typing-mark" aria-label={HERO_MARK_TEXT}>
      <span aria-hidden>{HERO_MARK_TEXT.slice(0, visibleChars)}</span>
    </span>
  );
};

export const Hero = () => {
  return (
    <section className="relative w-full bg-night text-white overflow-hidden">
      <Nav variant="dark" />

      {/* Cinematic wall */}
      <div className="relative h-screen min-h-[680px] w-full bg-[#2f3e4a]">
        {/* Top-right corner metadata rail */}
        <div className="absolute top-24 right-6 lg:right-10 z-10 hidden md:block">
          <div className="space-y-6 text-right font-mono text-[10px] uppercase tracking-[0.18em] text-white/70">
            <div>
              <div>Explore</div>
              <div>Our Governed AI</div>
              <div>Research Platform</div>
            </div>
            <div>
              <div>Time: 4 mins</div>
              <div>Scroll</div>
              <div>To Explore</div>
            </div>
            <div>
              <div>Built for serious</div>
              <div>investment</div>
              <div>operators</div>
            </div>
            <div>
              <div>Copyright ©2026</div>
              <div>Mnemosys</div>
              <div>Research Inc.</div>
            </div>
          </div>
        </div>

        {/* Oversized brand mark bottom-left */}
        <div className="absolute bottom-12 left-6 lg:left-10 z-10 select-none">
          <div className="flex items-end gap-3 sm:gap-5">
            <svg viewBox="0 0 80 80" className="h-20 sm:h-28 lg:h-36 w-auto text-white" fill="none" aria-hidden>
              <path d="M10 70 L10 10 L40 40 L70 10 L70 70" stroke="currentColor" strokeWidth="6" strokeLinejoin="miter" />
              <circle cx="40" cy="55" r="4" fill="currentColor" />
            </svg>
            <div className="font-display tracking-[-0.04em] text-[3.5rem] sm:text-[6rem] lg:text-[8rem] leading-[0.8]">
              <TypingMark />
            </div>
          </div>
        </div>

        {/* Section indicator top-left under nav */}
        <div className="absolute top-24 left-6 lg:left-10 z-10 hidden md:flex items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/60">Software</span>
        </div>
      </div>

      {/* Big editorial type below image - the "Go beyond chat" moment */}
      <div className="relative bg-paper text-ink">
        <div className="max-w-[1600px] mx-auto px-6 lg:px-10 pt-18 pb-16 lg:pt-24 lg:pb-20">
          <div className="flex items-start justify-between mb-12">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-ink-muted">{"{ MN }"}</span>
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-ink-muted">Get Started</span>
          </div>

          <h1 className="display text-[clamp(3rem,10vw,9rem)] text-ink text-balance">
            Go beyond chat.
            <br />
            <span className="text-aip-gradient">Governed Autonomy.</span>
          </h1>

          <div className="mt-12 lg:mt-16 flex flex-col items-center gap-3 text-center">
            <div className="text-ink-muted text-[15px]">Turn AI in your research workflow</div>
            <div className="text-ink text-[15px]">into Agents and Auditable Decisions</div>
            <a href="#beyond" className="mt-6 inline-flex flex-col items-center gap-2 text-ink hover:opacity-70 transition-opacity">
              <ArrowDown className="h-5 w-5" strokeWidth={1.5} />
              <span className="font-mono text-[10px] uppercase tracking-[0.18em]">Scroll to Explore</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};
