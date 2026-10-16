dv.execute(`
    table
        start,
        last, 
        notes
    where
        project = this.file.link and
       !contains(file.name,"Template") and
       !contains(file.path, "archive/") and
       category = [[Events]]
    sort start desc
`)
