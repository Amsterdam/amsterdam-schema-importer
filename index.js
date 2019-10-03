const H = require('highland')
const fs = require('fs')
const path = require('path')

const util = require('./util')
const db = require('./db')

const files = Object.fromEntries(process.argv.slice(2)
  .map((filename) => ([
    path.basename(filename),
    JSON.parse(fs.readFileSync(filename, 'utf8'))
  ])))

const datasetSchema = Object.values(files).filter((schema) => schema.type === 'dataset')[0]
const datasetName = datasetSchema.id
const compiledSchema = util.compileSchema(files, datasetSchema)
const classes = compiledSchema.items

const queries = classes.map((cls) => util.createTable(datasetName, cls))
const grants = util.grantStatements(compiledSchema)

const tables = classes.map((cls) => ({
  schema: datasetName,
  name: cls.id,
  columns: Object.keys(cls.schema.properties)
}))

const createSql = `
  DROP SCHEMA IF EXISTS ${datasetName} CASCADE;
  CREATE SCHEMA ${datasetName};

  ${queries.join('\n\n')}
  ${grants.join('\n')}
`

const objects = H(process.stdin)
  .split()
  .compact()
  .map(JSON.parse)
  .batch(100)

db(createSql, tables, objects)
  .then(() => console.log('Done!'))
  .catch((err) => console.error(err.message))
