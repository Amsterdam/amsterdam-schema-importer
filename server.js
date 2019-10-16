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

const dataPath = path.join(__dirname, 'data')

const port = process.env.PORT || 8765
const workerUrl = process.env.WORKER_URL || 'http://localhost:8766/mapfiles'

app.use(express.static(path.join(__dirname, 'public')))
app.use(fileUpload())
app.use(cors())
app.set('json spaces', 2)

const schemasBaseUrl = 'https://ams-schema.glitch.me/dataset/'

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
  } catch (err) {
    res.status(500).send(`Error compiling schema: ${err.message}`)
    return
  }

  try {
    const response = await axios({
      url: workerUrl,
      method: 'POST',
      data: compiledSchema
    })

    const mapfileDir = path.join(__dirname, 'mapserver')
    const mapfileFilename = path.join(mapfileDir, `asbestdaken.daken.map`)
    const mapfile = response.data
    fs.writeFileSync(mapfileFilename, mapfile, 'utf8')
  } catch (err) {
    console.error(`Error sending data to worker: ${err.message}`)
    res.status(500).send(err.message)
    return
  }

  try {
    await util.importData(datasetId, compiledSchema, objectStream, db)
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

app.get('/check-schema/:datasetId', async (req, res) => {
  const datasetId = req.params.datasetId

  // URL of dataset JSON metadata file
  const datasetBaseUrl = schemasBaseUrl + datasetId + '/'
  const datasetUrl = datasetBaseUrl + datasetId

  let schema
  try {
    const response = await axios.get(datasetUrl)
    schema = response.data
  } catch (err) {
    res.status(err.response.status).send(err.response.statusMessage)
  }

  try {
    const compiledSchema = await util.compileSchema(schema, datasetBaseUrl)
    // util.validate

    res.send(compiledSchema)
  } catch (err) {
    res.status(500).send(err.message)
  }
})

app.get('/:datasetId/:classId', async (req, res) => {
  const datasetId = req.params.datasetId
  const classId = req.params.classId

  const query = `
  SELECT *, ST_AsGeoJSON(ST_Transform(geometry, 4326)) AS geometry
  FROM $1~.$2~`

  try {
    const rows = await db.db.any(query, [datasetId, classId])
    res.send({
      type: 'FeatureCollection',
      features: rows.map((row) => ({
        type: 'Feature',
        properties: {
          ...row,
          geometry: undefined
        },
        geometry: JSON.parse(row.geometry)
      }))
    })
  } catch (err) {
    res.status(500).send(err.message)
  }
})

app.listen(port, () => console.log(`Amsterdam Schema Importer listening on port ${port}!`))
