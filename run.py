import builtins
import lark.exceptions
import sys

from lark import Lark, Transformer


def super_print(*args, **kwargs):
    builtins.print(*args, **kwargs)


# function to print output with prompt
def printo(*args, **kwargs):
    super_print('DB_2019-12333>', *args, **kwargs)


# class to print out appropriate output for each parsed query.
class MyTransformer(Transformer):
    def create_table_query(self, items):
        printo('\'CREATE TABLE\' requested')
        return items

    def drop_table_query(self, items):
        printo('\'DROP TABLE\' requested')
        return items

    def select_query(self, items):
        printo('\'SELECT\' requested')
        return items

    def insert_query(self, items):
        printo('\'INSERT\' requested')
        return items

    def explain_query(self, items):
        printo('\'EXPLAIN\' requested')
        return items

    def describe_query(self, items):
        printo('\'DESCRIBE\' requested')
        return items

    def desc_query(self, items):
        printo('\'DESC\' requested')
        return items

    def delete_query(self, items):
        printo('\'DELETE\' requested')
        return items

    def show_query(self, items):
        printo('\'SHOW TABLES\' requested')
        return items

    def update_query(self, items):
        printo('\'UPDATE\' requested')
        return items

    def exit_query(self, items):
        printo('exiting...')
        sys.exit()


my_transformer = MyTransformer()

with open('grammar.lark') as file:
    sql_parser = Lark(file.read(), start="command", lexer="basic")


# Loops until the transformer detects an exit query.
# Appends ' ' at the end of each line to as we ignore newline.
while True:
    inputs = input('DB_2019-12333> ') + ' '
    # Loops until the query(queries) ends with ';'
    while not inputs.strip().endswith(';'):
        inputs += input() + ' '
    input_array = inputs.strip().split(';')
    # The last element in the array should be '', so ignore it.
    for i in range(len(input_array)-1):
        try:
            output = sql_parser.parse(input_array[i]+';')
            my_transformer.transform(output)

        except lark.exceptions.UnexpectedInput as e:
            printo(f'Syntax error in pos {e.pos_in_stream} of number {i+1} request.')
            break


