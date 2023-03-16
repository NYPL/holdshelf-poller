import os
from nypl_py_utils import (PostgreSQLClient)
from psycopg.rows import dict_row
from nypl_py_utils.functions.log_helper import create_log


class SierraDbClient:
    def __init__(self):
        self.base_client = PostgreSQLClient(
            os.environ['SIERRA_DB_HOST'],
            os.environ['SIERRA_DB_PORT'],
            os.environ['SIERRA_DB_NAME'],
            os.environ['SIERRA_DB_USER'],
            os.environ['SIERRA_DB_PASSWORD']
        )
        self.logger = create_log('sierra_db_client')

    def holdshelf_entries(self):
        """Get latest holdshelf entries from Sierra DB

        Returns
        -------
        list
            List of dicts representing items on holdshelf
        """

        self.base_client.connect()

        min_placed_gmt = "DATE(NOW()) - INTERVAL '1 DAYS'"
        # min_placed_gmt = "'2022-07-05 19:22:29-04'"

        pickup_locations = os.environ['PICKUP_LOCATION_CODES'].split(',')
        holding_locations = os.environ['HOLDING_LOCATION_CODES'].split(',')

        query = '''
            SELECT
              H.id AS hold_id,
              placed_gmt,
              I.record_num AS item_id,
              I.location_code AS item_location,
              H.pickup_location_code AS pickup_location
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

        sierra_raw_data = self.base_client.execute_query(query,
                                                         row_factory=dict_row)

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
