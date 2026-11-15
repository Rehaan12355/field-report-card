import { recolorRibbon, ribbon, ribbonKey } from "./charts";
import type { Field, Meta, Plan } from "./types";

/** The field's story: a short, captioned sequence that plays when a field is
 *  opened, walking through what the satellites saw and what each plan would
 *  change. Every sentence is built from the field's own record. */

type Scene = {
  seconds: number;
  caption: string;
  /** Called when the scene starts, to set up what is on screen. */
  show: (stage: Stage) => void;
};

type Stage = {
  root: HTMLElement;
  visual: HTMLElement;
  grades: HTMLElement;
};

let stop: (() => void) | null = null;
let sound = false;

const round = (x: number) => Math.round(x);
const weeks = (x: number) => `${round(x)} ${round(x) === 1 ? "week" : "weeks"}`;
const lowerFirst = (s: string) => s.charAt(0).toLowerCase() + s.slice(1);

function gradeChips(...plans: Plan[]): string {
  return plans
    .map((p, i) => `${i ? `<span class="story-to">to</span>` : ""}<b class="grade-block grade-${p.grade}">${p.grade}</b>`)
    .join("");
}

function scenes(field: Field, meta: Meta): Scene[] {
  const [current, cover, rotation] = field.plans;
  const years = field.years;
  const c = current.counts;
  const showRibbon = (stage: Stage, plan: Plan, extra = "") => {
    const existing = stage.visual.querySelector<HTMLElement>(".ribbon");
    if (existing) recolorRibbon(existing, field, plan, meta);
    else stage.visual.innerHTML = ribbon(field, plan, meta) + ribbonKey(cover);
    stage.root.dataset.mode = extra;
  };
  const list: Scene[] = [
    {
      seconds: 5.5,
      caption: `This field is ${round(field.ha)} hectares. ${current.rationale.replace("What the field has been doing:", `From ${years[0]} to ${years[years.length - 1]} it grew`)}`,
      show: (stage) => {
        stage.root.dataset.mode = "";
        stage.grades.innerHTML = "";
        stage.visual.innerHTML = `<ol class="story-crops">${years
          .map((y, yi) => {
            const crop = meta.crops[String(current.crops[yi])];
            return `<li><i style="background:${crop.color}"></i><span class="num">${y}</span><b>${crop.name}</b></li>`;
          })
          .join("")}</ol>`;
      },
    },
    {
      seconds: 7,
      caption: `Here is every week, seen by NASA satellites. Each row is a year. Green is a growing crop. Brown is soil with no green cover: about ${weeks(c.bare)} a year.`,
      show: (stage) => {
        stage.visual.innerHTML = "";
        showRibbon(stage, current, "reveal");
      },
    },
    {
      seconds: 5.5,
      caption:
        c.exposed >= 0.5
          ? `Red marks the weeks when heavy rain fell on that open soil: about ${round(c.exposed)} a year. That is when soil is most at risk.`
          : `Blue ticks mark heavy-rain weeks. Almost none of them fell while this field was bare.`,
      show: (stage) => showRibbon(stage, current, c.exposed >= 0.5 ? "exposed" : ""),
    },
    {
      seconds: 4.5,
      caption: `Together with its crop variety, that earns a grade of ${current.grade}. The grade is a screening tool, not a soil test.`,
      show: (stage) => {
        showRibbon(stage, current);
        stage.grades.innerHTML = gradeChips(current);
      },
    },
    {
      seconds: 7,
      caption:
        cover.counts.bare < c.bare - 0.5
          ? `Plan one: add a cover crop after harvest. Bare weeks fall from ${round(c.bare)} to ${round(cover.counts.bare)} a year, and the grade moves to ${cover.grade}. The trade-off: it ${lowerFirst(cover.water.note)}`
          : `Plan one: add a cover crop. This field has few bare weeks a cover crop could fill, so little changes.`,
      show: (stage) => {
        showRibbon(stage, cover);
        stage.grades.innerHTML = gradeChips(current, cover);
      },
    },
    {
      seconds: 7,
      caption: `Plan two: change the rotation. ${rotation.rationale} The grade would be ${rotation.grade}.`,
      show: (stage) => {
        showRibbon(stage, rotation);
        stage.grades.innerHTML = gradeChips(current, rotation);
      },
    },
    {
      seconds: 5,
      caption: `Three plans to weigh against water, cost and income. ${current.review}`,
      show: (stage) => {
        stage.root.dataset.mode = "";
        stage.grades.innerHTML = "";
        stage.visual.innerHTML = `<ul class="story-plans">${field.plans
          .map(
            (p) => `<li><b class="grade-chip grade-${p.grade}">${p.grade}</b><span>${p.title}
              <small>${weeks(p.counts.bare)} bare a year, ${round(p.counts.exposed)} in heavy rain</small></span></li>`,
          )
          .join("")}</ul>`;
      },
    },
  ];
  return list;
}

export function stopStory(): void {
  stop?.();
  stop = null;
}

/** Play the story inside the card, then call onDone. */
export function playStory(card: HTMLElement, field: Field, meta: Meta, onDone: () => void): void {
  stopStory();
  const list = scenes(field, meta);
  const lastYear = field.years[field.years.length - 1];
  const latest = meta.crops[String(field.plans[0].crops[field.years.length - 1])];
  const canSpeak = "speechSynthesis" in window;
  card.innerHTML = `<div class="story" data-mode="">
    <div class="card-top">
      <p class="note">${round(field.ha)} hectares, ${latest.name.toLowerCase()} in ${lastYear}</p>
      <button type="button" class="button button-quiet" data-close>All fields</button>
    </div>
    <div class="story-bar" aria-hidden="true">${list.map(() => "<span><i></i></span>").join("")}</div>
    <div class="story-grades"></div>
    <p class="story-caption" aria-live="polite"></p>
    <div class="story-visual"></div>
    <div class="story-controls">
      <button type="button" class="button button-quiet" data-story="toggle">Pause</button>
      ${canSpeak ? `<button type="button" class="button button-quiet" data-story="sound" aria-pressed="${sound}">Read aloud</button>` : ""}
      <button type="button" class="button" data-story="skip">Skip to the report card</button>
    </div>
  </div>`;
  card.scrollTop = 0;
  const root = card.querySelector(".story") as HTMLElement;
  const stage: Stage = {
    root,
    visual: root.querySelector(".story-visual") as HTMLElement,
    grades: root.querySelector(".story-grades") as HTMLElement,
  };
  const caption = root.querySelector(".story-caption") as HTMLElement;
  const bars = [...root.querySelectorAll<HTMLElement>(".story-bar i")];
  const toggle = root.querySelector('[data-story="toggle"]') as HTMLButtonElement;

  let index = -1;
  let elapsed = 0;
  let paused = false;
  let speaking = false;
  let last = performance.now();
  let frame = 0;
  let done = false;

  const say = (text: string) => {
    if (!canSpeak) return;
    speechSynthesis.cancel();
    speaking = false;
    if (!sound) return;
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.onend = u.onerror = () => (speaking = false);
    speaking = true;
    speechSynthesis.speak(u);
  };

  const go = (i: number) => {
    index = i;
    elapsed = 0;
    bars.forEach((b, k) => (b.style.transform = `scaleX(${k < i ? 1 : 0})`));
    caption.textContent = list[i].caption;
    // Restart the caption's entrance animation.
    caption.classList.remove("in");
    void caption.offsetWidth;
    caption.classList.add("in");
    list[i].show(stage);
    say(list[i].caption);
  };

  const finish = () => {
    if (done) return;
    done = true;
    cancelAnimationFrame(frame);
    if (canSpeak) speechSynthesis.cancel();
    root.removeEventListener("click", onClick);
    stop = null;
    onDone();
  };

  const tick = (now: number) => {
    if (done) return;
    const dt = (now - last) / 1000;
    last = now;
    if (!paused) elapsed += dt;
    const scene = list[index];
    bars[index].style.transform = `scaleX(${Math.min(elapsed / scene.seconds, 1)})`;
    // With read-aloud on, wait for the sentence to finish before moving on.
    if (elapsed >= scene.seconds && !speaking) {
      if (index === list.length - 1) return finish();
      go(index + 1);
    }
    frame = requestAnimationFrame(tick);
  };

  const onClick = (e: Event) => {
    const action = (e.target as HTMLElement).closest<HTMLElement>("[data-story]")?.dataset.story;
    if (action === "skip") finish();
    if (action === "toggle") {
      paused = !paused;
      toggle.textContent = paused ? "Play" : "Pause";
      if (canSpeak) paused ? speechSynthesis.pause() : speechSynthesis.resume();
    }
    if (action === "sound") {
      sound = !sound;
      (e.target as HTMLElement).closest("button")?.setAttribute("aria-pressed", String(sound));
      say(list[index].caption);
    }
  };
  root.addEventListener("click", onClick);

  stop = () => {
    done = true;
    cancelAnimationFrame(frame);
    if (canSpeak) speechSynthesis.cancel();
  };
  go(0);
  frame = requestAnimationFrame((now) => {
    last = now;
    tick(now);
  });
}
