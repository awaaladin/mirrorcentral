import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { ArrowRight, Check, Columns2, LockKeyhole, PenLine, ScanFace, Sparkles, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { PageShell, StoreBadges, MirrorMark } from "@/components/mirror-shell";
import { lashStyles, shadeCategories, shadeCount } from "@/lib/shades";
import { people, photoFor } from "@/lib/people";
import portraitOne from "@/assets/mirror-portrait-one.jpg";
import portraitTwo from "@/assets/mirror-portrait-two.jpg";
import portraitThree from "@/assets/mirror-portrait-three.jpg";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "mirror — Nigerian Atelier Makeup Simulator" },
    { name: "description", content: "Upload a portrait and try lips, foundation, eyes, lashes, blush and brows in shades made for deep skin tones. Face mapping runs on your phone." },
    { property: "og:title", content: "mirror — Nigerian Atelier Makeup Simulator" },
    { property: "og:description", content: "Face mapping and makeup preview that run on your phone, with shades made for deep skin tones." },
    { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
  ]}), component: HomePage,
});

const portraits = [portraitOne, portraitTwo, portraitThree];

function HomePage() {
  const [categoryIndex, setCategoryIndex] = useState(0);
  const [picked, setPicked] = useState<Record<string, number>>({ lips: 0 });
  const [saturation, setSaturation] = useState([55]);
  const [intensity, setIntensity] = useState([45]);
  const category = shadeCategories[categoryIndex]!;
  const shadeIndex = picked[category.id];
  const activeShade = shadeIndex === undefined ? undefined : category.shades[shadeIndex];
  const faces = people.filter((person) => photoFor(person));

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
              <p className="mt-7 max-w-lg text-base leading-relaxed text-foreground/75 sm:text-lg">Choose a portrait and mirror maps 468 points of the face on your phone, then paints lips, foundation, eyes, lashes, blush and brows in shades made for deep skin tones. The face mapping and preview work offline.</p>
              <div className="mt-8 flex flex-wrap gap-3"><Button asChild size="lg" className="h-12 rounded-full px-7"><Link to="/guide">See how it works <ArrowRight /></Link></Button><Button asChild variant="outline" size="lg" className="h-12 rounded-full bg-background/70 px-7 backdrop-blur"><a href="#download">Download mirror</a></Button></div>
              <div className="mt-7"><StoreBadges /></div>
            </div>
          </div>
        </section>

        <section className="bg-foreground px-5 py-24 text-background sm:px-8 md:py-32">
          <div className="reveal-flow mx-auto max-w-7xl">
            <div className="mb-14 grid gap-6 md:grid-cols-2 md:items-end"><div><p className="text-xs font-semibold uppercase text-secondary">Studio preview</p><h2 className="mt-3 max-w-xl text-5xl leading-none sm:text-6xl">The real shade library, try it here.</h2></div><p className="max-w-md text-sm leading-relaxed text-background/65 md:justify-self-end">These are the {shadeCount} shades in the app's Studio tabs, with their real names and finishes. This page tints a sample portrait; in the app, each layer is placed on your own photo using the face mesh.</p></div>
            <div className="grid gap-4 overflow-hidden rounded-[2.5rem] bg-background/5 p-3 shadow-soft md:grid-cols-[minmax(0,26rem)_1fr] md:gap-8 md:p-5">
              <div className="relative mx-auto aspect-[2/3] w-full max-w-md overflow-hidden rounded-[2rem]" style={{ isolation: "isolate" }}>
                <img src={portraitTwo} alt="Sample portrait for the shade preview" loading="lazy" width={1024} height={1536} className="h-full w-full object-cover" />
                {shadeCategories.map((layer) => {
                  const index = picked[layer.id];
                  const shade = index === undefined ? undefined : layer.shades[index];
                  if (!shade) return null;
                  const opacity = Math.min(0.8, layer.strength * ((intensity[0] ?? 0) / 50));
                  return layer.blobs.map((blob, blobIndex) => (
                    <div key={`${layer.id}-${blobIndex}`} aria-hidden="true" className="pointer-events-none absolute" style={{
                      left: `${blob.x}%`, top: `${blob.y}%`, width: `${blob.w}%`, height: `${blob.h}%`,
                      transform: `translate(-50%, -50%) rotate(${blob.rotate ?? 0}deg)`,
                      background: `radial-gradient(closest-side, ${shade.hex} 0%, ${shade.hex} 55%, transparent 100%)`,
                      mixBlendMode: layer.blend, opacity, filter: `saturate(${0.5 + ((saturation[0] ?? 0) / 100) * 0.9}) blur(3px)`,
                    }} />
                  ));
                })}
                <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full bg-foreground/75 px-4 py-2 text-xs backdrop-blur"><ScanFace className="size-4 text-secondary" /> Shade preview</div>
              </div>
              <div className="flex min-w-0 flex-col p-3 sm:p-6">
                <div className="flex gap-2 overflow-x-auto pb-5">{shadeCategories.map((item, index) => <Button key={item.id} variant={index === categoryIndex ? "secondary" : "ghost"} size="sm" className="shrink-0 rounded-full text-xs text-background hover:text-foreground" onClick={() => setCategoryIndex(index)}>{item.label}</Button>)}</div>
                <div className="mt-4">
                  <div className="flex items-baseline justify-between gap-4"><p className="text-xs uppercase text-background/50">Shade spectrum · {category.label}</p><p className="truncate text-xs uppercase text-secondary">{activeShade ? `${activeShade.name} · ${activeShade.finish}` : "None selected"}</p></div>
                  <div className="mt-5 flex flex-wrap gap-3">{category.shades.map((item, index) => <button key={item.name} type="button" aria-label={`${item.name}, ${item.finish}`} title={`${item.name} · ${item.finish}`} aria-pressed={shadeIndex === index} onClick={() => setPicked((current) => { const next = { ...current }; if (current[category.id] === index) delete next[category.id]; else next[category.id] = index; return next; })} className={`size-9 shrink-0 rounded-full border border-background/20 transition ${shadeIndex === index ? "ring-2 ring-secondary ring-offset-4 ring-offset-foreground" : ""}`} style={{ backgroundColor: item.hex }} />)}</div>
                  <p className="mt-4 text-xs text-background/50">Tap a selected shade again to remove it. In the app this layer follows {category.anchor}.</p>
                </div>
                <div className="mt-10 space-y-9"><Control label="Pigment saturation" value={saturation} onChange={setSaturation} /><Control label="Intensity" value={intensity} onChange={setIntensity} /></div>
                <div className="mt-10 border-t border-background/10 pt-6"><p className="text-xs uppercase text-background/50">Lashes · four styles</p><div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-2 text-sm">{lashStyles.map((style) => <p key={style.name}><span className="text-background">{style.name}</span> <span className="text-background/50">{style.note}</span></p>)}</div></div>
              </div>
            </div>
          </div>
        </section>

        <section className="px-5 py-24 sm:px-8 md:py-36"><div className="mx-auto max-w-7xl">
          <div className="reveal-flow mx-auto max-w-3xl text-center"><p className="text-xs font-semibold uppercase text-primary">What the Studio does</p><h2 className="mt-4 text-balance text-5xl leading-none sm:text-7xl">From one photo to a look you can keep.</h2></div>
          <div className="mt-20 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            <Feature icon={<ScanFace />} title="Face mapping on your phone" copy="MediaPipe's face landmarker finds 468 points plus the irises, on the device. It wants exactly one face and tells you plainly if it finds none or several." />
            <Feature icon={<Sparkles />} title={`${shadeCount} shades and four lash styles`} copy="Lips, foundation from Porcelain Fair to Deep Mystery Ebony, eyeshadow, eye colour, blush and brows. Every shade has a real finish: matte, satin, glossy or shimmer." />
            <Feature icon={<PenLine />} title="Your own shades" copy="Need a colour that is not in the library? Name it, type a hex code, and it is saved on your phone for any account." />
            <Feature icon={<Columns2 />} title="Honest before and after" copy="Drag across the photo to wipe between your original portrait and the makeup actually rendered on it." />
            <Feature icon={<Check />} title="Named, reopenable looks" copy="Save a look as Bridal Glam or anything else. Open it again later and keep editing, search your saved looks, or delete the ones you do not need." />
            <Feature icon={<LockKeyhole />} title="Private by design" copy="Your portrait is analysed and painted on the device. Only your account and the shade-list refresh use the internet, and the shade list has an offline copy built in." />
          </div>
        </div></section>

        {faces.length > 0 && (
          <section className="px-5 pb-24 sm:px-8 md:pb-32"><div className="mx-auto max-w-7xl">
            <div className="reveal-flow grid gap-8 md:grid-cols-[1fr_auto] md:items-end"><div><p className="text-xs font-semibold uppercase text-primary">The young team</p><h2 className="mt-3 max-w-2xl text-5xl leading-none sm:text-6xl">Shaped by students, built into an app.</h2></div><Button asChild variant="outline" className="rounded-full px-7"><Link to="/about">Meet the team <ArrowRight /></Link></Button></div>
            <div className="mt-12 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">{faces.map((person) => <Link key={person.slug} to="/about" hash={person.slug} className="reveal-flow group block"><div className="aspect-[3/4] overflow-hidden rounded-[1.75rem] bg-muted"><img src={photoFor(person)} alt={person.name} loading="lazy" className="size-full object-cover transition duration-500 group-hover:scale-[1.03]" /></div><p className="mt-3 font-display text-2xl">{person.name}</p><p className="text-xs uppercase text-muted-foreground">{person.role}</p></Link>)}</div>
          </div></section>
        )}

        <section className="px-5 pb-24 sm:px-8 md:pb-36"><div className="reveal-flow mx-auto grid max-w-7xl gap-12 rounded-[3rem] bg-accent p-8 md:grid-cols-2 md:p-16">
          <div><p className="text-xs font-semibold uppercase text-primary">Personal or professional</p><h2 className="mt-3 text-5xl leading-none sm:text-6xl">Your mirror grows with your artistry.</h2><p className="mt-6 max-w-md text-muted-foreground">Choose Personal or Pro / MUA when you sign up. Pro adds a Client Mode directory for bridal and editorial consultations, so each client has a card with notes and a place to start a look.</p><div className="mt-8 flex flex-wrap gap-3"><Button asChild className="rounded-full px-7"><Link to="/pricing">Compare plans <ArrowRight /></Link></Button><Button asChild variant="ghost" className="rounded-full px-7"><Link to="/guide">Read the guide</Link></Button></div></div>
          <div className="rounded-[2rem] bg-card p-7"><p className="flex items-center gap-3 font-display text-3xl"><Users className="size-6 text-primary" /> Pro / MUA</p><div className="mt-7 space-y-4">{["Client Mode directory", "Client cards with name, notes and a Self or Client tag", "Search clients by name or notes", "Start a look in the Studio from a client's card"].map((item) => <div className="flex items-center gap-3 text-sm" key={item}><span className="grid size-7 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground"><Check className="size-4" /></span>{item}</div>)}</div></div>
        </div></section>
      </main>
    </PageShell>
  );
}

function Control({ label, value, onChange }: { label: string; value: number[]; onChange: (value: number[]) => void }) { return <div><div className="mb-3 flex justify-between text-xs uppercase"><span className="text-background/60">{label}</span><span className="text-secondary">{value[0] ?? 0}%</span></div><Slider value={value} onValueChange={onChange} /></div>; }
function Feature({ icon, title, copy }: { icon: React.ReactNode; title: string; copy: string }) { return <article className="reveal-flow rounded-[2rem] border border-border bg-card p-8"><div className="grid size-12 place-items-center rounded-full bg-accent text-primary">{icon}</div><h3 className="mt-14 text-3xl">{title}</h3><p className="mt-3 text-sm leading-relaxed text-muted-foreground">{copy}</p></article>; }
