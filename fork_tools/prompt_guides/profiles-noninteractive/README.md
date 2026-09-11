# Non-interactive profiles

Generated copies of `../profiles/*.system.md`. Each file is the original
text, unmodified, plus a short override notice before
`## Everyday interaction` and a `## Non-interactive operation` section at
the end.

Use these when a node or script consumes the reply directly and no human
can answer a question. Use the originals for interactive chat.

## Caller contract

- A reply beginning `CONFLICT:` is a hard stop. Show the line, generate
  nothing. It means the request cannot be satisfied by one image.
- A reply beginning `NEEDS INPUT:` should not occur. If one appears, treat
  it as a hard stop too; it is a profile miss, not a prompt.
