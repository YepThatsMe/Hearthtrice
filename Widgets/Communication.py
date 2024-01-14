import pyodbc
from typing import List
from Widgets.components.DataTypes import CardMetadata

class Communication:
    
    class Response:
        def __init__(self, ok: bool, msg: str = ""):
            self.ok = ok
            self.msg = msg


    def __init__(self) -> None:
        self.driver = "SQL Server Native Client 11.0"
        self.database = "hearth_db"
        self.server = ""
        self.port = "1433"
        self.login = ""
        self.password = ""

        self.connection = None
        self.cursor = None
        self.status = Communication.Response(False)


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
            self.status =  Communication.Response(True)
            return self.status
        except pyodbc.Error as e:
            print("Failed to connect")
            self.status =  Communication.Response(False, e)
            return self.status

    def get_card_by_name(self, name: str):
        try:
            query = "SELECT * FROM Cards WHERE name = ?;"
            self.cursor.execute(query, (name,))
            rows = self.cursor.fetchall()
        except pyodbc.Error as e:
            print("Fetch error:", e)
    
    def upload_card(self, metadata: CardMetadata) -> Response:
        if not self.status.ok:
            print('Connection is not established.')
            return
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
            return Communication.Response(True)
        except pyodbc.Error as e:
            print(f"Insert error: {e}")
            return Communication.Response(False, e)

    def upload_edit_card(self, metadata: CardMetadata) -> Response:
        if not self.status.ok:
            print('Connection is not established.')
            return
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
            return Communication.Response(True)
        except pyodbc.Error as e:
            print(f"Update error: {e}")
            return Communication.Response(False, e)

    def delete_card(self, metadata: CardMetadata) -> Response:
        sql_query = f"""
            DELETE FROM Cards
            WHERE id = ?
        """

        try:
            self.cursor.execute(sql_query, metadata.id)
            self.connection.commit()
            print(f"Card {metadata.name} has been deleted.")
            return Communication.Response(True)
        except pyodbc.Error as e:
            print(f"Deletion error: {e}")
            return Communication.Response(False, e)

    def fetch_all_cards(self) -> List[tuple]:
        if not self.status.ok:
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
            print(f"Fetch all error: {e}")
            return None

    def update_file(self, file_id, new_file, new_name = None):
        if not self.status.ok:
            print('Connection is not established.')
            return
