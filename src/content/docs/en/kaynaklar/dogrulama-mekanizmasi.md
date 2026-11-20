---
title: "The Verification Mechanism — When Does a Page Go Stale?"
description: "What the `dogrulama` field standing in every page's header means, where its initial values were derived from, what it doesn't guarantee, and the three files of the mechanism that banners a stale page."
dogrulama: 2026-11-20
---

This site has version names, model names, prices and measured numbers. All four go stale. There's no way to hide the staleness; but there is a way to **show the staleness to the reader**, and this page explains it.

## Why Does Such a Field Exist

Two claim types are intertwined when a guide page is written:

- **Timeless claims:** "In LoRA the base model stays in memory", "an epoch is one pass over all the data". These are independent of the tool version.
- **Timely claims:** "Ollama 0.40.4", "vLLM v0.31.0", "`transformers` v5 removed `warmup_ratio`", "RunPod bills the network volume even while the pod is off". Each of these silently turns wrong when upstream changes.

This site's own credentials did exactly that in three days: the `ornekler/tekrarlanabilirlik` record ran with **Ollama 0.40.4** on October 17, the `ornekler/eminlik-olcu` record with **0.40.5** the same day's evening; the machine moved to **0.40.6** on October 19. I.e. even the version inside the sentence "this was measured on this machine" goes stale in two days — the numbers aren't wrong, they're incomplete the moment it isn't written which version's numbers they are.

The timeless/timely distinction had never been made on the site. Every page showed a three-month-old version name with the same certainty as if written yesterday. The `dogrulama` field is the only thing separating the two: **the page's header now gives a date answering "when were these claims last reviewed"**, and when the date's thresholds pass, a banner appears atop the page.

## What the Stamp Says, What It Doesn't Say

| The stamp says | The stamp doesn't say |
| --- | --- |
| The page's claims were **reviewed once** on that date. | That the claims are **still** true. The review date isn't proof of correctness. |
| This page had a content touch after that date. | What the touch was — adding an internal link also carries the stamp forward. |
| If a threshold is passed, the reader is warned. | That the site anywhere goes and **asks** "is this version still valid". There's no automatic upstream check. |
| Every page has a single stamp. | That every line on the page is the same age. On a site of over sixty pages, no per-line stamp is kept. |

:::caution[The stamp isn't a guarantee, it's a calendar]
The misreading would be: "the stamp is fresh, hence safe." Stamp freshness says only the *maintenance date*. Understanding whether a page's price or version name is really current still rests on two jobs: looking at the upstream doc and — as this site does — taking a run on your own machine.
:::

## The Mechanism Sits in Three Files

**1. The required field** — `src/content.config.ts`:

```ts
const verificationStamp = z
  .union([z.string(), z.date()])
  .transform((value) => (value instanceof Date ? localISO(value) : value.trim()))
  .refine((value) => /^\d{4}-\d{2}-\d{2}$/.test(value), {
    message: '`dogrulama` must be in YYYY-MM-DD form (e.g. 2026-10-19).',
  });

export const collections = {
  docs: defineCollection({
    loader: docsLoader(),
    schema: docsSchema({ extend: () => z.object({ dogrulama: verificationStamp }) }),
  }),
};
```

The field is **required**: a page without a stamp breaks `astro build`. This is the mechanism's fail-closed side — someone forgetting to write a new page can't silently publish an unstamped one.

**2. The banner** — `src/starlightRouteData.ts` (Starlight's route middleware):

```ts
const STALE_DAYS = 90;
const VERY_STALE_DAYS = 180;

// ...
} else if (days < VERY_STALE_DAYS) {
  text = `The claims on this page were last verified on <strong>${stamp}</strong> (${days} days ago). ...`;
} else {
  text = `This page hasn't been verified since <strong>${stamp}</strong> (${days} days). ...`;
}
entry.data.banner = { content: text };
```

The thresholds are arbitrary and deliberately high: 90 days is the "review again" warning, 180 days the "don't assume the numbers here are current" warning. For today (2026-10-19) no page exceeds either; the oldest stamp was four days prior.

**3. The audit script** — `scripts/dogrulama-kontrol.mjs`, run with `npm run dogrula`. Every page missing a stamp, with a broken format, or having **stamped itself into the future** is an error with exit code 1. Stale pages are by default only reported; with `--strict` they become an error. The distinction is deliberate: staleness is a normal state, an unstamped page is an error.

:::note[Why Starlight's own `lastUpdated` field wasn't used]
Starlight has a built-in `lastUpdated` field, appearing as a "last updated" line under the page. Its meaning is different: that's **the file's** being updated. Our stamp has to be the date **the claims** were reviewed; the two aren't the same thing — the founding section below is exactly where this difference was measured. The built-in field also produces no staleness warning.
:::

## Where the First Stamps Came From

This repo had no git history, i.e. the only objective answer to "when did this page last change" was the file's modification time. `scripts/dogrulama-baslat.mjs` wrote the mtime date as the stamp onto all 60 files existing at the time — after showing the plan with a dry run without `--yaz`. Since this page was added after that run, its own stamp (2026-10-19) comes not from the mtime but from the day it was genuinely written. The real distribution the audit script produced on the first run:

| Stamp | Pages | What was being done |
| --- | --- | --- |
| 2026-10-15 | 27 | The site skeleton + the depth phase (five batches) |
| 2026-10-16 | 11 | Speed/Cost, the 127.0.0.1 switch, agents, injection |
| 2026-10-17 | 14 | Inference parameters, reproducibility, licensing, embedding training |
| 2026-10-18 | 8 | The confidence page + internal links to seven pages |

:::caution[The distribution's known flaw]
In seven of the eight pages stamped 2026-10-18, that night's work was **adding internal links**; the claims weren't re-verified. On those seven pages the stamp says the claims were reviewed on October 18 — whereas what was reviewed was the links. The eighth page ([Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/)) is the exception: there the measurement records were looked at again that night and the wrong request counts (266 instead of 176 chat + 100 embedding) were corrected, i.e. that stamp rests on a claim review.
This flaw comes not from the mechanism but from what the mtime measures — and the justification for carrying the stamps by hand from now on is exactly this.
:::

:::note[The table is now history, not today's distribution]
The table shows the distribution the audit script wrote when the stamps were first pressed. On October 19 the version-credential fix above was made: twelve pages' stamps were moved to **2026-10-19**; then the scope map and concurrency pages were added. The script's second run that day printed `2026-10-15: 27 · 10-16: 5 · 10-17: 13 · 10-18: 3 · 10-19: 15`. That number too is a frozen snapshot — the only current thing is the `npm run dogrula` output.
:::

## The Runs Tested Today

The banner code had naturally never run, since no page passed the thresholds. That it works was verified with temporary files — no published page's stamp was touched and all seven test files were deleted as soon as the run finished.

**The build and banner side:**

| Run | Expectation | Measured output |
| --- | --- | --- |
| a page never stamped | the build breaks | `[InvalidContentEntryDataError] … data does not match collection schema.` and beneath it `> Required`; exit code 1 |
| stamp 2026-07-15 (96 days) | the 90-179 band's banner | `.sl-banner` printed: "The claims on this page were last verified on 2026-07-15 (96 days ago)..." |
| stamp 2026-04-01 (201 days) | the 180-and-above band's banner | "This page hasn't been verified since 2026-04-01 (201 days). Don't assume the numbers and version names here are current." |
| stamp 2026-10-19 (today, a negative control) | no banner | no `.sl-banner` element |

**The audit script side:**

| Run | Expectation | Measured output |
| --- | --- | --- |
| a single stale page, `npm run dogrula` | report, don't break the build | "Stale (>=90 days): 1" + "OK: every page has a valid stamp.", exit 0 |
| the same page, `npm run dogrula --strict` | staleness becomes an error | exit 1 |
| stamp 2027-01-01 (the future) | should be rejected | "ERROR: ... a future stamp (2027-01-01, 74 days ahead)", exit 1 |
| no stamp field | should be caught | "ERROR: ... no verification stamp", exit 1 |

The banner's place and readability were measured in the browser: it comes **before** the page's `<h1>` element, printing `rgb(27, 23, 64)` text on an `rgb(211, 204, 255)` background at 16 px; the test page's internal link goes to `/en/kaynaklar/dogrulama-mekanizmasi/` and the console was clean.

**The build times were also measured in this run:** producing 65 HTML took **7.84 s**, the second run **4.48 s**. The gap's cause isn't a guess but what the log says: because the schema changed, the first run did `[content] Content config changed → Clearing content store` and re-synced the content from scratch. The audit script scanned the freshly stamped 60-file set in **110 ms**; that's why it isn't embedded inside `astro build` but stands separately as `npm run dogrula`.

:::caution[YAML doesn't see the stamp as a string]
The first build attempt gave the error `dogrulama: Expected type "string", received "object"`. The cause isn't Turkish text or a typo: an unquoted `2026-10-19` is parsed as a **date** under YAML 1.1 rules and arrives at the schema as a `Date` object. `src/content.config.ts` therefore accepts the field as both a string and a `Date`, reducing both to a `YYYY-MM-DD` string. Result: writing the stamp quoted or unquoted is equivalent.
:::

:::note[The evidence's limit]
These runs show the banner **produces the right text in code**, not its timing. Waiting for the calendar date when a real page hits 90 days is required; the test dates were artificially pulled back and none remained on a published page. The verification was done from the browser surface via the DOM and computed style; a pixel screenshot couldn't be taken — how the banner wraps at narrow mobile widths wasn't measured in this run.
:::

## The Gaps This Mechanism Doesn't Cover

- **Upstream isn't probed.** The script touches no package site, price page or Ollama interface asking "is this still valid". Nor should it; if it did, that page would have started producing its own claims.
- **No per-line stamp.** A timeless concept page and a price table are warned with the same weight. The more correct thing is multiple stamps per page or a stamp per section; either doubles this site's maintenance load.

## Not Measured

- That the 90 and 180-day thresholds fit this site's staleness speed was **not measured** — it's a guess, not a measurement. The fit will be seen when the calendar genuinely fills 90 days, i.e. at the earliest on **2027-01-13** (the oldest stamp 2026-10-15). Until that date the mechanism stands verified with artificial dates, as in the table above.
- The **stamp fresh, claim wrong** state is outside this audit's scope. Since the mechanism verifies no claim by asking upstream, a stale page can look "fresh" while its schema and banner work flawlessly. Its rate can't be measured; and because it can't, it sits here.
- At which stage the unstamped page broke the build was seen with a single error message; that error's debuggability in a repo of hundreds of pages wasn't tested.
- Whether the banner actually makes the reader more careful was **not measured**; the only thing measured on the site is that the banner rendered and the console was clean.

## Related Pages

- [Local Setup](/en/donanim/yerel-kurulum/) — version pinning and the `pip freeze` habit; the stamp mechanism's counterpart on the reader's side.
- [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) — the measured source of the site's latency numbers; the most concrete example of the difference between "measured" and "reviewed".
- [Frequently Asked Questions](/en/kaynaklar/sss/) — the short answer to the question "how current is this guide".

## Sources and Further Reading

- [Starlight — Route Data](https://starlight.astro.build/guides/route-data/) — changing the per-page generated data with middleware; the channel used for printing the banner. (Last read: 2026-10-19.)
- [Starlight — Frontmatter](https://starlight.astro.build/reference/frontmatter/) — the shape of the built-in `banner` and `lastUpdated` fields and adding fields over `docsSchema`. (Last read: 2026-10-19.)
