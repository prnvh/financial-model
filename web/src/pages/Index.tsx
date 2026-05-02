import { Hero } from "@/components/landing/Hero";
import { BeyondChat } from "@/components/landing/BeyondChat";
import { Chapters } from "@/components/landing/Chapters";
import { Industries } from "@/components/landing/Industries";
import { CTA } from "@/components/landing/CTA";
import { Footer } from "@/components/landing/Footer";
import { useEffect } from "react";

const Index = () => {
  useEffect(() => {
    document.title = "Mnemosys — Go beyond chat. Governed research autonomy.";
    const meta =
      document.querySelector('meta[name="description"]') ||
      (() => {
        const m = document.createElement("meta");
        m.setAttribute("name", "description");
        document.head.appendChild(m);
        return m;
      })();
    meta.setAttribute(
      "content",
      "Mnemosys turns AI in your investment research into specialized agents with structured memory, auditable decisions, and human-reviewed deliverables.",
    );
  }, []);

  return (
    <div className="min-h-screen bg-paper text-ink">
      <main>
        <Hero />
        <BeyondChat />
        <Chapters />
        <Industries />
        <CTA />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
