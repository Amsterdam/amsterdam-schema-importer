const fs = require('fs')
const path = require('path')
const axios = require('axios')

const util = require('./util')
const validate = require('./validate')

const SCHEMA_BASE_URL = 'https://ams-schema.glitch.me/'

const filename = process.argv[2]
const datasetSchema = JSON.parse(fs.readFileSync(filename, 'utf8'))

async function run () {
  const compiledSchema = await util.compileSchema(datasetSchema, path.dirname(filename))

  const amsSchemaUrl = `${SCHEMA_BASE_URL}schema`

  const response = await axios.get(amsSchemaUrl)
  const amsSchema = response.data

  const validator = await validate.createValidatorAsync(amsSchema)

  try {
    validator(compiledSchema)
    console.log('No errors found!')
  } catch (err) {
    console.error('Errors found:')
    console.error(err.errors)
  }

  // TODO: check data
}

run()
