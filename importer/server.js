const fs = require('fs')
const path = require('path')
const axios = require('axios')
const nodeUtil = require('util')
const glob = nodeUtil.promisify(require('glob'))
const H = require('highland')
const express = require('express')
const cors = require('cors')
const fileUpload = require('express-fileupload')
const app = express()

const util = require('./util')
const db = require('./db')
const validate = require('./validate')

const mapfilePath = process.env.MAPFILE_DIRECTORY || path.join(__dirname, '..', 'mapserver')
const dataPath = process.env.DATA_DIRECTORY || path.join(__dirname, '..', 'data')
const port = process.env.PORT || 8080
const workerUrl = process.env.WORKER_URL || 'http://localhost:8766/mapfiles'
const SCHEMA_BASE_URL = 'https://ams-schema.glitch.me/'

app.use(express.static(path.join(__dirname, 'public')))
app.use(fileUpload())
app.use(cors())
app.set('json spaces', 2)

app.post('/import/:datasetId', async (req, res) => {
  const datasetId = req.params.datasetId
  const datasetPath = path.join(dataPath, datasetId)

  const files = await glob(path.join(datasetPath, '*.ndjson'))
  const readFile = H.wrapCallback(fs.readFile)
  const objectStream = H(files).map(readFile).merge()

  let compiledSchema
  try {
    const datasetSchema = JSON.parse(fs.readFileSync(path.join(datasetPath, `${datasetId}.dataset.schema.json`), 'utf8'))
    compiledSchema = await util.compileSchema(datasetSchema, datasetPath)

    const amsSchemaUrl = `${SCHEMA_BASE_URL}schema`
    const response = await axios.get(amsSchemaUrl)
    const amsSchema = response.data

    console.log('Creating validator:', amsSchema)
    const validator = await validate.createValidatorAsync(amsSchema)

    console.log('Validating:', compiledSchema)

    const result = validator(compiledSchema)
    console.log('Validation result:', result)

    // TODO: also validate data!
  } catch (err) {
    console.error('Sending internal server error 500:', err.message)
    if (err.name === 'ValidationException') {
      console.error(err.errors)
    }

    res.status(500).send({
      message: `Error compiling schema: ${err.message}`,
      errors: err.errors
    })

    return
  }

  try {
    const response = await axios({
      url: workerUrl,
      method: 'POST',
      data: compiledSchema
    })

    const mapfileFilename = path.join(mapfilePath, `${datasetId}.map`)
    const mapfile = response.data

    fs.writeFileSync(mapfileFilename, mapfile, 'utf8')
  } catch (err) {
    console.error(`Error sending data to worker: ${err.message}`)
    res.status(500).send(err.message)
    return
  }

  try {
    console.log('Starting import')
    await util.importData(datasetId, compiledSchema, objectStream, db)
    console.log('Importing successful!')
    res.send('Done')
  } catch (err) {
    console.error(err.message)
    res.status(500).send(`Error executing SQL queries: ${err.message}`)
  }
})

app.post('/upload/:datasetId', async (req, res, next) => {
  const datasetId = req.params.datasetId
  const datasetPath = path.join(dataPath, datasetId)

  try {
    fs.mkdirSync(datasetPath)
  } catch (err) {
    // Already exists!
  }

  if (!req.files || Object.keys(req.files).length === 0) {
    return res.status(400).send('No files were uploaded.')
  }

  for (const filename in req.files) {
    const file = req.files[filename]
    const filePath = path.join(datasetPath, filename)

    const mv = nodeUtil.promisify(file.mv)

    await mv(filePath)
  }

  res.send('Done')
})

app.listen(port, () => console.log(`Amsterdam Schema Importer listening on port ${port}!`))
