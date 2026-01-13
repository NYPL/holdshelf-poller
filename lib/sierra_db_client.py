import os
from nypl_py_utils.classes.postgresql_client import PostgreSQLClient
from psycopg.rows import dict_row
from lib.logger import logger


class SierraDbClient:
    def __init__(self):
        self.base_client = PostgreSQLClient(
            os.environ['SIERRA_DB_HOST'],
            os.environ['SIERRA_DB_PORT'],
            os.environ['SIERRA_DB_NAME'],
            os.environ['SIERRA_DB_USER'],
            os.environ['SIERRA_DB_PASSWORD']
        )
        self.logger = logger

    def holdshelf_entries(self):
        """Get latest holdshelf entries from Sierra DB

        Returns
        -------
        list
            List of dicts representing items on holdshelf
        """

        self.base_client.connect(row_factory=dict_row)

        # Assume a polling period of 4 minutes.
        # We have to cast a rather wide net when querying holds based on
        # placed_at because a patron may place a hold just before closing
        # on Saturday and staff will not scan it until sometime after opening
        # on Sunday at 1pm (in the worst case). Accounting for retrieval
        # time and temporary closers, let's assume a hold could take as much
        # 24 hours to arrive on holdshelf.
        age_of_holds = int(os.environ.get('AGE_OF_HOLDS_TO_QUERY_HOURS', '24'))
        min_placed_gmt = f"NOW() - INTERVAL '{age_of_holds} HOURS'"

        pickup_locations = os.environ['PICKUP_LOCATION_CODES'].split(',')
        holding_locations = os.environ['HOLDING_LOCATION_CODES'].split(',')

        query = '''
            SELECT
              H.id AS hold_id,
              placed_gmt,
              I.record_num AS item_id,
              I.location_code AS item_location,
              H.pickup_location_code AS pickup_location,
              ( SELECT _P.record_num FROM sierra_view.patron_view _P
                WHERE _P.id=H.patron_record_id
              ) AS patron_id
            FROM sierra_view.hold H
            INNER JOIN sierra_view.item_view I ON I.id=H.record_id
            WHERE H.status='i'
            AND H.pickup_location_code IN ({pickup_location_codes})
            AND H.placed_gmt > {min_placed_gmt}
            AND I.location_code IN ({holding_location_codes})
            ORDER BY H.placed_gmt DESC;'''.format(
                min_placed_gmt=min_placed_gmt,
                pickup_location_codes=self._sql_string_list(pickup_locations),
                holding_location_codes=self._sql_string_list(holding_locations)
            )

        sierra_raw_data = self.base_client.execute_query(query)

        self.base_client.close_connection()

        return sierra_raw_data

    @staticmethod
    def _sql_string_list(arr):
        """Return string representation of given list suitable for use in a
        SQL IN clause

        Parameters
        ----------
        arr : list
            Array of scalar values

        Returns
        -------
        str
            Single-quoted, comma separated values. e.g. "'v1','v2','v3'"
        """
        return ','.join(f"'{code}'" for code in arr)
