from datetime import datetime
import pyodbc
import psycopg2
from typing import List, Tuple
from DataTypes import CardMetadata, Deck, Response

from main import DEBUG
TABLE = "Cards" if not DEBUG else "CardsDbg"
CHANGELOG_TABLE = "CardsLog" if not DEBUG else "CardsLogDbg"

class CommunicationPostgres:
    def __init__(self) -> None:
        self.database = "hearth_db"
        self.server = ""
        self.port = "5432"
        self.login = ""
        self.password = ""
        self.connection = None
        self.cursor = None
        self.is_connected = False
    
    def _safe_rollback(self):
        try:
            if self.connection and not self.connection.closed:
                self._safe_rollback()
        except:
            pass

    def set_connection(self, server: str, login: str, password: str, database: str = None, port: str = None) -> Response:
        self.server, self.login, self.password = server, login, password
        if database:
            self.database = database
        if port:
            self.port = port
        try:
            self.connection = psycopg2.connect(
                dbname=self.database,
                user=self.login,
                password=self.password,
                host=self.server,
                port=self.port,
                connect_timeout=10
            )
            self.cursor = self.connection.cursor()
            print("Connection established")
            self.is_connected = True
            return Response(True)
        except psycopg2.Error as e:
            msg = str(e)
            print(msg)
            self.is_connected = False
            if self.connection:
                self.connection.close()
            self.connection = None
            return Response(False, msg)

    def fetch_all_cards(self) -> List[tuple]:
        if not self.is_connected:
            print("Connection is not established.")
            return []
        query = f"""
        SELECT id, name, description, manacost, rarity, cardtype, classtype, attack, health, tribe, istoken, tokens, comment, command, card_image, hash
        FROM {TABLE}
        WHERE card_image IS NOT NULL;
        """
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            print(f"Library has been loaded from the PostgreSQL database.")
            return rows
        except psycopg2.Error as e:
            print(f"Fetch cards error: {e}")
            self._safe_rollback()
            return []

    def fetch_cards_by_ids(self, ids: List[int]) -> List[tuple]:
        if not self.is_connected:
            print("Connection is not established.")
            return []
        if not ids:
            return []
        placeholders = ', '.join(['%s'] * len(ids))
        query = f"""
        SELECT id, name, description, manacost, rarity, cardtype, classtype, attack, health, tribe, istoken, tokens, comment, command, card_image, hash 
        FROM {TABLE} WHERE id IN ({placeholders}) AND card_image IS NOT NULL;
        """
        try:
            self.cursor.execute(query, ids)
            rows = self.cursor.fetchall()
            return rows
        except psycopg2.Error as e:
            print(f"Fetch cards error: {e}")
            self._safe_rollback()
            return []

    def fetch_edit_data_by_id(self, id: int) -> tuple:
        if not self.is_connected:
            print("Connection is not established.")
            return None
        if not id:
            print("fetch_edit_data_by_ids: Empty ID")
            return None
        query = f"""
        SELECT id, picture, move_x, move_y, zoom
        FROM {TABLE} WHERE id = %s AND card_image IS NOT NULL;
        """
        try:
            self.cursor.execute(query, (id,))
            rows = self.cursor.fetchall()
            return rows[0] if rows else None
        except psycopg2.Error as e:
            print(f"Fetch cards error: {e}")
            self._safe_rollback()
            return None

    def fetch_all_hashes(self) -> List[tuple]:
        if not self.is_connected:
            print('Connection is not established.')
            return []
        query = f"""
        SELECT id, name, hash
        FROM {TABLE}
        WHERE card_image IS NOT NULL;
        """
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return rows
        except psycopg2.Error as e:
            print(f"Fetch hashes error: {e}")
            self._safe_rollback()
            return []

    def upload_card(self, metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print('Connection is not established.')
            return Response(False, "Подключение не установлено.")
        query = f"""
        INSERT INTO {TABLE} (name, description, manacost, rarity, cardtype, classtype, attack, health, tribe, istoken, tokens, comment, command, picture, move_x, move_y, zoom, card_image, hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        params = (
            metadata.name,
            metadata.description,
            metadata.manacost,
            metadata.rarity,
            metadata.cardtype,
            metadata.classtype,
            metadata.attack,
            metadata.health,
            metadata.tribe,
            metadata.istoken,
            metadata.tokens,
            metadata.comment,
            metadata.command,
            metadata.picture,
            metadata.move_x,
            metadata.move_y,
            metadata.zoom,
            metadata.card_image,
            metadata.hash
        )
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            print(f"Card {metadata.name} has been added to the PostgreSQL database.")
            return Response(True)
        except psycopg2.Error as e:
            print(f"Insert error: {e}")
            self._safe_rollback()
            return Response(False, str(e))

    def upload_edit_card(self, metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print('Connection is not established.')
            return Response(False, "Подключение не установлено.")
        query = f"""
            UPDATE {TABLE}
            SET name = %s,
                description = %s,
                manacost = %s,
                rarity = %s,
                cardtype = %s,
                classtype = %s,
                attack = %s,
                health = %s,
                tribe = %s,
                istoken = %s,
                tokens = %s,
                comment = %s,
                command = %s,
                picture = %s,
                move_x = %s,
                move_y = %s,
                zoom = %s,
                card_image = %s,
                hash = %s
            WHERE id = %s;
        """
        params = (
            metadata.name,
            metadata.description,
            metadata.manacost,
            metadata.rarity,
            metadata.cardtype,
            metadata.classtype,
            metadata.attack,
            metadata.health,
            metadata.tribe,
            metadata.istoken,
            metadata.tokens,
            metadata.comment,
            metadata.command,
            metadata.picture,
            metadata.move_x,
            metadata.move_y,
            metadata.zoom,
            metadata.card_image,
            metadata.hash,
            metadata.id
        )
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            print(f"Card {metadata.name} has been updated in PostgreSQL.")
            return Response(True)
        except psycopg2.Error as e:
            print(f"Update error: {e}")
            self._safe_rollback()
            return Response(False, str(e))

    def upload_edit_changelog(self, metadata: CardMetadata, old_metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print('Connection is not established.')
            return Response(False, "Подключение не установлено.")
        date = datetime.now()
        for meta in (old_metadata, metadata):
            query = f"""
            INSERT INTO {CHANGELOG_TABLE} (id, name, description, manacost, rarity, attack, health, tribe, comment, change_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            params = (
                meta.id,
                meta.name,
                meta.description,
                meta.manacost,
                meta.rarity,
                meta.attack,
                meta.health,
                meta.tribe,
                meta.comment,
                date
            )
            try:
                self.cursor.execute(query, params)
            except psycopg2.Error as e:
                print(f"Update error: {e}")
                return Response(False, str(e))
        try:
            self.connection.commit()
            return Response(True)
        except psycopg2.Error as e:
            print(f"Update error: {e}")
            self._safe_rollback()
            return Response(False, str(e))

    def delete_card(self, metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print("Connection is not established.")
            return Response(False, "Подключение не установлено.")
        sql_query = f"""
            DELETE FROM {TABLE}
            WHERE id = %s;
        """
        try:
            self.cursor.execute(sql_query, (metadata.id,))
            self.connection.commit()
            print(f"Card {metadata.name} has been deleted from PostgreSQL.")
            return Response(True)
        except psycopg2.Error as e:
            print(f"Deletion error: {e}")
            self._safe_rollback()
            return Response(False, str(e))

    def create_new_deck(self, deck_name: str, owner: str) -> int:
        if not self.is_connected:
            print('Connection is not established.')
            return None
        query = """
            INSERT INTO Decks (name, cards, owner)
            VALUES (%s, %s, %s)
            RETURNING id;
            """
        try:
            self.cursor.execute(query, (deck_name, "", owner))
            deck_id = self.cursor.fetchone()[0]
            self.connection.commit()
            print(f"Deck {deck_name.upper()} has been created in PostgreSQL.")
            return int(deck_id)
        except psycopg2.Error as e:
            print(f"Fetch decks error: {e}")
            self._safe_rollback()
            return None

    def fetch_all_decks(self) -> List[tuple]:
        if not self.is_connected:
            print('Connection is not established.')
            return []
        query = """
        SELECT * FROM Decks;
        """
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            print(f"Decks have been loaded from the PostgreSQL database.")
            return rows
        except psycopg2.Error as e:
            print(f"Fetch decks error: {e}")
            self._safe_rollback()
            return []

    def upload_edit_deck(self, id: int, cards_string: str) -> Response:
        if not self.is_connected:
            print('Connection is not established.')
            return Response(False, "Подключение не установлено.")
        query = f"""
            UPDATE Decks
            SET cards = %s
            WHERE id = %s;
        """
        params = (cards_string, id)
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            print(f"Deck {id} has been updated in PostgreSQL.")
            return Response(True)
        except psycopg2.Error as e:
            print(f"Update error: {e}")
            self._safe_rollback()
            return Response(False, str(e))

    def fetch_full_changelog(self, days: int = 0):
        query = f"""
        SELECT * FROM {CHANGELOG_TABLE} order by change_date DESC;
        """
        params = ()
        if days:
            query = f"""
            SELECT *
            FROM CardsLogDbg
            WHERE change_date >= NOW() - INTERVAL '%s days'
            order by change_date ASC;
            """
            params = (days,)
        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return rows
        except psycopg2.Error as e:
            print(f"Update error: {e}")
            self._safe_rollback()
            return []

# Deprecated
class CommunicationMS:
    def __init__(self) -> None:
        self.driver = ""
        for driver in pyodbc.drivers():
            if driver == 'SQL Server Native Client 11.0':
                self.driver = driver
                break
        self.database = "hearth_db"
        self.server = ""
        self.port = "1433"
        self.login = ""
        self.password = ""

        self.connection = None
        self.cursor = None
        self.is_connected = False


    def set_connection(self, server: str, login: str, password: str) -> Response:
        self.server, self.login, self.password = server, login, password
        try:
            self.connection = pyodbc.connect(f' DRIVER={self.driver}; \
                                                SERVER={self.server}; \
                                                PORT={self.port}; \
                                                DATABASE={self.database}; \
                                                UID={self.login}; \
                                                PWD={self.password}',
                                                trusted_connection="no", 
                                                timeout=6)

            self.cursor = self.connection.cursor()
            print("Connection established")
            self.is_connected = True
            return Response(True)
        except pyodbc.Error as e:
            msg = ''
            if e.args and len(e.args) > 0:
                error_info = e.args[0]
                if error_info == 'IM002':
                    msg = "Отсутствует драйвер SQL Server Native Client 11.0"
                elif error_info == '28000':
                    msg = "Некорректные данные подключения."
                elif error_info == '08001':
                    msg = "Время ожидания истекло."
                else:
                    msg = str(e)
            print(msg)
            self.is_connected = False
            if self.connection:
                self.connection.close()
            self.connection = None
            return Response(False, msg)

    def fetch_all_cards(self) -> List[tuple]:
        if not self.is_connected:
            print("Connection is not established.")
            return
        query = f"""
        SELECT id, name, description, manacost, rarity, cardtype, classtype, attack, health, tribe, istoken, tokens, comment, command, card_image, hash FROM {TABLE} where card_image is not null;
        """

        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            print(f"Library has been loaded from the database.")
            return rows
        except pyodbc.Error as e:
            print(f"Fetch cards error: {e}")
            return None

    def fetch_cards_by_ids(self, ids: List[int]) -> List[tuple]:
        if not self.is_connected:
            print("Connection is not established.")
            return
        if not ids:
            return Response(False, "Empty ID list")
        
        placeholders = ", ".join("?" for _ in ids)
        query = f"SELECT id, name, description, manacost, rarity, cardtype, classtype, attack, health, tribe, istoken, tokens, comment, command, card_image, hash FROM {TABLE} WHERE id IN ({placeholders}) and card_image is not null"

        try:
            self.cursor.execute(query, ids)
            rows = self.cursor.fetchall()
            return rows
        except pyodbc.Error as e:
            print(f"Fetch cards error: {e}")
            return None
             
    def fetch_edit_data_by_id(self, id: int) -> tuple:
        if not self.is_connected:
            print("Connection is not established.")
            return
        if not id:
            print("fetch_edit_data_by_ids: Empty ID")
            return Response(False, "Empty ID")
        
        params = ( id )
        query = f"SELECT id, picture, move_x, move_y, zoom FROM {TABLE} WHERE id IN (?) and card_image is not null"

        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return rows[0]
        except pyodbc.Error as e:
            print(f"Fetch cards error: {e}")
            return None
   
    def fetch_all_hashes(self) -> List[tuple]:
        if not self.is_connected:
            print('Connection is not established.')
            return
        query = f"""
        SELECT id, name, hash FROM {TABLE} where card_image is not null;
        """
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return rows
        except pyodbc.Error as e:
            print(f"Fetch hashes error: {e}")
            return None

    def upload_card(self, metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print('Connection is not established.')
            return Response(False, "Подключение не установлено.")
        query = f"""
        INSERT INTO {TABLE} (name, description, manacost, rarity, cardtype, classtype, attack, health, tribe, istoken, tokens, comment, command, picture, move_x, move_y, zoom, card_image, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        # Параметры (кроме id) передаются в execute в виде кортежа
        params = (  metadata.name,
                    metadata.description,
                    metadata.manacost,
                    metadata.rarity, 
                    metadata.cardtype, 
                    metadata.classtype,
                    metadata.attack, 
                    metadata.health, 
                    metadata.tribe,
                    metadata.istoken,
                    metadata.tokens,
                    metadata.comment,
                    metadata.command,
                    metadata.picture,
                    metadata.move_x,
                    metadata.move_y,
                    metadata.zoom, 
                    metadata.card_image,
                    metadata.hash  )

        try:

            self.cursor.execute(query, params)
            self.connection.commit()
            print(f"Card {metadata.name} has been added to the database.")
            return Response(True)
        except pyodbc.Error as e:
            print(f"Insert error: {e}")
            return Response(False, e)

    def upload_edit_card(self, metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print('Connection is not established.')
            return Response(False, "Подключение не установлено.")
        # Параметризованный SQL запрос
        query = f"""
            UPDATE {TABLE}
            SET name = ?,
                description = ?,
                manacost = ?,
                rarity = ?,
                cardtype = ?,
                classtype = ?,
                attack = ?,
                health = ?,
                tribe = ?,
                istoken = ?,
                tokens = ?,
                comment = ?,
                command = ?,
                picture = ?,
                move_x = ?,
                move_y = ?,
                zoom = ?,
                card_image = ?,
                hash = ?
            WHERE id = ?
        """
        params = (  metadata.name,
                    metadata.description,
                    metadata.manacost,
                    metadata.rarity, 
                    metadata.cardtype, 
                    metadata.classtype,
                    metadata.attack, 
                    metadata.health, 
                    metadata.tribe,
                    metadata.istoken,
                    metadata.tokens,
                    metadata.comment,
                    metadata.command,
                    metadata.picture,
                    metadata.move_x,
                    metadata.move_y,
                    metadata.zoom, 
                    metadata.card_image,
                    metadata.hash,
                    metadata.id)
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            print(f"Card {metadata.name} has been updated.")
            return Response(True)
        except pyodbc.Error as e:
            print(f"Update error: {e}")
            return Response(False, e)
        
    def upload_edit_changelog(self, metadata: CardMetadata, old_metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print('Connection is not established.')
            return Response(False, "Подключение не установлено.")
        
        date = datetime.now()

        for meta in (old_metadata, metadata):
            query = f"""
            INSERT INTO {CHANGELOG_TABLE} (id, name, description, manacost, rarity, attack, health, tribe, comment, change_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """

            params = (  meta.id,
                        meta.name,
                        meta.description,
                        meta.manacost,
                        meta.rarity,
                        meta.attack, 
                        meta.health, 
                        meta.tribe,
                        meta.comment,
                        date )
            
            self.cursor.execute(query, params)
        try:
            self.connection.commit()
            return Response(True)
        except pyodbc.Error as e:
            print(f"Update error: {e}")
            return Response(False, e)

    def delete_card(self, metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print("Connection is not established.")
            return Response(False, "Подключение не установлено.")
        
        sql_query = f"""
            DELETE FROM {TABLE}
            WHERE id = ?
        """

        try:
            self.cursor.execute(sql_query, metadata.id)
            self.connection.commit()
            print(f"Card {metadata.name} has been deleted.")
            return Response(True)
        except pyodbc.Error as e:
            print(f"Deletion error: {e}")
            return Response(False, e)

    def create_new_deck(self, deck_name: str, owner: str) -> int:
        if not self.is_connected:
            print('Connection is not established.')
            return
        
        query = """
            INSERT INTO Decks (name, cards, owner)
            OUTPUT INSERTED.id VALUES (?, ?, ?)
            """

        try:
            self.cursor.execute(query, (deck_name, "", owner))
            deck_id = self.cursor.fetchone()[0]
            self.connection.commit()
            print(f"Deck {deck_name.upper()} has been created.")
            return int(deck_id)
        except pyodbc.Error as e:
            print(f"Fetch decks error: {e}")
            return None

    def fetch_all_decks(self) -> List[tuple]:
        if not self.is_connected:
            print('Connection is not established.')
            return
        
        query = """
        SELECT * FROM DECKS;        
        """

        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            print(f"Decks have been loaded from the database.")
            return rows
        except pyodbc.Error as e:
            print(f"Fetch decks error: {e}")
            return None
        
    def upload_edit_deck(self, id: int, cards_string: str) -> Response:
        if not self.is_connected:
            print('Connection is not established.')
            return Response(False, "Подключение не установлено.")
    
        # Параметризованный SQL запрос
        query = f"""
            UPDATE Decks
            SET cards = ?
            WHERE id = ?
        """
        params = (  cards_string,
                    id )
        
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            print(f"Deck {id} has been updated.")
            return Response(True)
        except pyodbc.Error as e:
            print(f"Update error: {e}")
            return Response(False, e)

    def fetch_full_changelog(self, days: int = 0):
        # SQL-запрос
        query = "SELECT * FROM MyTable order by change_date DESC;"
        if days:
            query = f"""
            SELECT *
            FROM {CHANGELOG_TABLE}
            WHERE change_date >= DATEADD(DAY, -(?), GETDATE())
            order by change_date ASC;
            """
        params = ( days )
        
        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return rows
        except pyodbc.Error as e:
            print(f"Update error: {e}")
            return Response(False, e)


# Deprecated
# if __name__ == '__main__':
#     c = CommunicationMS()
#     c.server = "26.113.25.65"
#     c.login = "hs_guest"
#     c.password = "123"
#     print(c.set_connection(c.server, c.login, c.password).ok)
    
if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import credentials

    c2 = CommunicationPostgres()
    c2.server = credentials.IP
    c2.login = credentials.USER
    c2.password = credentials.PASSWORD
    print(c2.set_connection(c2.server, c2.login, c2.password).ok)

    


