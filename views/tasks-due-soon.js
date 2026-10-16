const {DataViewUtils} = await cJS()
const {dueSoon} = DataViewUtils.tasksFunctions(dv)

dueSoon(input?.group || false)