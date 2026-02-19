from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport
from lib.connectors.OTLCursorPool import OTLCursorPool


class Report0044(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0044',
                               title='Ingevulde deprecated attributen',
                               spreadsheet_id='1GFfEoWVvi0-BpFvrPQUG6w5AuMcoyVk9Kutf9ux8bOE',
                               datasource='PostGIS',
                               persistent_column='E')

        otl_cursor = OTLCursorPool.get_cursor()
        deprecated_attributes = otl_cursor.execute("""
            with cte_attributen as (
                SELECT oa.class_uri, oa.uri, oa.deprecated_version
                FROM OSLOAttributen oa
                UNION
                SELECT oca.class_uri, oca.uri, oca.deprecated_version
                FROM OSLODatatypeComplexAttributen oca
                UNION
                SELECT opa.class_uri, opa.uri, opa.deprecated_version
                FROM OSLODatatypePrimitiveAttributen opa
                UNION
                SELECT oua.class_uri, oua.uri, oua.deprecated_version
                FROM OSLODatatypeUnionAttributen oua
                )
            -- main query
            select distinct
                a.uri
            from cte_attributen a
            left join OSLOClass o on a.class_uri = o.uri
            -- Het attirbuut is deprecated en de klasse waartoe het attribuut behoort is niet deprecated. Bijvoorbeeld klasse Damwand, attribuut isWaterdicht.
            WHERE a.deprecated_version != "" and a.uri not like '%abstracten%'
              and o.deprecated_version == ""
            order by a.uri
        """).fetchall()

        self.report.result_query = """
            SELECT a.uuid AS asset_uuid, a.toestand AS asset_toestand, ab.uri AS attribuut_uri, a_w.waarde AS attribuut_waarde
            FROM assets a
            INNER JOIN attribuutwaarden AS a_w ON (a.uuid = a_w.assetuuid)
            INNER JOIN attributen AS ab ON (a_w.attribuutuuid = ab.uuid)
            INNER JOIN (values {}) AS d_a(uri) ON (ab.uri = d_a.uri)
            WHERE a.actief = TRUE AND a_w.NOTNULL
        """.format(",".join(["('{}')".format(d[0]) for d in deprecated_attributes]))

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)

aql_query = """
/* Report0044 Ingevulde deprecated attributen */
LET properties_deprecated = [
"Aanvaarbescherming_typeAanvaarbescherming",
"Damwand_materiaal",
"Kokercomplex_ligtFunderingInOpRandWaterweg",
"Kokercomplex_ligtFunderingsaanzetOnderBodem",
"Leuning_afwerkingstype",
"Leuning_materiaal",
"Rioleringsstelsel_rioleringsstelsel",
"Aardingspen_lengte",
"Badgelezer_configuratiebestand",
"Bevestigingssteun_beschermlaag",
"Boom_heeftBoomrooster",
"Boom_kroonDiameter",
"Boom_takvrijeStamlengte",
"Boom_vrijeDoorrijhoogte",
"Brandhaspel_maximaalDebiet",
"Cabine_aardingsstelsel",
"Camera_configBestandAid",
"Camera_heeftAid",
"Camera_heeftSpitsstrook",
"ForfaitaireAansluiting_adresVolgensDNB",
"ForfaitaireAansluiting_eanNummer",
"ForfaitaireAansluiting_referentieDNB",
"Groutanker_hellingshoek",
"Laagspanningsbord_vermogen",
"Lichtmast_beschermlaag",
"MIVLus_meetrapport",
"MIVLus_uitslijprichting",
"MIVLus_zichtbaarheid",
"NietStandaardStalenProfiel_profielbreedte",
"NietStandaardStalenProfiel_profielhoogte",
"Ontvanger_toepassing",
"PTRegelaar_protocol",
"Repeater_toepassing",
"Segmentcontroller_beveil?igingssleutel",
"Segmentcontroller_merk",
"Segmentcontroller_modelnaam",
"Software_documentatie",
"Sokkel_hoogteSokkel",
"Straatkolk_rooster",
"Verkeersbordsteun_operationeleStatus",
"VerlichtingstoestelLED_armatuurkleur",
"VerlichtingstoestelLED_tussenAfstand",
"VerlichtingstoestelNaHP_armatuurkleur",
"Vluchtopening_type",
"Voedt_aansluitvermogen",
"Voorzetconstructie_brandweerstand",
"Voorzetconstructie_dikte",
"Voorzetconstructie_getestOpSpalling",
"Voorzetconstructie_isBrandwerend",
"Voorzetconstructie_maximaleInterfaceTemperatuur",
"Voorzetconstructie_technischefiche",
"WatergreppelStd_isVerholen",
"Zender_toepassing"]

FOR a IN assets
  FILTER a.AIMDBStatus_isActief == true

  LET deprecated_found = INTERSECTION(
    ATTRIBUTES(a, true),   // true = remove system attributes
    properties_deprecated
  )

  FILTER LENGTH(deprecated_found) > 0

  LET at = DOCUMENT("assettypes", a.assettype_key)

  SORT at.uri ASC

  RETURN {
    asset_uuid: a._key,
    assettype_uri: at ? at.uri : null,
    asset_toestand: a.toestand,
    asset_naam: a.AIMNaamObject_naam,
    deprecated_attributes: deprecated_found
  }
"""