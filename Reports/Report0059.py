from DQReport import DQReport


class Report0059:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0059',
                               title='Er zijn geen assets die zichzelf direct of indirect voeden (geen lussen in voeding).',
                               spreadsheet_id='15z-3mTVmjg63EepO1uaN5R5dgFARcfiyrRBbXa3TzUQ',
                               datasource='Neo4J',
                               persistent_column='F')

        self.report.result_query = """
            MATCH p=(x:Asset {isActief: True})-[:Voedt*]->(x)
            WHERE all(n in nodes(p) WHERE NOT (n:UPSLegacy))
            WITH x, reduce(path_loop = [], n IN nodes(p) | path_loop + [[n.uuid, n.typeURI]]) as path_loop
            RETURN DISTINCT x.uuid AS uuid, x.naampad AS naampad, x.typeURI AS typeURI, x.toestand as toestand, path_loop
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)


# to verify
aql_query = """
[
  {
    "uuid": "29058156-e67e-4479-be68-a912020d6e9a",
    "naampad": null,
    "typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel",
    "toestand": "in-gebruik",
    "path_loop": [
      [
        "29058156-e67e-4479-be68-a912020d6e9a",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ],
      [
        "8a5665c4-8892-419d-ad60-c1469d872ccc",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ],
      [
        "29058156-e67e-4479-be68-a912020d6e9a",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ]
    ]
  },
  {
    "uuid": "3def25cc-fcb9-479d-a2ef-65c0d0a93e55",
    "naampad": null,
    "typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel",
    "toestand": "in-gebruik",
    "path_loop": [
      [
        "3def25cc-fcb9-479d-a2ef-65c0d0a93e55",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ],
      [
        "9c973aba-80eb-45d3-8ee7-dab79ec34157",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ],
      [
        "3def25cc-fcb9-479d-a2ef-65c0d0a93e55",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ]
    ]
  },
  {
    "uuid": "8a5665c4-8892-419d-ad60-c1469d872ccc",
    "naampad": null,
    "typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel",
    "toestand": "in-gebruik",
    "path_loop": [
      [
        "8a5665c4-8892-419d-ad60-c1469d872ccc",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ],
      [
        "29058156-e67e-4479-be68-a912020d6e9a",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ],
      [
        "8a5665c4-8892-419d-ad60-c1469d872ccc",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ]
    ]
  },
  {
    "uuid": "9c973aba-80eb-45d3-8ee7-dab79ec34157",
    "naampad": null,
    "typeURI": "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel",
    "toestand": "in-gebruik",
    "path_loop": [
      [
        "9c973aba-80eb-45d3-8ee7-dab79ec34157",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ],
      [
        "3def25cc-fcb9-479d-a2ef-65c0d0a93e55",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ],
      [
        "9c973aba-80eb-45d3-8ee7-dab79ec34157",
        "https://lgc.data.wegenenverkeer.be/ns/installatie#LSDeel"
      ]
    ]
  }
]
"""