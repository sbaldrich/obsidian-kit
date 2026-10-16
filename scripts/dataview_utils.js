class DataViewUtils {
    mappingFunctions(luxon) {
        const {DateTime, Duration} = luxon

        const today = DateTime.now().startOf('day')
        const never = DateTime.fromISO('1990-01-01')

        const mapWithMask = (n) => {
            if (n.mask) {
                let mask = n.mask.toString()
                mask = (mask.length === 1 ? '0' : '') + mask
                // console.log(`this is the mask: ${mask}`)
                // console.log(`The task is due on: ${DateTime.fromISO(today.toISODate().slice(0, 10 - mask.length) + mask)}`)
                // console.log(`The task was last done on : ${n.last}`)

                return {
                    note: n,
                    last: n.last || never,
                    due: DateTime.fromISO(today.toISODate().slice(0, 10 - mask.length) + mask),
                    ...n
                };
            }
            // console.log(`returning null for ${n.file.name}`)
            return null;
        };

        const mapWithDow = (n) => {
            if (n.dow) {
                const daysOfWeek = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
                const weekdayIndex = daysOfWeek.indexOf(n.dow.toLowerCase()) + 1;
                return {
                    note: n,
                    last: n.last || never,
                    due: today.set({weekday: weekdayIndex}),
                    ...n
                };
            }
            // console.log(`returning null for ${n.file.name}`)
            return null;
        };

        const mapWithDue = (n) => {
            if (n.due) {
                // console.log(`The task is due on: ${n.due}`)
                // console.log(`The task was last done on : ${n.last}`)

                return {
                    note: n,
                    last: n.last || never,
                    due: n.due,
                    ...n
                };
            }
            // console.log(`returning null for ${n.file.name}`)
            return null;
        };

        const mapWithPeriod = (n) => {
            if (n.period) {
                const dur = Duration.fromISO(n.period);
                const due = n.last ? n.last.plus(dur) : today;
                return {
                    note: n,
                    last: n.last || never,
                    due: due,
                    ...n
                };
            }
            // console.log(`returning null for ${n.file.name}`)
            return null;
        };

        const composeMappers = (mappers) => (n) => {
            for (let mapper of mappers) {
                try {
                    const result = mapper(n);
                    if (result !== null) {
                        return result;
                    }
                } catch (error) {
                    console.warn(`Can't apply mappers to '${n.file.path}'`, error);
                    throw new Error(
                        `Error: '${error.message}'
        File: '${n.file.name}'`);
                }
            }
            console.warn(`No mapper applied for task ${n.file.name}`)
            return null;
        };

        return {
            mapWithMask,
            mapWithDow,
            mapWithPeriod,
            mapWithDue,
            composeMappers,
            defaultTaskMapper: composeMappers([mapWithMask, mapWithDow, mapWithDue, mapWithPeriod]),
            today,
            never
        }
    };

    tasksFunctions(dv) {

        const {DateTime} = dv.luxon
        const {
            today,
            never,
            defaultTaskMapper: mapper,
        } = this.mappingFunctions(dv.luxon)

        const filterTasks = (taskFilter, group = true) => {
            return dv.pages('#task and "projects/actions" and -#test and -"projects/actions/archive" and -#ktlo')
                .map(mapper)
                .filter(n => n !== null)
                .filter(taskFilter)
                .map(r => [
                    (group && r.category) || '',
                    r.note.file.link,
                    // r.due.toLocaleString(DateTime.DATE_MED_WITH_WEEKDAY),
                    `<code class="mb-input mb-input-inline"><!----><div class="mb-input-wrapper mb-input-type-date" data-internal-value='"${r.due.toISODate()}"'><input type="date" value="${r.due.toISODate()}" disabled></div></code>`,
                    // r.last === never ? null : r.last.toLocaleString(DateTime.DATE_MED_WITH_WEEKDAY),
                    `\`INPUT[date:${r.note.file.path}#last]\``
                ])
                .values
                .reduce((acc, cur) => {
                    const [category, ...rest] = cur
                    if (!acc[category]) {
                        acc[category] = [];
                    }
                    acc[category].push(rest);
                    return acc;
                }, {})
        }

        const outputTaskTable = (tasks, header) => {
            dv.header(4, header)

            Object.entries(tasks)
                .sort((a, b) => a[0] > b[0] ? 1 : -1)
                .forEach(([category, tasks]) => {
                    if (!!category) {
                        dv.header(6, category)
                    }
                    dv.table(
                        ['Task', 'Due', 'Last'],
                        tasks
                    )
                })
        }

        const dueToday = (group = true) => {

            const filteredTasks = filterTasks(r =>
                r.note.status === 'active' &&
                r.last < r.due &&
                r.due <= today
            )

            outputTaskTable(filteredTasks, "Due Today")

        }

        const dueSoon = (group) => {
            const filteredTasks = filterTasks(r =>
                    r.last < r.due &&
                    r.due > today &&
                    r.due <= today.plus({days: 5})
                , group)

            outputTaskTable(filteredTasks, "Due Soon")
        }

        const upcomingBirthdays = () => {
            const year = today.year
            const people = dv.pages('"projects/people"')
                .sort(p => p.birth_date)
                .filter(p => {
                    const birthday = DateTime.fromISO(`${year}-${p.birth_date}`)
                    const delta = today.diff(birthday, ['days']).days
                    return p.last < birthday && delta >= -8 && delta < 4
                })
                .map(n => {
                    const birthday = DateTime.fromISO(`${year}-${n.birth_date}`)
                    const delta = today.diff(birthday, ['days']).days
                    const annotation = delta > 0 ? '❗' : delta === 0 ? '🎈' : ''
                    const when = `${annotation} ${n.birth_date} ${annotation}`
                    return [n.file.link, when]
                })

            dv.header(2, "Past and Upcoming Birthdays")

            dv.table(['Who', 'When'], people)
        }
        return {
            dueToday,
            dueSoon,
            upcomingBirthdays,
            filterTasks,
            rawTasks: () => dv.pages('#ktlo and "projects/actions" and -#test and -"projects/actions/archive"').map(mapper)
        }
    };

}