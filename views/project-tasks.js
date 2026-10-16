const thisNote = dv.current().file.link;
for (
	let group of
		dv.pages()
		   .where(p => p.status && p.project?.path === thisNote.path)
		   .groupBy(p => p.status)
	){
	dv.header(5, group.key);
	dv.table(["Task", "Start", "Last Updated"],
			 group.rows
				 .sort((p, q) => p.last <= q.last ? -1 : 1)
				 .map(r => [r.file.link, r.start, r.last]))
}

