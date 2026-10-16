---
register: false
---
<%*
tR = '';
await tp.user.leet({n: await tp.system.prompt('Enter LC problem id', '',true)})
let output = await tp.system.clipboard();
console.log(output)
const [num, title] = output
  .split('\n')
  .find(line => line.trim() !== '')
  .replace("is on the run...", "")
  .replace(/\s*\[(\d+)\]\s*/, "$1 - ")
  .split(" - ")
  .map(t => t.trim())

const link = title.toLowerCase()
	.trim()
	.replace(/[^a-z ]+/, '')  
	.replaceAll(/[^a-z-]/g, '-')

output = output
  // Remove trailing brackets and numbers on a line
  .replace(/\s*\[(\d+)\]\s*.*/, "")
  // Trim empty lines at the beginning
  .replace(/^(?:\s*\r?\n)+/, '')
  // Wrap specific tokens in backticks
  .replaceAll(/((\S+\s*[^<>]=\s*(?:\[.*\]|\d+))|(?:\[.*\]))/g, "`$1`")
  // Add markdown headers for examples and constraints
  .replaceAll(/(Example\s.*:)/g, '### $1\n')
  .replaceAll(/(Constraints\s*:)/g, '### $1\n')
  // Wrap contiguous tab-indented lines in triple backticks
  .replaceAll(/((?:^\t.*(?:\r?\n|$))+)/gm, '```\n$1```')
  // Remove unwanted symbols
  .replaceAll(/¬†/gm, '')
  // Clean lines that contain only spaces or tabs (leave the newline)
  .replace(/^[ \t]+$/gm, '')
  // Replace three or more consecutive empty lines with two
  .replace(/\n(?:\s*\n){2,}/g, '\n\n');

const file = tp.file.find_tfile(tp.file.path(true))

await app.vault.modify(file, output) 
const filename = `${num.padStart(4, 0)} - ${title}`;
await tp.file.rename(filename)
await app.fileManager.processFrontMatter(file, 
	(frontmatter) => {
		 frontmatter["category"] = "[[Coding Tasks]]" 
		 frontmatter["last"] = tp.date.now("YYYY-MM-DD"); frontmatter["start"] = tp.date.now("YYYY-MM-DD"); frontmatter["source"] = '[[Leetcode]]';
		 frontmatter["link"] = `https://leetcode.com/problems/${link}`
		 frontmatter["solution"] = `[[${filename} - Solution]]`
});
-%>
