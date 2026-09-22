# Assisted note taking protocol

Use this protocol when recording iterations of the coral reef surveying light water craft project. Each relevant project subfolder has its own `engineering_notes.md`. Start with the folder for the iteration being discussed; do not create entries for other folders until the maker describes that work.

## Before writing

1. Inspect the folder structure, any existing `engineering_notes.md`, and the files and images for the iteration. Read the current notes before editing so earlier entries and any later edits are preserved.
2. Ask the maker to describe the iteration in their own words. Stream of consciousness and dictation are fine. Ask only concise follow up questions needed to avoid a material misunderstanding, especially about measurements, dates, or the reason for a design choice.
3. Use the maker's account as the source for intent, reasoning, fabrication, and test results. Use assets to identify visible features and to point readers to evidence. An image can show geometry; it cannot establish why that geometry was chosen or whether it worked in use.

## Writing the entry

- Put `**Model created:** YYYY-MM-DD` directly below the file title, using the date the physical model or component was made. Use a more fitting noun than "Model" where needed. This is not the date the Markdown file was written. Keep the original creation date at the top when the model changes later.
- Give the initial account and each later physical change its own `## YYYY-MM-DD — short description` heading, dated when that work happened. For example, if rear ballast is added on 18 September to a model made on 15 September, keep `**Model created:** 2026-09-15` at the top and add a separate `## 2026-09-18 — Added rear ballast` entry. Record tests on their actual dates too, when known. Do not date past work with the day its notes were written or silently fold a later change into an earlier entry.
- If a work or test date is unknown, ask briefly when it matters. Otherwise write `Date not confirmed` for that work; do not invent a calendar date.
- Keep the maker's first person voice and degree of confidence. Organise and lightly edit dictated wording for grammar and clarity, but keep the reasoning close to what was said. Correct obvious transcription errors using context; ask when a correction would change the technical meaning.
- Use these sections as a starting structure: `### What I made and why`, `### Assumptions and uncertainties`, `### What I observed`, and `### Next tests`. Omit or rename a section when the account does not support it. Do not fill gaps with invented content.
- Describe the stage honestly: rough model, proof of concept, prototype, or tested design only when the maker's account supports that description. Avoid assessment prose and claims of success stronger than the evidence.
- Separate what the maker intended, what the assets visibly show, what was actually tested or observed, and what is estimated or planned. Mark important gaps with plain labels such as **Not specified** or **Unverified estimate**. Do not claim the maker failed to record something merely because it was not mentioned in the conversation.
- Preserve units, scale, and test conditions. If a calculation is useful, show its inputs and arithmetic, state its assumptions, and distinguish an estimate from a measured result. Clarify whether a load is added weight or total mass when that affects the conclusion.
- Link relevant local assets inline at the point where they help the reader, using relative Markdown links from `engineering_notes.md`. Use the asset's actual filename and a descriptive link label, such as `[isometric view](v1%20Assets/Iso%20View.png)`. Link a few directly useful views or models rather than listing every file. A link supports a visual description; it does not verify intent or performance.
- Record next tests only when the maker mentioned them or they follow directly from an identified uncertainty. Phrase additional suggestions as suggestions, not as tests already planned by the maker.

## After writing

Check that every link resolves, the entry reflects the maker's wording and uncertainty, calculations use the stated measurements, and earlier entries remain intact. Share the file location and ask at most a concise, material clarification if one remains. Update the entry when the maker provides the answer.
