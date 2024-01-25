import pyodbc
from typing import List, Tuple
from Widgets.components.DataTypes import CardMetadata, Deck, Response

class Communication:
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
                                            trusted_connection="no")

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
                else:
                    msg = str(e)
            print(msg)
            self.is_connected = False
            if self.connection:
                self.connection.close()
            self.connection = None
            return Response(False, msg)

    def get_card_by_name(self, name: str):
        try:
            query = "SELECT * FROM Cards WHERE name = ?;"
            self.cursor.execute(query, (name,))
            rows = self.cursor.fetchall()
        except pyodbc.Error as e:
            print("Fetch error:", e)
    
    def upload_card(self, metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print('Connection is not established.')
            return Response(False, "Подключение не установлено.")
        query = """
        INSERT INTO Cards (name, description, manacost, rarity, cardtype, classtype, attack, health, tribe, comment, picture, move_x, move_y, zoom, card_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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
                    metadata.comment,
                    metadata.picture,
                    metadata.move_x,
                    metadata.move_y,
                    metadata.zoom, 
                    metadata.card_image)

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
            UPDATE Cards
            SET name = ?,
                description = ?,
                manacost = ?,
                rarity = ?,
                cardtype = ?,
                classtype = ?,
                attack = ?,
                health = ?,
                tribe = ?,
                comment = ?,
                picture = ?,
                move_x = ?,
                move_y = ?,
                zoom = ?,
                card_image = ?
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
                    metadata.comment,
                    metadata.picture,
                    metadata.move_x,
                    metadata.move_y,
                    metadata.zoom, 
                    metadata.card_image,
                    metadata.id)
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            print(f"Card {metadata.name} has been updated.")
            return Response(True)
        except pyodbc.Error as e:
            print(f"Update error: {e}")
            return Response(False, e)

    def delete_card(self, metadata: CardMetadata) -> Response:
        if not self.is_connected:
            print("Connection is not established.")
            return Response(False, "Подключение не установлено.")
        
        sql_query = f"""
            DELETE FROM Cards
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

    def fetch_all_cards(self) -> List[tuple]:
        if not self.is_connected:
            print('Connection is not established.')
            return
        query = """
        SELECT * FROM CARDS;
        """
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            print(f"Library has been loaded from the database.")
            return rows
        except pyodbc.Error as e:
            print(f"Fetch cards error: {e}")
            return None

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
