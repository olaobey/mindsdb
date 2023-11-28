from mindsdb_sql.parser.ast import ASTNode
import pandas as pd
from typing import Text, List, Dict, Any

from mindsdb_sql.parser import ast
from mindsdb.integrations.libs.api_handler import APITable

from mindsdb.integrations.handlers.utilities.query_utilities.insert_query_utilities import INSERTQueryParser
from mindsdb.integrations.handlers.utilities.query_utilities.select_query_utilities import SELECTQueryParser

from mindsdb.utilities import log

logger = log.getLogger(__name__)


class MessagesTable(APITable):
    """The Microsoft Teams Messages Table implementation"""

    def insert(self, query: ast.Insert) -> None:
        """Sends messages to a Microsoft Teams Channel through a configured webhook.

        Parameters
        ----------
        query : ast.Insert
           Given SQL INSERT query.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the query contains an unsupported condition
        """
        insert_statement_parser = INSERTQueryParser(
            query,
            supported_columns=['text', 'title'],
            mandatory_columns=['text'],
            all_mandatory=False
        )
        message_data = insert_statement_parser.parse_query()
        self.send_message(message_data)

    def send_message(self, message_data: List[Dict[Text, Any]]) -> None:
        """Sends messages to a Microsoft Teams Channel using the parsed message data.

        Parameters
        ----------
        message_data : List[Dict[Text, Any]]
           List of dictionaries containing the messages to send.

        Returns
        -------
        None
        """
        teams = self.handler.connect() 
        for message in message_data:
            try:
                teams.title(message['title'])
                teams.text(message['text'])
                teams.send()
                logger.info(f"Message sent to Microsoft Teams channel successfully.")
            except Exception as e:
                logger.error(f"Error sending message to Microsoft Teams channel: {e}")
                raise e
            
class ChannelsTable(APITable):
    """The Microsoft Channels Table implementation"""

    def select(self, query: ASTNode) -> pd.DataFrame:
        """Pulls data from the Microsoft Teams "GET /teams/{group_id}/channels" API endpoint.

        Parameters
        ----------
        query : ast.Select
           Given SQL SELECT query

        Returns
        -------
        pd.DataFrame
            Microsoft Teams Channels matching the query

        Raises
        ------
        ValueError
            If the query contains an unsupported condition
        """
        select_statement_parser = SELECTQueryParser(
            query,
            'channels',
            self.get_columns()
        )

        selected_columns, where_conditions, order_by_conditions, result_limit = select_statement_parser.parse_query()

        channels_df = pd.json_normalize(self.get_channels())

        return channels_df

    def get_channels(self) -> List[Dict[Text, Any]]:
        api_client = self.handler.connect()
        return api_client.get_channels()
    
    def get_columns(self) -> List[Text]:
        return [
            "id",
            "createdDateTime",
            "displayName",
            "description",
            "isFavoriteByDefault",
            "email",
            "tenantId",
            "webUrl",
            "membershipType"
        ]