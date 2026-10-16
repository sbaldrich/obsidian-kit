---
register: true
---
<%*
tR = '';
const pattern = await tp.user.util.suggestByCategory(
	tp,
	"Techniques",
	"Pattern..."
)

const problem = await tp.user.util.suggestByCategory(
	tp,
	"Coding Tasks",
	"Problem..."
)

const newTitle = `Study Session [${pattern}]`;

await tp.user.util.moveToEventDirectory(tp, newTitle)

let frontmatter = `---
category: "[[Study Session]]"
type: "[[Data Structures and Algorithms]]"
start: ${tp.date.now()}
patterns:
- "[[${pattern}]]"
problems:
- "[[${problem}]]"
status: started
`;

frontmatter += `---\n`;

tR += frontmatter;
-%>

### Phase 1: Attempt (20 mins)

- [ ] Read the problem
- [ ] Identify brute force idea
- [ ] Spot candidate pattern
- [ ] Sketch invariant / complexity
- [ ] Time check @ 20 min → stop attempt

### Phase 2: Analysis (<10 mins)

*Note down what the key insights for solving were, check the editorial if you weren't able to solve the problem.*

#### Key invariant / idea:

#### Optimal Complexity: 

#### Gotchas:

### Flashcards

>*Create cloze or Q/A flashcards if applicable*

>[!TIP] Creating Flashcards
> Syntax for creating flashcards can be found in the [Spaced Repetition Docs](https://www.stephenmwangi.com/obsidian-spaced-repetition/flashcards/flashcards-overview/)

