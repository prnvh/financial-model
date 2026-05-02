import { useState } from "react";

type Tab = {
  num: string;
  label: string;
  caption: string;
};

const tabs: Tab[] = [
  {
    num: "01",
    label: "Ingest",
    caption: "Filings, notes, decks, and models",
  },
  {
    num: "02",
    label: "Structure",
    caption: "Assumptions, drivers, risks, sources",
  },
  {
    num: "03",
    label: "Output",
    caption: "Financial model, memo, and audit trail",
  },
];

export const BeyondChat = () => {
  const [active, setActive] = useState(0);
  const tab = tabs[active];

  return (
    <section id="beyond" className="relative bg-night text-white">
      <div className="max-w-[1600px] mx-auto px-6 lg:px-10 pt-24 pb-32 lg:pt-32 lg:pb-44">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-10 mb-14 lg:mb-20 items-end">
          <div>
            <h2 className="display text-[clamp(2.5rem,6vw,5rem)] text-white">
              From Research To Model
            </h2>
            <p className="mt-4 text-night-muted text-[15px] tracking-tight">
              Mnemosys turns messy investment research into source-backed assumptions, reviewed model changes, and IC-ready outputs.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            {tabs.map((t, i) => (
              <button
                key={t.num}
                onClick={() => setActive(i)}
                className={`text-left px-5 py-3 min-w-[180px] border transition-colors ${
                  active === i
                    ? "border-white bg-white/5 text-white"
                    : "border-white/15 text-white/55 hover:text-white hover:border-white/40"
                }`}
              >
                <div className={`font-mono text-[11px] uppercase tracking-[0.16em] ${active === i ? "text-white" : "text-white/40"}`}>
                  {t.label}
                </div>
                <div className={`font-mono text-2xl mt-1 tabular-nums ${active === i ? "text-white" : "text-white/40"}`}>
                  {t.num}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="relative border border-white/15 bg-night-2/50 overflow-hidden">
          <div className="flex items-center gap-3 px-4 py-2 border-b border-white/10 bg-night/60">
            <div className="flex gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
            </div>
            <div className="flex-1 text-center font-mono text-[10px] uppercase tracking-[0.16em] text-white/40">
              {tab.label}
            </div>
            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-white/40">
              {tab.caption}
            </span>
          </div>

          <div className="relative aspect-[16/6.2] w-full overflow-hidden">
            <ProductMock kind={active} />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-x-10 gap-y-8 mt-10">
          {[
            "Ingest company materials and spreadsheet models without losing source context.",
            "Convert research into explicit assumptions, valuation drivers, risks, and reviewed updates.",
            "Produce model summaries, IC memos, and audit trails that stay tied to approved evidence.",
          ].map((text, i) => (
            <p key={text} className="text-[14px] text-white/75 leading-relaxed border-t border-white/15 pt-4">
              <span className="block font-mono text-[10px] uppercase tracking-[0.16em] text-white/40 mb-2">
                {tabs[i].label}
              </span>
              {text}
            </p>
          ))}
        </div>
      </div>
    </section>
  );
};

const ProductMock = ({ kind }: { kind: number }) => {
  if (kind === 0) return <ResearchMemoryMock />;
  if (kind === 1) return <AnalystReviewMock />;
  return <ICOutputsMock />;
};

function ResearchMemoryMock() {
  return (
    <div className="absolute inset-0 grid grid-cols-[44px_1fr_250px] bg-night-2 text-white/80 text-[10px] font-mono">
      <div className="border-r border-white/10 py-3 flex flex-col items-center gap-3">
        {Array.from({ length: 7 }).map((_, i) => (
          <span key={i} className={`h-4 w-4 rounded-sm ${i === 0 ? "bg-white/40" : "bg-white/10"}`} />
        ))}
      </div>
      <div className="p-2.5 flex flex-col gap-2">
        <div className="flex justify-between text-white/50">
          <span>Ingest / Datacenter Infrastructure Diligence</span>
          <span>Updated 09:42 ET</span>
        </div>
        <div className="flex-1 grid grid-cols-3 gap-2">
          <div className="col-span-2 border border-white/10 bg-night/70 p-2.5">
            <div className="text-white/50 mb-2">SOURCE INTAKE</div>
            <div className="grid grid-cols-2 gap-2">
              {[
                ["10-K Filing", "parsed", "38 refs"],
                ["Q1 Transcript", "parsed", "22 refs"],
                ["Operating Model", "linked", "v14"],
                ["Board Deck", "indexed", "17 refs"],
                ["Risk Memo", "mapped", "6 risks"],
                ["IC Notes", "indexed", "12 notes"],
              ].map(([label, value, source]) => (
                <div key={label} className="border border-white/10 bg-white/[0.03] p-2">
                  <div className="text-white/45 text-[9px] uppercase tracking-wider">{label}</div>
                  <div className="text-white text-[13px] mt-1">{value}</div>
                  <div className="text-primary text-[9px] mt-1">{source}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="border border-white/10 bg-night/70 p-2 flex flex-col gap-1.5">
            <div className="text-white/50 mb-1">EXTRACTED SIGNALS</div>
            {["Revenue guide changed", "Margin bridge updated", "Customer concentration", "Capex plan revised", "New risk language"].map((t, i) => (
              <div key={t} className="border border-white/10 bg-white/5 p-1.5">
                <div className="text-white/85 text-[11px] truncate">{t}</div>
                <div className="flex justify-between mt-1 text-[9px]">
                  <span className="text-primary">{3 + i} refs</span>
                  <span className="text-white/40">verified</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="border border-white/10 bg-night/70 p-2 grid grid-cols-5 gap-2 text-[9px]">
          {[["Companies", "18"], ["Assumptions", "142"], ["Sources", "391"], ["Open Risks", "7"], ["Memo", "Draft"]].map(([l, v]) => (
            <div key={l}>
              <div className="text-white/50">{l}</div>
              <div className="text-white text-base font-mono mt-0.5">{v}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="border-l border-white/10 p-2.5 flex flex-col gap-1.5">
        <div className="text-white/50 mb-1">DESTINATIONS</div>
        {["Assumption library", "Model driver map", "Risk register", "Memo evidence", "Scenario notes", "Source binder"].map((t, i) => (
          <div key={t} className="flex items-center justify-between border-b border-white/5 pb-1">
            <span className="text-white/85">{t}</span>
            <span className={i % 3 === 0 ? "text-warning" : "text-success"}>{i % 3 === 0 ? "review" : "locked"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalystReviewMock() {
  return (
    <div className="absolute inset-0 bg-night-2 text-white/85 text-[11px] font-mono flex flex-col">
      <div className="px-4 py-2 border-b border-white/10 flex justify-between text-white/50 text-[10px]">
        <span>Structure / proposed model and memo updates</span>
        <span>23 TO REVIEW</span>
      </div>
      <div className="grid grid-cols-[40px_1fr_150px_90px_120px_100px] gap-2 px-4 py-2 border-b border-white/10 text-white/40 text-[9px] uppercase tracking-wider">
        <div></div><div>Structured Item</div><div>Evidence</div><div>Type</div><div>Status</div><div>Action</div>
      </div>
      {[
        ["Raise FY27 revenue CAGR from 16% to 18%", "Q1 call + model", "valuation", "validated", "primary"],
        ["Add export controls to bear-case risk memo", "policy note", "risk", "needs edit", "muted"],
        ["Update terminal multiple comp range to 16-20x", "comp sheet", "model", "validated", "primary"],
        ["Flag customer concentration disclosure", "10-K", "diligence", "review", "muted"],
        ["Retire old margin bridge from appendix", "model v13", "cleanup", "review", "muted"],
      ].map(([prop, src, impact, st, tone], i) => (
        <div
          key={prop}
          className={`grid grid-cols-[40px_1fr_150px_90px_120px_100px] gap-2 px-4 py-2.5 border-b border-white/5 items-center ${
            i < 2 ? "bg-primary/12" : ""
          }`}
        >
          <input type="checkbox" defaultChecked={i < 2} className="accent-primary" />
          <div className="text-white/90 truncate">{prop}</div>
          <div className="text-white/55">{src}</div>
          <div className={tone === "primary" ? "text-primary" : "text-white/70"}>{impact}</div>
          <div>
            <span className={`px-1.5 py-0.5 border text-[9px] uppercase tracking-wider ${
              st === "validated"
                ? "border-success/40 text-success bg-success/5"
                : st === "needs edit"
                ? "border-warning/40 text-warning bg-warning/5"
                : st === "blocked"
                ? "border-critical/40 text-critical bg-critical/5"
                : "border-white/15 text-white/60"
            }`}>{st}</span>
          </div>
          <div className="flex gap-1">
            <button className="px-2 py-0.5 border border-white/20 text-[9px] hover:bg-white/5">Accept</button>
            <button className="px-2 py-0.5 border border-white/10 text-[9px] text-white/50">Reject</button>
          </div>
        </div>
      ))}
    </div>
  );
}

function ICOutputsMock() {
  return (
    <div className="absolute inset-0 grid grid-cols-[200px_1fr_210px] bg-night-2 text-white/85 text-[10px] font-mono">
      <div className="border-r border-white/10 p-3">
        <div className="text-white/50 mb-2">OUTPUTS</div>
        {["IC Memo", "Model Summary", "Assumption Log", "Risk Register", "Scenario Pack", "Source Binder"].map((s, i) => (
          <div key={s} className={`py-1 ${i === 0 ? "text-primary border-l-2 border-primary pl-2" : "text-white/70 pl-2"}`}>
            {s}
          </div>
        ))}
      </div>
      <div className="bg-white/95 m-3 text-ink p-4 overflow-hidden">
        <div className="text-[8px] text-ink-muted mb-2 flex justify-between">
          <span>MNEMOSYS / INVESTMENT COMMITTEE</span>
          <span>MODEL V18 / APPROVED SOURCES</span>
        </div>
        <div className="font-sans text-[14px] font-semibold leading-tight mb-2">
          Datacenter Infrastructure - Memo Draft
        </div>
        <div className="font-sans text-[10px] text-ink-soft leading-relaxed mb-3">
          Base case assumes 18% FY27 revenue CAGR, 64.5% steady-state gross margin, and
          continued hyperscaler demand. Key assumptions are linked to the model and reviewed sources.
        </div>
        <div className="h-12 mb-2 flex items-end gap-1">
          {Array.from({ length: 24 }).map((_, i) => (
            <div key={i} className="flex-1 bg-gradient-to-t from-primary to-primary-2"
              style={{ height: `${20 + Math.sin(i * 0.5) * 30 + i * 1.5}%` }} />
          ))}
        </div>
        <div className="font-sans text-[10px] text-ink-soft leading-relaxed mb-2">
          Bear case centers on pricing pressure and export-control exposure, tied to approved evidence.
        </div>
        <div className="grid grid-cols-3 gap-2 text-[8px]">
          {["Base IRR", "Downside", "Confidence"].map((l, i) => (
            <div key={l} className="border border-ink/10 p-1.5">
              <div className="text-ink-muted">{l}</div>
              <div className="font-mono text-[10px] mt-0.5">{["18.4%", "-11.2%", "High"][i]}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="border-l border-white/10 p-3">
        <div className="text-white/50 mb-2">AUDIT TRAIL</div>
        {[
          ["Revenue CAGR", "analyst approved"],
          ["Margin bridge", "source linked"],
          ["Risk register", "updated"],
          ["Scenario pack", "model synced"],
          ["Memo draft", "ready"],
        ].map(([t, k]) => (
          <div key={t} className="border-b border-white/5 py-1.5">
            <div className="text-white/85 text-[10px]">{t}</div>
            <div className="text-primary text-[8px] mt-0.5 uppercase tracking-wider">{k}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
