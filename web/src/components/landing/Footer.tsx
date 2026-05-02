export const Footer = () => (
  <footer className="bg-paper-soft text-ink border-t border-ink/10">
    <div className="max-w-[1600px] mx-auto px-6 lg:px-10 py-16">
      <div className="grid md:grid-cols-[2fr_1fr_1fr_1fr_1fr] gap-10">
        <div>
          <div className="flex items-center gap-2 mb-5">
            <svg viewBox="0 0 24 24" className="h-5 w-5 text-ink" fill="none" aria-hidden>
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <span className="text-[15px] font-medium tracking-tight">Mnemosys</span>
          </div>
          <p className="text-[13px] text-ink-soft max-w-sm leading-relaxed">
            Governed AI memory for serious investment research. Built for teams that need
            auditable decisions, not autonomous trading.
          </p>
          <div className="mt-6 flex gap-2">
            {["US", "UK", "JP"].map((r) => (
              <button key={r} className="font-mono text-[10px] uppercase tracking-[0.16em] px-3 py-1 border border-ink/20 hover:bg-ink hover:text-paper transition-colors">{r}</button>
            ))}
          </div>
        </div>
        {[
          { h: "Platform", l: ["Beyond Chat", "Workspace", "Promotion", "Deliverables", "Audit"] },
          { h: "Company", l: ["About", "Research", "Careers", "Press"] },
          { h: "Customers", l: ["Hedge Funds", "Family Offices", "Allocators", "Banks"] },
          { h: "Trust", l: ["Security", "Privacy", "Disclosures", "Status"] },
        ].map((c) => (
          <div key={c.h}>
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-ink-muted mb-4">{c.h}</div>
            <ul className="space-y-2.5">
              {c.l.map((i) => (
                <li key={i}>
                  <a href="#" className="text-[13px] text-ink hover:text-primary transition-colors">{i}</a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mt-16 pt-6 border-t border-ink/10 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] uppercase tracking-[0.16em] text-ink-muted">
        <div>© 2026 Mnemosys Labs · All Rights Reserved</div>
        <div>Not Investment Advice · Not An Autonomous Trading System</div>
      </div>
    </div>
  </footer>
);
