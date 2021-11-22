#!/usr/bin/env python

import sys
import sqlparse
import logging
from enum import Enum
from typing import NamedTuple, List
from sqlparse import tokens
from sqlparse.sql import Statement, Parenthesis, Identifier
from sqlparse.tokens import Token
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.WARN,
                    format='%(levelname)s(%(lineno)d): %(message)s')

env = Environment(loader=FileSystemLoader('./', encoding='utf8'))
tpl = env.get_template('table_xml.j2')


class Column(NamedTuple):
    name: str
    name_jp: str
    data_type: str
    is_nullable: bool

    @classmethod
    def create(cls, tokens):
        Mode = Enum('Mode', ['NAME', 'DATA_TYPE', 'NAME_JP', 'DONE'])
        mode = Mode.NAME

        name = name_jp = ''
        data_types = []
        is_nullable = False

        logging.debug('tokens: %s', tokens)
        for token in tokens:
            logging.debug('token: %s, %s, %s', mode, token.ttype, token.value)
            if (mode == Mode.NAME and str(token.ttype) == 'Token.Name'):
                name = token.value.strip('`')
                mode = Mode.DATA_TYPE
            elif (mode == Mode.DATA_TYPE and token.value.upper() == 'COMMENT'):
                mode = Mode.NAME_JP
            elif (mode == Mode.DATA_TYPE and str(token.ttype) == 'Token.Keyword' and 'NULL' in token.value.upper()):
                is_nullable = False if token.value.upper() == 'NOT NULL' else True
            elif (mode == Mode.DATA_TYPE and str(token.ttype) == 'Token.Keyword' and token.value.upper() in ['AUTO_INCREMENT', 'COLLATE', 'DEFAULT']):
                pass
            elif (mode == Mode.DATA_TYPE and str(token.ttype) == 'Token.Name' and '_UNICODE_' in token.value.upper()):
                pass
            elif (mode == Mode.DATA_TYPE):
                value = token.value
                if value.isdecimal():
                    value = f'({value})'
                data_types.append(value)
            elif (mode == Mode.NAME_JP and str(token.ttype) == 'Token.Literal.String.Single'):
                name_jp = token.value.strip("'")
                mode = Mode.DONE
            else:
                logging.debug('マッチしなかった: %s, %s', token.ttype, token.value)

        col = cls(
            name=name,
            name_jp=name_jp,
            data_type=' '.join(data_types).replace(' (', '('),
            is_nullable=is_nullable,
        )
        logging.debug('%s', col)

        return col


class Table(NamedTuple):
    name: str
    name_jp: str
    columns: List[Column]


def extract_table_name(statement: Statement):
    _, identifier = statement.token_next_by(i=Identifier)
    _, single = statement.token_next_by(t=Token.Literal.String.Single)

    return (identifier.value.strip('`'), single.value.strip("'"))


def extract_columns(statement: Statement):
    def is_not_exclude_column(col):
        return col and not (col[0].value.strip('`') in [
            'PRIMARY',
            'KEY',
            'FULLTEXT',
            'created_at',
            'updated_at',
            'deleted_at',
            'created_by',
            'updated_by'
        ])

    parenthesis: Parenthesis
    _, parenthesis = statement.token_next_by(i=Parenthesis)

    definitions: List[Token] = []
    tmp: List[Token] = []
    par_level = 0
    for token in parenthesis.flatten():
        if token.is_whitespace:
            continue
        elif token.match(tokens.Punctuation, '('):
            par_level += 1
            continue
        if token.match(tokens.Punctuation, ')'):
            if par_level == 0:
                break
            else:
                par_level -= 1
        elif token.match(tokens.Punctuation, ','):
            if is_not_exclude_column(tmp):
                definitions.append(Column.create(tmp))
            tmp = []
        else:
            tmp.append(token)
    if is_not_exclude_column(tmp):
        definitions.append(Column.create(tmp))

    return definitions


def extract_table(sql):
    statement = sqlparse.parse(sql)[0]
    table_name, table_name_jp = extract_table_name(statement)
    columns = extract_columns(statement)

    logging.debug('table name: %s: %s', table_name_jp, table_name)
    for column in columns:
        logging.debug('%s', column)

    return Table(name=table_name, name_jp=table_name_jp, columns=columns)


def convert_to_xml(filenames: List[str]):
    tables: List[Table] = []
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as f:
            sql = f.read()
            tables.append(extract_table(sql))

    logging.debug('tables: %s', tables)
    logging.debug('tables: %s', tables[0]._asdict())
    return tpl.render(tables=tables)


if __name__ == '__main__':
    args = sys.argv
    print(convert_to_xml(args[1:]))
