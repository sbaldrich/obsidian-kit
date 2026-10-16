const {DataViewUtils} = await cJS()
const {dueToday} = DataViewUtils.tasksFunctions(dv)

try {
    dueToday(input?.group || true)
} catch (error) {
    dv.paragraph(`>[!ERROR] Something went wrong
        ${error.message}
    `)
}
