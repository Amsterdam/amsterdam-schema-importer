const fs = require('fs')
const path = require('path')
const H = require('highland')
const axios = require('axios')

const toSnakeCase = (property) => property.replace(/\.?([A-Z]+)/g, '_$1').toLowerCase().replace(/^_/, '')

const importData = async (datasetName, compiledSchema, objectStream, db) => {
  const classes = compiledSchema.classes

  const queries = classes.map((cls) => createTable(datasetName, cls))
  const grants = grantStatements(compiledSchema)

  const tables = classes.map((cls) => ({
    schema: datasetName,
    name: cls.id,
    crs: cls.crs || compiledSchema.crs,
    columns: Object.keys(cls.schema.properties)
  }))

  const createSql = `
    DROP SCHEMA IF EXISTS ${datasetName} CASCADE;
    CREATE SCHEMA ${datasetName};

    ${queries.join('\n\n')}
    ${grants.join('\n')}
  `

  const objects = H(objectStream)
    .split()
    .compact()
    .map(JSON.parse)
    .batch(100)

  try {
    const result = await db.createAndBulkImport(createSql, tables, objects)
    return result
  } catch (err) {
    throw err
  }
}

const objOrRef = async (obj, basePath, isUrl) => {
  if (obj.$ref) {
    const schema = await resolveSchema(obj.$ref, basePath, isUrl)
    return schema
  } else {
    return obj
  }
}

const resolveSchema = async ($ref, basePath, isUrl) => {
  if (isUrl) {
    $ref = $ref
      .replace('@v0.1', '')
      .replace('.json', '')
  } else {
    $ref = $ref
      .replace('@v0.1', '')
    $ref = $ref.endsWith('.json') ? $ref : $ref + '.json'
  }

  const schema = await fetchSchema($ref, basePath, isUrl)
  return schema
}

const fetchSchema = async (filePath, basePath, isUrl) => {
  let filename
  if (isUrl) {
    try {
      filename = basePath + filePath
      const response = await axios.get(filename)
      return response.data
    } catch (err) {
      throw new Error(`Can't open URL: ${filename}`)
    }
  } else {
    try {
      filename = path.join(basePath, filePath)
      return JSON.parse(fs.readFileSync(filename, 'utf8'))
    } catch (err) {
      throw new Error(`Can't open file: ${filename}`)
    }
  }
}

const compileSchema = async (schema, basePath) => {
  let isUrl
  try {
    const url = new URL(basePath)
    if (url.protocol === 'http:' || url.protocol === 'https:') {
      isUrl = true
    } else {
      throw new Error(`Invalid path/URL: ${basePath}`)
    }
  } catch (err) {
    // basePath is a relative file path
    isUrl = false
  }

  async function compile (s) {
    const schema = s.schema && await objOrRef(s.schema, basePath, isUrl)
    let classes
    try {
      if (s.classes) {
        classes = []
        for (const itemOrRef of s.classes) {
          const item = await objOrRef(itemOrRef, basePath, isUrl)
          const compiledItem = await compile(item)
          classes.push(compiledItem)
        }
      }
    } catch (err) {
      throw err
    }

    return {
      ...s,
      schema,
      classes
    }
  }

  try {
    const compiledSchema = await compile(schema)
    return compiledSchema
  } catch (err) {
    throw err
  }
}

const createTable = (datasetName, cls) => {
  const tableName = `${datasetName}.${cls.id}`
  const columns = Object.entries(cls.schema.properties).map(makeColumn)

  return `CREATE TABLE ${tableName} (
${columns.map((line) => `  ${line}`).join(',\n')}
);`
}

const grantStatements = (completeSchema) => {
  return completeSchema.classes
    .map((cls) => {
      return Object.entries(cls.schema.properties)
        .map(([property, value]) => {
          if (value.auth) {
            // TODO: all members of auth array
            let to = value.auth[0]
            if (to === 'public') {
              to = 'PUBLIC'
            }

            return `GRANT SELECT(${toSnakeCase(property)}) ON ${completeSchema.id}.${cls.id} TO ${to};`
          }
        })
    }).flat()
}

const tableNameFromUri = (uri) => uri.split('/')
  .slice(-2).join('.')
  .replace('.objects', '')
  .replace('@v0.1', '')

const makeColumn = ([key, value]) => {
  let pgType

  if (value.type === 'number') {
    pgType = 'double precision'
  } else if (value.type === 'integer') {
    pgType = 'integer'
  } else if (value.type === 'boolean') {
    pgType = 'boolean'
  } else if (value.type === 'array') {
    pgType = 'text []'
  } else if (value.type === 'object') {
    pgType = 'jsonb'
  } else if (value.type === 'string') {
    if (value.format === 'date-time') {
      pgType = 'timestamp with time zone'
    } else if (value.format === 'date') {
      pgType = 'date'
    } else if (value.format === undefined) {
      pgType = 'text'
    }
  } else if (value.$ref === 'https://ams-schema.glitch.me/schema@v0.1#/definitions/id') {
    pgType = 'text PRIMARY KEY'
  } else if (value.$ref === 'https://ams-schema.glitch.me/schema@v0.1#/definitions/class') {
    pgType = 'text'
  } else if (value.$ref === 'https://ams-schema.glitch.me/schema@v0.1#/definitions/dataset') {
    pgType = 'text'
  } else if (value.$ref === 'https://geojson.org/schema/Geometry.json') {
    pgType = 'geometry'
  } else if (value.$ref === 'https://geojson.org/schema/Point.json') {
    pgType = 'geometry'
  } else if (value.$ref === 'https://geojson.org/schema/Polygon.json') {
    pgType = 'geometry'
  } else if (value.$ref === 'https://ams-schema.glitch.me/schema@v0.1#/definitions/year') {
    pgType = 'integer'
  } else if (value.$ref === 'https://ams-schema.glitch.me/schema@v0.1#/definitions/uri') {
    if (value['ams.$ref.class']) {
      const tableName = tableNameFromUri(value['ams.$ref.class'])
      pgType = `text REFERENCES ${tableName}(id)`
    }
  }

  if (!pgType) {
    throw new Error(`Can't Postgressify ${JSON.stringify(value)}`)
  }

  return `${toSnakeCase(key)} ${pgType}`
}

module.exports = {
  compileSchema,
  createTable,
  grantStatements,
  toSnakeCase,
  importData
}
