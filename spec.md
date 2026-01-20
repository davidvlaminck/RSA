# spec for refactoring

## existing use case
fill google spreadsheets with report data, both from neo4j and from postGIS

## new use case
fill microsoft Excel spreadsheets with report data, mostly from arangoDB and some from postGIS.
the spreadsheets will be uploaded to OneDrive or SharePoint

## some requirements:
- the data source is arangoDB (mostly) and postGIS (some)
- the output format is Microsoft Excel spreadsheets
- the spreadsheets will be uploaded to OneDrive or SharePoint
- the process should be automated and scheduled
  * first at 3h01 AM every day the arangoDB data will be erased and reloaded from the API
  * then at 5 AM every day the spreadsheets will be generated and uploaded
  * the postGIS databade has its own schedule for syncing data from the source
- error handling and logging should be implemented
- when changing the query's from any to AQL, the columns in the spreadsheets should be adjusted accordingly so that the fixed column for comments is always the last column
- the code should be automatically updated from a git repository and ran
  * this means it's better if the code is imported as a module so it's filebased and can be updated easily
