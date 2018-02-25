"""
databse_manager.py - Manages access to the central database file

Copyright (c) 2018 The Fuel Rats Mischief,
All rights reserved.

Licensed under the BSD 3-Clause License.

See LICENSE.md

This module is built on top of the Pydle system.
"""
import sqlite3


class DataBaseManager:
    def __init__(self):
        if not self.instance:
            self.instance = self.__DatabaseManager()

    def __getattr__(self, item):
        return self.instance

    class __DatabaseManager:
        filePath: str = "mecha3.db"

        def __init__(self):
            """
            Initializes the connection and creates the default tables, should they not exist
            """
            self.connection = sqlite3.connect(self.filePath)
            if self.has_table("mecha3-facts"):
                self.create_table("mecha3-facts", {"fact": "STRING", "lang": "STRING", "text": "STRING"})

        def has_table(self, name: str):
            """
            checks whether or not the given table exists
            :param name: name of the table to check
            :return: True when table exists, false otherwise
            """
            return len(self.connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='"+ name +"'").fetchall()) >= 1

        def create_table(self, name: str, types: dict):
            """
            Creates a table with the given name and signature
            :param name: name of the table to create
            :param types: dict of columns, key denotes the name, value the type. type must be a valid SQL type
            :return: nothing
            """
            if self.has_table(name): raise ValueError(f"Table {name} already exists")
            type_string: str = ""
            for k, v in types.items():
                type_string += f" {k} {v.upper()},"
            type_string = type_string[:-1]
            self.connection.execute("CREATE TABLE '" + name + "' (" + type_string + ")")

        def insert_row(self, table_name: str, values: tuple):
            """
            Inserts the given row into the given table
            :param table_name: Name of table to insert into
            :type table_name: str
            :param values: values to insert into the given table. amount and ordering must match the table columns
            :type values: tuple
            :return: nothing
            :raises sqlite3.OperationalError: When the statement was malformed, most likely because the length of the tuple wasn't equal to the number of columns
            :raises ValueError: When the given table does not exist
            """
            if not self.has_table(table_name): raise ValueError(f"Table {table_name} does not exist")

            value_string: str = ""
            for k in values:
                value_string += f" {k},"
            value_string = value_string[:-1]

            self.connection.execute("INSERT INTO '" + table_name + "' VALUES (" + value_string + ")")

        def select_rows(self, table_name: str, connector: str, condition: dict = {}) -> list[tuple]:
            """
            Return the rows from the specified table and filters them by the specified conditions. Supports
                'AND' and 'OR'
            :param table_name: name of table to select from
            :type table_name: str
            :param connector: either 'AND' or 'OR'
            :type connector: str
            :param condition: a dict of conditions to filter the result. these will be connected via 'connector'
                and in the end must be true for the given row to be included in the result
            :return: list of tuples, where each tuple represents the row,
                and each element of the tuple represents the value of the column
            :rtype list[tuple]
            :raises ValueError, should connector not be 'OR' or 'AND'
            :raises ValueError: When the given table does not exist
            """
            if not self.has_table(table_name): raise ValueError(f"Table {table_name} does not exist")

            connector = connector.upper()
            if connector not in ["AND", "OR"]: raise ValueError("")

            condition_string: str = ""
            for k, v in condition.items():
                condition_string += f" {k} {v} {connector}"
            condition_string = condition_string[:-len(connector)]
            condition_string = f" WHERE {condition_string}"

            return self.connection.execute("SELECT * FROM '" + table_name + "'" + condition_string).fetchall()

        def update_row(self, table_name: str, connector: str, values: dict, condition: dict = {}):
            """
            Updates the rows of the given table with the given values. Rows to update are filtered by the
            :param table_name: name of table to update
            :param connector: 'AND' or 'OR'
            :param values: new value set. key is column name, value is new column value.
            :param condition: the set of conditions to be fulfilled to update the column
            :return: nothing
            :rtype: None
            :raises ValueError: If:
                1.: The table does not exist
                2.: No condition was given
                3.: the Connector was not 'AND' or 'OR'
            """
            if not self.has_table(table_name): raise ValueError(f"Table {table_name} does not exist")

            if len(condition) <= 0: raise ValueError("No conditions were given!")

            connector = connector.upper()
            if connector not in ["AND", "OR"]: raise ValueError("")

            condition_string: str = ""
            for k, v in condition.items():
                condition_string += f" {k} {v} {connector}"
            if len(condition_string) > 0:
                condition_string = condition_string[:-len(connector)]
                condition_string = f" WHERE {condition_string}"

            value_string: str = ""
            for k, v in values.items():
                value_string += f" {k}={v},"
            if len(value_string) > 0:
                value_string = value_string[:-1]
                value_string = f" WHERE {value_string}"

            self.connection.execute("UPDATE '" + table_name + "' SET " + value_string + condition_string)

        def delete_row(self, table_name: str, connector: str, condition: dict = {}):
            """
            deletes the rows from the specified table and filters them by the specified conditions. Supports
                'AND' and 'OR'
            :param table_name: name of table to delete from
            :type table_name: str
            :param connector: either 'AND' or 'OR'
            :type connector: str
            :param condition: a dict of conditions to filter the result. these will be connected via 'connector'
                and in the end must be true for the given row to be deleted
            :raises ValueError, should connector not be 'OR' or 'AND'
            :raises ValueError: When the given table does not exist
                        """
            if not self.has_table(table_name): raise ValueError(f"Table {table_name} does not exist")

            if not len(condition) > 0: raise ValueError("No conditions were given!")

            connector = connector.upper()
            if connector not in ["AND", "OR"]: raise ValueError(f"Connector {connector} not supported")

            condition_string: str = ""
            for k, v in condition.items():
                condition_string += f" {k} {v} {connector}"
            condition_string = condition_string[:-len(connector)]

            return self.connection.execute("DELETE FROM '" + table_name + "' WHERE " + condition_string).fetchall()
