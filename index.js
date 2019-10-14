const fs = require('fs')
const path = require('path')

const util = require('./util')
const db = require('./db')

const filename = process.argv[2]
const datasetSchema = JSON.parse(fs.readFileSync(filename, 'utf8'))

const datasetName = datasetSchema.id

async function run () {
  const compiledSchema = await util.compileSchema(datasetSchema, path.dirname(filename))

  util.importData(datasetName, compiledSchema, process.stdin, db)
    .then(() => console.log('Done!'))
    .catch((err) => {
      console.error(`Error executing SQL queries: ${err.message}`)
    })
}

run()
