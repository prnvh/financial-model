import { ArrowRight } from "lucide-react";

export const CTA = () => (
  <section id="cta" className="relative bg-paper text-ink">
    <div className="max-w-[1600px] mx-auto px-6 lg:px-10 py-32 lg:py-44">
      {/* Mark */}
      <div className="flex justify-center mb-10">
        <svg viewBox="0 0 80 80" className="h-16 w-auto text-ink" fill="none" aria-hidden>
          <path d="M10 70 L10 10 L40 40 L70 10 L70 70" stroke="currentColor" strokeWidth="6" />
          <circle cx="40" cy="55" r="4" fill="currentColor" />
        </svg>
      </div>

      <h2 className="display text-[clamp(2.5rem,7vw,6rem)] text-ink text-center text-balance mb-20">
        Build now with Mnemosys
      </h2>

      <div className="grid md:grid-cols-2 gap-px bg-ink/10 border border-ink/10">
        <a
          href="#"
          className="group relative bg-paper-soft p-10 lg:p-14 min-h-[360px] flex flex-col justify-between overflow-hidden hover:bg-paper transition-colors"
        >
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-ink-muted mb-4">
              Apply for the cohort
            </div>
            <h3 className="display text-[clamp(1.75rem,3vw,2.5rem)] text-ink leading-tight max-w-[12ch]">
              Build with Mnemosys
            </h3>
            <p className="mt-5 text-[15px] text-ink-soft max-w-md leading-relaxed">
              Request access to the next cohort. We deploy your private instance, wire it to
              your sources, and ship your first daily brief within a week.
            </p>
          </div>
          <div className="mt-10 flex items-center justify-between">
            <span className="text-[13px] text-ink font-medium">Request access</span>
            <span className="h-12 w-12 rounded-full bg-ink text-paper flex items-center justify-center group-hover:scale-110 transition-transform">
              <ArrowRight className="h-5 w-5" />
            </span>
          </div>
        </a>

        <a
          href="#beyond"
          className="group relative bg-paper-soft p-10 lg:p-14 min-h-[360px] flex flex-col justify-between overflow-hidden hover:bg-paper transition-colors"
        >
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-ink-muted mb-4">
              Tour the system
            </div>
            <h3 className="display text-[clamp(1.75rem,3vw,2.5rem)] text-ink leading-tight max-w-[14ch]">
              Explore Mnemosys Now
            </h3>
            <p className="mt-5 text-[15px] text-ink-soft max-w-md leading-relaxed">
              Walk through a live promotion queue, a strategy workspace, and a sample daily
              research deliverable — pulled from a representative cohort dataset.
            </p>
          </div>
          <div className="mt-10 flex items-center justify-between">
            <span className="text-[13px] text-ink font-medium">Open the console</span>
            <span className="h-12 w-12 rounded-full border border-ink text-ink flex items-center justify-center group-hover:bg-ink group-hover:text-paper transition-colors">
              <ArrowRight className="h-5 w-5" />
            </span>
          </div>
        </a>
      </div>
    </div>
  </section>
);
