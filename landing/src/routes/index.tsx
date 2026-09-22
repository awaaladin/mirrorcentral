import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { ArrowRight, Camera, Check, LockKeyhole, ScanFace, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { PageShell, StoreBadges, MirrorMark } from "@/components/mirror-shell";
import portraitOne from "@/assets/mirror-portrait-one.jpg";
import portraitTwo from "@/assets/mirror-portrait-two.jpg";
import portraitThree from "@/assets/mirror-portrait-three.jpg";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "mirror — Nigerian Atelier Makeup Simulator" },
    { name: "description", content: "Try makeup in real time with private, fully offline face landmark simulation made for Nigerian beauty." },
    { property: "og:title", content: "mirror — Nigerian Atelier Makeup Simulator" },
    { property: "og:description", content: "Private, precise makeup simulation that works fully offline." },
    { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
  ]}), component: HomePage,
});

const portraits = [portraitOne, portraitTwo, portraitThree];
const shades = ["shade-cocoa", "shade-clay", "shade-berry", "shade-rose", "shade-flame", "shade-wine"];
const categories = ["Eyeliner", "Eye color", "Lashes", "Blush", "Brows"];

function HomePage() {
  const [category, setCategory] = useState("Blush");
  const [shade, setShade] = useState(1);
  const [saturation, setSaturation] = useState([68]);
  const [intensity, setIntensity] = useState([52]);
  return (
    <PageShell>
      <div className="splash pointer-events-none fixed inset-0 z-[100] grid place-items-center bg-background">
        <div className="text-center"><div className="mx-auto w-fit"><MirrorMark /></div><div className="mx-auto mt-7 h-px w-44 overflow-hidden bg-border"><div className="splash-line h-full bg-primary" /></div></div>
      </div>
      <main>
        <section className="relative min-h-[94svh] overflow-hidden pt-24">
          <div className="absolute inset-y-0 right-0 w-full md:w-[54%]">
            {portraits.map((image, index) => <img key={image} src={image} alt={index === 0 ? "Nigerian beauty portrait wearing a warm atelier look" : ""} width={1024} height={1536} className="portrait-cycle absolute inset-0 h-full w-full object-cover" />)}
            <div className="absolute inset-0 bg-gradient-to-r from-background via-background/45 to-transparent md:from-background/80 md:via-transparent" />
          </div>
          <div className="relative mx-auto flex min-h-[calc(94svh-6rem)] max-w-7xl items-end px-5 pb-16 sm:px-8 md:items-center md:pb-0">
            <div className="max-w-2xl">
              <p className="mb-5 text-xs font-semibold uppercase text-primary">Nigerian Atelier Edition</p>
              <h1 className="text-balance font-display text-6xl leading-[.9] sm:text-7xl lg:text-8xl">Makeup, imagined <em className="text-primary">on you.</em></h1>
              <p className="mt-7 max-w-lg text-base leading-relaxed text-foreground/75 sm:text-lg">Take or upload a portrait. Explore every shade, line and finish in real time—with an on-device formulation engine that stays fully offline.</p>
              <div className="mt-8 flex flex-wrap gap-3"><Button asChild size="lg" className="h-12 rounded-full px-7"><Link to="/pricing">Subscribe to Pro <ArrowRight /></Link></Button><Button asChild variant="outline" size="lg" className="h-12 rounded-full bg-background/70 px-7 backdrop-blur"><a href="#download">Download mirror</a></Button></div>
              <div className="mt-7"><StoreBadges /></div>
            </div>
          </div>
        </section>

        <section className="bg-foreground px-5 py-24 text-background sm:px-8 md:py-32">
          <div className="reveal-flow mx-auto max-w-7xl">
            <div className="mb-14 grid gap-6 md:grid-cols-2 md:items-end"><div><p className="text-xs font-semibold uppercase text-secondary">Studio simulator</p><h2 className="mt-3 max-w-xl text-5xl leading-none sm:text-6xl">Artistry in your hands.</h2></div><p className="max-w-md text-sm leading-relaxed text-background/65 md:justify-self-end">Move through shades and finishes. Every adjustment stays private on your device.</p></div>
            <div className="grid overflow-hidden rounded-[2.5rem] bg-background/5 p-3 shadow-soft md:grid-cols-[1.05fr_.95fr] md:p-5">
              <div className="relative min-h-[470px] overflow-hidden rounded-[2rem]">
                <img src={portraitTwo} alt="Interactive makeup simulation portrait" loading="lazy" width={1024} height={1536} className="h-full w-full object-cover" style={{ filter: `saturate(${.65 + (saturation[0] ?? 0) / 100}) contrast(${.9 + (intensity[0] ?? 0) / 500})` }} />
                <div className="absolute left-5 top-5 flex items-center gap-2 rounded-full bg-foreground/75 px-4 py-2 text-xs backdrop-blur"><ScanFace className="size-4 text-secondary" /> Landmarks active</div>
                <div className={`absolute inset-0 pointer-events-none ${shades[shade]} mix-blend-soft-light`} style={{ opacity: (intensity[0] ?? 0) / 220 }} />
              </div>
              <div className="flex flex-col p-5 sm:p-8">
                <div className="flex gap-2 overflow-x-auto pb-5">{categories.map((item) => <Button key={item} variant={item === category ? "secondary" : "ghost"} size="sm" className="rounded-full text-xs text-background hover:text-foreground" onClick={() => setCategory(item)}>{item}</Button>)}</div>
              <div className="mt-8"><p className="text-xs uppercase text-background/50">Shade spectrum · {category}</p><div className="mt-5 flex gap-3">{shades.map((item, index) => <Button key={item} variant="ghost" size="icon" aria-label={`Select shade ${index + 1}`} onClick={() => setShade(index)} className={`h-9 w-9 shrink-0 rounded-full p-0 ${item} ${shade === index ? "ring-2 ring-secondary ring-offset-4 ring-offset-foreground" : ""}`} />)}</div></div>
                <div className="mt-12 space-y-9"><Control label="Pigment saturation" value={saturation} onChange={setSaturation} /><Control label="Intensity" value={intensity} onChange={setIntensity} /></div>
                <label className="mt-10 flex cursor-pointer items-center justify-center gap-2 rounded-full border border-background/15 px-5 py-4 text-sm"><Camera className="size-4" /> Upload your portrait<input type="file" accept="image/*" className="sr-only" /></label>
              </div>
            </div>
          </div>
        </section>

        <section className="px-5 py-24 sm:px-8 md:py-36"><div className="mx-auto max-w-7xl">
          <div className="reveal-flow mx-auto max-w-3xl text-center"><p className="text-xs font-semibold uppercase text-primary">Built for true-to-you decisions</p><h2 className="mt-4 text-balance text-5xl leading-none sm:text-7xl">A private atelier, wherever you are.</h2></div>
          <div className="mt-20 grid gap-5 md:grid-cols-3">
            <Feature icon={<LockKeyhole />} title="Fully offline" copy="Face landmarks and makeup rendering stay on your device. Your portraits remain yours." />
            <Feature icon={<Sparkles />} title="Certified shade library" copy="Explore foundation, lip and eye pigments tuned for the depth and nuance of melanin-rich skin." />
            <Feature icon={<ScanFace />} title="Formulation engine" copy="Blend, layer and adjust pigment intensity with immediate, realistic visual feedback." />
          </div>
        </div></section>

        <section className="px-5 pb-24 sm:px-8 md:pb-36"><div className="reveal-flow mx-auto grid max-w-7xl gap-12 rounded-[3rem] bg-accent p-8 md:grid-cols-2 md:p-16">
          <div><p className="text-xs font-semibold uppercase text-primary">Personal or professional</p><h2 className="mt-3 text-5xl leading-none sm:text-6xl">Your mirror grows with your artistry.</h2><p className="mt-6 max-w-md text-muted-foreground">Keep a personal lookbook for life, or open a full client atelier with profiles, unlimited formulations and polished exports.</p><Button asChild className="mt-8 rounded-full px-7"><Link to="/pricing">Compare plans <ArrowRight /></Link></Button></div>
          <div className="rounded-[2rem] bg-card p-7"><p className="font-display text-3xl">Pro Atelier Studio</p><div className="mt-7 space-y-4">{["Client Mode Directory", "Private client profiles", "Unlimited shade formulations", "Studio-ready exports"].map((item) => <div className="flex items-center gap-3 text-sm" key={item}><span className="grid size-7 place-items-center rounded-full bg-primary text-primary-foreground"><Check className="size-4" /></span>{item}</div>)}</div></div>
        </div></section>
      </main>
    </PageShell>
  );
}

function Control({ label, value, onChange }: { label: string; value: number[]; onChange: (value: number[]) => void }) { return <div><div className="mb-3 flex justify-between text-xs uppercase"><span className="text-background/60">{label}</span><span className="text-secondary">{value[0] ?? 0}%</span></div><Slider value={value} onValueChange={onChange} /></div>; }
function Feature({ icon, title, copy }: { icon: React.ReactNode; title: string; copy: string }) { return <article className="reveal-flow rounded-[2rem] border border-border bg-card p-8"><div className="grid size-12 place-items-center rounded-full bg-accent text-primary">{icon}</div><h3 className="mt-14 text-3xl">{title}</h3><p className="mt-3 text-sm leading-relaxed text-muted-foreground">{copy}</p></article>; }