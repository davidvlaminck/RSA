refactoring requirements

momenteel gebruikt dit project als output Google spreadsheets
dit moet herwerkt worden zodat de dit ook met Excel kan werken.
De excels zouden dan mogelijk van een OneDrive of Sharepoint moeten komen en ook terug geüpload worden ipv rechtstreeks sheets aan te passen zoals nu
De opmaak van de excel kan dan lokaal gebeuren ipv online

Ik wil een robuuste en duidelijk refactoring, met OOP principes zien, met een duidelijke structuur en extensie mogelijkheden

de rapporten run mag NOOIT falen, er moet altijd een retry mechanisme zijn met logging die na x aantal keren de logs upload naar een centrale locatie (bv. een S3 bucket of een andere cloud opslag)
de run moet instelbaar zijn qua tijdswindow, zoals nu
er moet ook gemail worden

de datasource kan arango of postgis zijn en moet onafhankelijk van elkaar werken


