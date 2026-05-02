const items = [
  "Hedge Funds & Multi-Strategy",
  "Family Offices & Private Wealth",
  "Independent Research Shops",
  "Investment Banking & Advisory",
  "Asset Allocators & Pensions",
  "Compliance & Risk Functions",
  "Sovereign Wealth & Endowments",
  "Quant Research Desks",
  "Corporate Strategy & M&A",
  "Credit & Distressed Funds",
  "Macro & Policy Analysts",
  "Boutique RIAs",
  "Insurance Investment Offices",
];

import { ArrowUpRight } from "lucide-react";

export const Industries = () => (
  <section className="relative bg-night text-white">
    <div className="max-w-[1600px] mx-auto px-6 lg:px-10 py-32 lg:py-44">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-12 lg:gap-20">
        <div className="lg:sticky lg:top-24 self-start">
          <h2 className="display text-[clamp(2.25rem,5vw,4rem)] text-white text-balance">
            Solving complex research problems across every kind of investment shop, in days, not years.
          </h2>
          <a
            href="#cta"
            className="mt-10 inline-flex items-center gap-2 px-5 py-2.5 border border-white/30 rounded-full text-[13px] text-white hover:bg-white hover:text-night transition-colors"
          >
            Explore Mnemosys Now
            <ArrowUpRight className="h-4 w-4" />
          </a>
        </div>

        <ul className="border-t border-white/10">
          {items.map((label, i) => (
            <li key={label} className="border-b border-white/10 group">
              <a
                href="#cta"
                className="flex items-center justify-between py-6 transition-colors"
              >
                <span className="font-mono text-[12px] text-white/40 w-10">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span
                  className="flex-1 display text-[clamp(1.75rem,3.6vw,3.25rem)] text-white/15 group-hover:text-white transition-colors duration-500"
                  style={{
                    WebkitTextStroke: "0px",
                  }}
                >
                  {label.toUpperCase()}
                </span>
                <ArrowUpRight className="h-5 w-5 text-white/0 group-hover:text-white transition-colors" />
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  </section>
);
