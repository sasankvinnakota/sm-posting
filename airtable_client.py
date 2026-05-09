import logging
from pyairtable import Table

logger = logging.getLogger(__name__)

class AirtableClient:
    def __init__(self, api_key: str, base_id: str, table_name: str):
        if not api_key:
            raise ValueError("Airtable API key is required")

        self.table = Table(api_key, base_id, table_name)

    def get_pending_posts(self, max_records: int = 10):
        try:
            # Only fetch Pending records so each profile picks a NEW record
            formula = "AND(OR(NOT({Posting}), {Posting} = 'Pending'), OR({ImageLInk} != '', {Videolink} != ''))"
            records = self.table.all(
                formula=formula,
                max_records=max_records,
                sort=["PostDate"]
            )
            return records
        except Exception:
            logger.exception("Error fetching from Airtable")
            return []

    def update_status(self, record_id: str, status: str):
        try:
            self.table.update(record_id, {"Posting": status})
            logger.info(f"Updated record {record_id} status to '{status}' in Airtable.")
        except Exception:
            logger.exception(f"Error updating Airtable record {record_id} to {status}")

    def mark_as_posted(self, record_id: str):
        self.update_status(record_id, "Done")
