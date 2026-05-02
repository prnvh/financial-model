import { Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";

type Chapter = {
  index: string;
  num: number;
  title: string;
  caption: string;
  body: React.ReactNode;
};

const chapters: Chapter[] = [
  {
    index: "[0.1]",
    num: 1,
    title: "Designed for governed research",
    caption: "Mnemosys turns AI inside your investment workflow into specialized agents — observing markets, drafting updates, and queuing them for review.",
    body: <ResearchMock />,
  },
  {
    index: "[0.2]",
    num: 2,
    title: "Promotion before persistence",
    caption: "Agents propose updates. They never write to research memory alone. Every fact is reviewed, attributed, and reversible.",
    body: <PromotionMock />,
  },
  {
    index: "[0.3]",
    num: 3,
    title: "Deliverables anchored in truth",
    caption: "Reports, briefs, and risk memos regenerate from your structured memory — not from a model's best guess.",
    body: <DeliverableMock />,
  },
];

export const Chapters = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const snapTimeoutRef = useRef<number>();
  const progressRef = useRef(0);
  const wheelLockRef = useRef(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let frame = 0;

    const updateProgress = () => {
      const section = sectionRef.current;
      if (!section) return;

      const rect = section.getBoundingClientRect();
      const scrollable = rect.height - window.innerHeight;
      const nextProgress = scrollable <= 0 ? 0 : Math.min(Math.max(-rect.top / scrollable, 0), 1);
      progressRef.current = nextProgress;
      setProgress(nextProgress);
    };

    const scrollToChapter = (index: number) => {
      const section = sectionRef.current;
      if (!section) return;

      const rect = section.getBoundingClientRect();
      const scrollable = rect.height - window.innerHeight;
      const sectionTop = window.scrollY + rect.top;
      const targetY = sectionTop + (scrollable / (chapters.length - 1)) * index;

      wheelLockRef.current = true;
      window.scrollTo({
        top: targetY,
        behavior: "smooth",
      });
      window.setTimeout(() => {
        wheelLockRef.current = false;
      }, 620);
    };

    const snapToNearestChapter = () => {
      const section = sectionRef.current;
      if (!section) return;

      const rect = section.getBoundingClientRect();
      const scrollable = rect.height - window.innerHeight;
      const isInsidePinnedSection = rect.top <= 0 && rect.bottom >= window.innerHeight;

      if (!isInsidePinnedSection || scrollable <= 0) return;

      const currentProgress = Math.min(Math.max(-rect.top / scrollable, 0), 1);
      const nearestIndex = Math.round(currentProgress * (chapters.length - 1));
      scrollToChapter(nearestIndex);
    };

    const onScroll = () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(snapTimeoutRef.current);
      frame = window.requestAnimationFrame(updateProgress);
      snapTimeoutRef.current = window.setTimeout(snapToNearestChapter, 110);
    };

    const onWheel = (event: WheelEvent) => {
      const section = sectionRef.current;
      if (!section || wheelLockRef.current || Math.abs(event.deltaY) < 4) return;

      const rect = section.getBoundingClientRect();
      const isPinned = rect.top <= 1 && rect.bottom >= window.innerHeight - 1;
      if (!isPinned) return;

      const currentIndex = Math.round(progressRef.current * (chapters.length - 1));
      const direction = event.deltaY > 0 ? 1 : -1;
      const targetIndex = Math.min(Math.max(currentIndex + direction, 0), chapters.length - 1);

      if (targetIndex === currentIndex) return;

      event.preventDefault();
      window.clearTimeout(snapTimeoutRef.current);
      scrollToChapter(targetIndex);
    };

    updateProgress();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    window.addEventListener("wheel", onWheel, { passive: false });

    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(snapTimeoutRef.current);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      window.removeEventListener("wheel", onWheel);
    };
  }, []);

  const chapterPosition = progress * (chapters.length - 1);
  const activeIndex = Math.round(chapterPosition);

  return (
    <section ref={sectionRef} id="chapters" className="relative h-[300vh] bg-paper text-ink">
      <div className="sticky top-0 h-screen overflow-hidden">
        <div className="relative h-full max-w-[1600px] mx-auto px-6 lg:px-10">
          {chapters.map((c, index) => {
            const distance = index - chapterPosition;
            const isActive = activeIndex === index;

            return (
              <article
                key={c.index}
                className="absolute inset-x-6 lg:inset-x-10 top-0 h-screen flex flex-col justify-center py-10 lg:py-12 transition-[opacity,transform,filter] duration-700 ease-out"
                style={{
                  opacity: Math.max(0, 1 - Math.abs(distance) * 1.35),
                  transform: `translateY(${distance * 42}px) scale(${1 - Math.min(Math.abs(distance), 1) * 0.025})`,
                  pointerEvents: isActive ? "auto" : "none",
                }}
              >
                <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.4fr] gap-x-16 gap-y-8 mb-8 lg:mb-10">
                  <div>
                    <div className="flex items-center gap-3 chapter-rule mb-8">
                      {chapters.map((cc, i) => (
                        <span key={cc.index} className="flex items-center gap-3">
                          <span className={cc.index === c.index ? "text-ink" : "text-ink/40"}>
                            {cc.index === c.index ? cc.index : cc.index.replace(/[\[\]]/g, "")}
                          </span>
                          {i < chapters.length - 1 && <span className="h-px w-10 bg-ink/20 inline-block" />}
                        </span>
                      ))}
                    </div>
                    <h3 className="display text-[clamp(2.25rem,5vw,4rem)] text-ink text-balance">
                      {c.title}
                    </h3>
                  </div>
                  <div className="lg:pt-12">
                    <p className="text-[16px] lg:text-[18px] text-ink-soft leading-snug max-w-[44ch] tracking-tight">
                      {c.caption}
                    </p>
                    <div className="mt-5 inline-flex items-center gap-1 border border-ink/30 rounded-full overflow-hidden">
                      <button className="bg-ink text-paper px-4 py-1.5 rounded-full text-[12px] font-medium inline-flex items-center gap-1.5">
                        <Play className="h-3 w-3 fill-current" /> Demo
                      </button>
                      <button className="px-4 py-1.5 text-[12px] text-ink/70">Details</button>
                    </div>
                  </div>
                </div>

                {c.body}
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
};

function ResearchMock() {
  return (
    <div className="relative border border-ink/10 bg-night text-white aspect-[16/5.7] max-h-[48vh] overflow-hidden">
      <div className="grid grid-cols-[180px_1fr_220px] h-full text-[10px] font-mono">
        <div className="border-r border-white/10 p-3 space-y-1">
          <div className="text-white/40 uppercase tracking-wider mb-2">Workspace</div>
          {["Command Center", "Tracked List", "Watchlist", "Theses", "Promotion Queue", "Deliverables", "Audit Log"].map((s, i) => (
            <div key={s} className={`px-2 py-1 ${i === 0 ? "bg-primary/15 text-white border-l-2 border-primary" : "text-white/65"}`}>
              {s}
            </div>
          ))}
          <div className="text-white/40 uppercase tracking-wider mt-4 mb-2">Agents</div>
          {[["news.scraper", true], ["filings.parser", true], ["thesis.monitor", false], ["risk.detector", true]].map(([n, on]) => (
            <div key={n as string} className="flex items-center gap-2 px-2 text-white/60">
              <span className={`h-1.5 w-1.5 rounded-full ${on ? "bg-success animate-pulse-soft" : "bg-white/30"}`} />
              {n}
            </div>
          ))}
        </div>
        <div className="p-3 flex flex-col gap-2">
          <div className="flex justify-between text-white/40">
            <span>FRI · 01 MAY 2026 · 09:42 ET</span>
            <span>◉ ALL SYSTEMS NOMINAL</span>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {[
              ["Today's Brief", "READY", "primary"],
              ["Active Risks", "3", "warning"],
              ["Pending Promos", "207", "primary"],
              ["Watchlist Δ", "12", "success"],
            ].map(([l, v, t]) => (
              <div key={l as string} className="border border-white/10 bg-night-2/70 p-2">
                <div className="text-white/45 text-[9px] uppercase tracking-wider">{l}</div>
                <div className={`font-mono text-base mt-1 ${
                  t === "warning" ? "text-warning" : t === "success" ? "text-success" : "text-primary"
                }`}>{v}</div>
              </div>
            ))}
          </div>
          <div className="flex-1 grid grid-cols-2 gap-2">
            <div className="border border-white/10 bg-night-2/70 p-2">
              <div className="text-white/45 text-[9px] uppercase tracking-wider mb-1">Market signals</div>
              {[["SPX", "5,612.4", "+0.31%", true], ["NDX", "19,847", "+0.62%", true], ["VIX", "14.2", "-2.1%", false], ["10Y", "4.23%", "+3bp", true], ["DXY", "104.8", "+0.12%", true]].map(([t, p, c, up]) => (
                <div key={t as string} className="flex justify-between border-b border-white/5 py-0.5">
                  <span className="text-white/80">{t}</span><span className="text-white/55">{p}</span><span className={up ? "text-success" : "text-critical"}>{c}</span>
                </div>
              ))}
            </div>
            <div className="border border-white/10 bg-night-2/70 p-2">
              <div className="text-white/45 text-[9px] uppercase tracking-wider mb-1">News · classified</div>
              {[
                ["AVGO guides Q3 capex up 18%", "thesis"],
                ["China semi export probe", "risk"],
                ["ANET signs $4B hyperscaler deal", "watchlist"],
                ["Fed minutes: patient on cuts", "macro"],
              ].map(([t, tag]) => (
                <div key={t as string} className="border-b border-white/5 py-1">
                  <div className="text-white/80 text-[9px]">{t}</div>
                  <span className="text-primary text-[8px] uppercase tracking-wider">{tag}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="border-l border-white/10 p-3 space-y-1.5">
          <div className="text-white/45 uppercase tracking-wider mb-1">Human review</div>
          {["Promote: AVGO capex revision", "Disambiguate: NVDA Blackwell delay", "Confirm: AI Reset drift"].map((t, i) => (
            <div key={t} className="border border-white/10 p-1.5 bg-white/[0.02]">
              <div className="text-white/85 text-[9px] leading-snug">{t}</div>
              <div className="flex justify-between mt-1">
                <span className={`text-[8px] uppercase ${i === 1 ? "text-white/45" : "text-warning"}`}>{i === 1 ? "med" : "high"}</span>
                <span className="text-primary text-[8px]">OPEN →</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PromotionMock() {
  return (
    <div className="relative border border-ink/10 bg-night text-white aspect-[16/5.7] max-h-[48vh] overflow-hidden">
      <div className="px-5 py-3 border-b border-white/10 flex justify-between text-[11px] font-mono">
        <span className="text-white/55">Promotion Pipeline · 207 awaiting</span>
        <div className="flex gap-2">
          <button className="px-2 py-0.5 border border-white/20 text-[10px]">Bulk Promote (3)</button>
          <button className="px-2 py-0.5 border border-white/10 text-[10px] text-white/50">Reject</button>
        </div>
      </div>
      <div className="grid grid-cols-[40px_1fr_180px_120px_140px_120px] gap-2 px-5 py-2 border-b border-white/10 text-white/40 text-[9px] font-mono uppercase tracking-wider">
        <div></div><div>Proposal</div><div>Source</div><div>Confidence</div><div>Status</div><div>Action</div>
      </div>
      {[
        ["AVGO net cash → $11.2B (Q2 filing)", "filings.parser", "0.94", "validated", true],
        ["Add risk: China export probe to AI Reset", "news.scraper", "0.71", "ambiguous", true],
        ["Promote ANET to thesis-core", "thesis.monitor", "0.88", "needs review", true],
        ["Watchlist: add MRVL after capex revision", "watchlist.agent", "0.81", "needs review", false],
        ["Disambiguate: Arm Holdings entity match", "entity.linker", "0.62", "blocked", false],
        ["Update FOMC stance to 'patient on cuts'", "macro.parser", "0.91", "validated", false],
      ].map(([prop, src, conf, st, hi], i) => (
        <div key={i} className={`grid grid-cols-[40px_1fr_180px_120px_140px_120px] gap-2 px-5 py-2.5 border-b border-white/5 items-center text-[11px] font-mono ${hi ? "bg-primary/10" : ""}`}>
          <input type="checkbox" defaultChecked={!!hi} className="accent-primary" />
          <div className="text-white/90 truncate">{prop}</div>
          <div className="text-white/55">{src}</div>
          <div className={Number(conf) > 0.85 ? "text-primary" : "text-white/70"}>{conf}</div>
          <div>
            <span className={`px-1.5 py-0.5 border text-[9px] uppercase tracking-wider ${
              st === "validated" ? "border-success/40 text-success bg-success/5"
              : st === "ambiguous" ? "border-warning/40 text-warning bg-warning/5"
              : "border-white/15 text-white/60"
            }`}>{st as string}</span>
          </div>
          <div className="flex gap-1">
            <button className="px-2 py-0.5 border border-white/20 text-[9px] hover:bg-white/5">Promote</button>
            <button className="px-2 py-0.5 border border-white/10 text-[9px] text-white/50">Reject</button>
          </div>
        </div>
      ))}
    </div>
  );
}

function DeliverableMock() {
  return (
    <div className="relative border border-ink/10 bg-night text-white aspect-[16/5.4] max-h-[50vh] overflow-hidden">
      <div className="grid grid-cols-[200px_1fr_220px] h-full text-[10px] font-mono">
        <div className="border-r border-white/10 p-3">
          <div className="text-white/45 uppercase tracking-wider mb-2">Outline</div>
          {["Executive Summary", "Thesis Update", "Risk Register", "Position Sizing", "Catalysts", "Sources"].map((s, i) => (
            <div key={s} className={`py-1 ${i === 1 ? "text-primary border-l-2 border-primary pl-2" : "text-white/70 pl-2"}`}>{s}</div>
          ))}
        </div>
        <div className="p-4 overflow-hidden flex items-center">
          <div className="bg-paper text-ink mx-auto w-full max-w-[560px] p-5 shadow-[0_30px_60px_-30px_rgba(0,0,0,0.6)]">
            <div className="text-[8px] text-ink-muted flex justify-between mb-2">
              <span>MNEMOSYS / DAILY BRIEF</span>
              <span>FRI 01 MAY 2026</span>
            </div>
            <div className="font-sans text-[14px] font-semibold leading-tight mb-2 tracking-tight">
              AI Reset Thesis — Capex Revisions Tighten Conviction
            </div>
            <div className="font-sans text-[9px] text-ink-soft leading-snug mb-2">
              AVGO Q2 filing confirms net cash position of $11.2B, raising hyperscaler-served
              capex guidance by 18% YoY. Combined with ANET's $4B hyperscaler deal, the
              read-through to the broader AI buildout cohort is materially positive.
            </div>
            <div className="h-14 mb-2 flex items-end gap-1">
              {Array.from({ length: 28 }).map((_, i) => (
                <div key={i} className="flex-1 bg-gradient-to-t from-primary to-primary-2"
                  style={{ height: `${25 + Math.sin(i * 0.45) * 25 + i * 1.2}%` }} />
              ))}
            </div>
            <div className="font-sans text-[9px] text-ink-soft leading-snug mb-2">
              Risks: China semiconductor export probe announced 09:14 ET. Promoted to thesis
              risk register pending analyst review. See §3 for treatment and sizing impact.
            </div>
            <div className="grid grid-cols-3 gap-2 text-[9px]">
              {[["Conviction", "High"], ["Position Δ", "+0.4%"], ["Horizon", "12-18m"]].map(([l, v]) => (
                <div key={l} className="border border-ink/10 bg-paper-soft p-1.5">
                  <div className="text-ink-muted text-[8px] uppercase tracking-wider">{l}</div>
                  <div className="font-mono text-[11px] mt-0.5">{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="border-l border-white/10 p-3">
          <div className="text-white/45 uppercase tracking-wider mb-2">Sources</div>
          {[["AVGO 10-Q", "filings"], ["ANET 8-K", "filings"], ["FT 09:14 ET", "news"], ["FOMC minutes", "macro"], ["Internal note", "memory"], ["Promo #4821", "audit"]].map(([t, k]) => (
            <div key={t} className="border-b border-white/5 py-1.5">
              <div className="text-white/85 text-[10px]">{t}</div>
              <div className="text-primary text-[8px] mt-0.5 uppercase tracking-wider">{k}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
