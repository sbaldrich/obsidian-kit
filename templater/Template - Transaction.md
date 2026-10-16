---
register: false
---
<%*
tR = '';
// 1. Find all Financial Movement notes
const files = tp.app.vault.getMarkdownFiles();
const metadataCache = tp.app.metadataCache;

const financialMovements = [];
for (const f of files) {
    const cache = metadataCache.getFileCache(f);
    const fm = cache?.frontmatter;
    if (fm && fm.category === "[[Financial Movements]]") {
        financialMovements.push({
            name: f.basename,
            file: f,
            frontmatter: fm
        });
    }
}

if (financialMovements.length === 0) {
    throw new Error("No Financial Movement notes found. Please create one first.");
}

// 2. Suggest which Financial Movement to clone from
const selected = await tp.system.suggester(
    m => m.name,
    financialMovements,
    false,
    "Clone transaction from...",
    10
);

if (!selected) {
    throw new Error("No Financial Movement selected.");
}

const frontmatter = selected.frontmatter;

// 3. Extract defaults from selected Financial Movement note
const defaults = {
    amount: frontmatter.amount || '',
    payee: frontmatter.payee || '',
    method: frontmatter.method || '',
    type: frontmatter.type || 'expense',
    currency: frontmatter.currency || 'EUR',
    date: tp.date.now("YYYY-MM-DD")
};

// 4. Prompt with defaults (user can modify)
const date = await tp.system.prompt('Date (YYYY-MM-DD)', defaults.date);
const amount = await tp.system.prompt('Amount', defaults.amount.toString(), false, false);

// Handle payee - it might already be a wikilink
let payee = defaults.payee;
if (payee && !payee.startsWith('[[')) {
    payee = `[[${payee}]]`;
}

const method = await tp.system.suggester(
    ["Cash", "Credit Card", "Debit Card", "Transfer", "Check"],
    ["cash", "credit", "debit", "transfer", "check"],
    false,
    `Method (default: ${defaults.method})`,
    10
) || defaults.method;

const type = await tp.system.suggester(
    ["Expense", "Income", "Transfer", "Loan"],
    ["expense", "income", "transfer", "loan"],
    false,
    `Type (default: ${defaults.type})`,
    10
) || defaults.type;

// 5. Set parent to selected Financial Movement note
const parentLink = `[[${selected.name}]]`;
-%>
---
category: "[[Financial Transactions]]"
created: <%tp.date.now()%>
parents:
  - "<%parentLink%>"
date: <%date%>
amount: <%amount%>
currency: <%defaults.currency%>
payee: "<%payee%>"
method: <%method%>
type: <%type%>
status: pending
tags:
  - transaction
---
<%*
// 6. Create year/month folder structure and generate MMDD - Parent Name
async function ensureFolder(path) {
    if (!(await app.vault.adapter.exists(path))) {
        await app.vault.adapter.mkdir(path);
    }
}

// Get date parts from transaction date
const transactionDate = moment(date);
const year = transactionDate.format('YYYY');
const month = transactionDate.format('MM');
const day = transactionDate.format('DD');
const mmdd = month + day; // e.g., "0112" for Jan 12

// Set folder paths
const baseFolder = "projects/transactions";
const yearFolder = `${baseFolder}/${year}`;
const monthFolder = `${yearFolder}/${year}${month}`;

// Ensure folders exist
await ensureFolder(yearFolder);
await ensureFolder(monthFolder);

// Generate filename: MMDD - Parent Name
const filename = `${mmdd} - ${selected.name}`;

// Rename and move
await tp.file.rename(filename);
await tp.file.move(`${monthFolder}/${filename}`);
-%>
## Notes
