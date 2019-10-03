const toSnakeCase = (property) => property.replace(/\.?([A-Z]+)/g, '_$1').toLowerCase().replace(/^_/, '')

const objOrRef = (files, obj) => {
  if (obj.$ref) {
    return resolveSchema(files, obj.$ref)
  } else {
    return obj
  }
}

const resolveSchema = (files, $ref) => {
  $ref = $ref
    .replace('@v0.1', '')
    .replace('.json', '')

  return Object.entries(files).filter(([filename, schema]) => filename.replace('.json', '') === $ref)[0][1]
}

const compileSchema = (files, schema) => {
  function compile (schema) {
    return {
      ...schema,
      schema: schema.schema && objOrRef(files, schema.schema),
      items: schema.items && schema.items.map((item) => objOrRef(files, item)).map(compile)
    }
  }

  return compile(schema)
}

const createTable = (datasetName, cls) => {
  const tableName = `${datasetName}.${cls.id}`
  const columns = Object.entries(cls.schema.properties).map(makeColumn)

  return `CREATE TABLE ${tableName} (
${columns.map((line) => `  ${line}`).join(',\n')}
);`
}

const grantStatements = (completeSchema) => {
  return completeSchema.items
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
  toSnakeCase
}
