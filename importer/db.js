const R = require('ramda')
const pgp = require('pg-promise')({
  capSQL: true
})

const util = require('./util')

const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:@localhost:5432/postgres'

const db = pgp(connectionString)

const DEFAULT_CRS = 28992

const makeMakeGeometry = (crs) => {
  const makeGeometry = (col) => {
    const geojson = col.value
    if (geojson) {
      return {
        toPostgres: () => pgp.as.format('ST_SetSRID(ST_GeomFromGeoJSON($1), $2)', [geojson, crs]),
        rawType: true
      }
    }
  }

  return makeGeometry
}

const createAndBulkImport = (createSql, tables, stream) => db.tx('transaction', async (tx) => {
  function nextBatch () {
    return new Promise((resolve, reject) => {
      stream.pull((err, batch) => {
        if (err) {
          reject(err)
        } else {
          resolve(batch)
        }
      })
    })
  }

  const columnSets = Object.fromEntries(tables.map((table) => ([
    `${table.schema}.${table.name}`,

    new pgp.helpers.ColumnSet(table.columns.map((column) => {
      let isGeometry = false
      let makeGeometry
      if (column === 'geometry') {
        isGeometry = true
        // TODO: accept "urn:ogc:def:crs:EPSG::4326"
        const crs = parseInt(table.crs.replace('EPSG:', '')) || DEFAULT_CRS
        makeGeometry = makeMakeGeometry(crs)
      }

      return {
        name: column, // in DB
        prop: column, // in source
        // TODO: use actual type, not the column name!
        ...(isGeometry ? {
          mod: ':raw',
          init: makeGeometry
        } : {})
      }
    }), {
      table: {
        schema: table.schema,
        table: table.name
      }})
  ])))

  await tx.any(createSql)

  return tx.sequence(async (index) => {
    const batch = await nextBatch()

    if (batch && batch.length) {
      const byTable = R.groupBy((row) => `${row.dataset}.${row.class}`, batch)

      const inserts = Object.entries(byTable)
        .map(([tableName, rows]) => {
          const columnSet = columnSets[tableName]

          if (!columnSet) {
            throw new Error(`Class encountered not defined in schema: ${tableName}`)
          }
          const insert = pgp.helpers.insert(rows, columnSet)
          return tx.none(insert)
        })

      return Promise.all(inserts)
    }
  })
})

module.exports = {
  db,
  createAndBulkImport
}
