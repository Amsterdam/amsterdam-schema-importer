# NDJSON + Amsterdam Schema ⟶ PostgreSQL tables + Data Services

A small prototype tool that reads Amsterdam Schema + NDJSON data, and creates the following services:

- GraphQL, using Hasura or Postgraphile,
- MapServer,
- A Node.js data upload and validation tool,
- A Mapfile generator,
- A REST API, using Flask.

## Usage

Run Hasura using Docker:

    docker-compose up

## Using the command line validator:

Finally, run the script with the example data & schema:

    awk 1 ./example-data/data/*.ndjson | node index.js ./example-data/schema/example.json

## Hasura

We can create many-to-many relations using PostgreSQL `ARRAY`s by creating a view:

~~~sql
CREATE VIEW example.steden_bezienswaardigheden AS
  SELECT id, UNNEST(heeft_bezienswaardigheden) AS bezienswaardigheid FROM example.steden
~~~

We can create geospatial functions and use them with Hasura:

~~~sql
CREATE FUNCTION example.steden_near(near_id text, distance integer)
RETURNS SETOF example.steden AS $$
    SELECT * FROM example.steden s
    WHERE ST_Distance(geography(s.geometry), geography((SELECT geometry FROM example.steden s where s.id = near_id))) <= distance AND
    s.id != near_id
$$ LANGUAGE sql STABLE;
~~~

~~~sql
CREATE FUNCTION example.steden_intersects(id text)
RETURNS SETOF example.steden AS $$
  SELECT * FROM example.steden
  WHERE
  --
  --
$$ LANGUAGE sql STABLE;
~~~

## Compliance

The REST API has been developed in compliance with the NL API standard. On top of that the following extensions have been added:

- Near search based op query parameters in the GET request.

See also:

- https://blog.hasura.io/graphql-schema-on-postgres-with-foreign-keys-and-without-foreign-keys-95f6b2715478/
- https://docs.hasura.io/1.0/graphql/manual/queries/custom-functions.html#
- https://docs.hasura.io/1.0/graphql/manual/schema/relationships/database-modelling/many-to-many.html
