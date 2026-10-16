<%*const tags = Object.entries(app.metadataCache.getTags())
				    .map(it => it[0])
				    .filter(it => it.startsWith("#review"))
				    .map(it => `"${it}"`)
await tp.user.updateReviewTags({tags: tags})
new Notice("Finished refining SRS review tags", 1000)
-%> 
