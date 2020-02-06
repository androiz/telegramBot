import logging
import boto3

from .sentences import *


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def download_database(db_file):
    try:
        resource = boto3.client('s3')
        resource.download_file('amzn1-ask-skill-d0bc28cc-a99e-buildsnapshotbucket-16udz1564snfs', 'Media/dungeon_master', db_file)
        logger.info('Database downloaded successfully')
    except Exception as esc:
        logger.error('Error downloading database: %s', esc)


def get_spell_type_sentence(spell_type, spell_row):
    if spell_type == 'description':
        return HECHIZO_DESCRIPCION_PARCIAL.format(spell_name=spell_row[0], value=spell_row[8])
    elif spell_type == 'duration':
        return HECHIZO_DURACION.format(spell_name=spell_row[0], value=spell_row[7])
    elif spell_type == 'components':
        return HECHIZO_COMPONENTES.format(spell_name=spell_row[0], value=spell_row[6])
    elif spell_type == 'distance':
        return HECHIZO_ALCANCE.format(spell_name=spell_row[0], value=spell_row[5])
    elif spell_type == 'spelling_time':
        return HECHIZO_TIEMPO_LANZAMIENTO.format(spell_name=spell_row[0], value=spell_row[4])
    elif spell_type == 'level':
        return HECHIZO_NIVEL_HECHIZO.format(spell_name=spell_row[0], value=spell_row[3])
    elif spell_type == 'category':
        return HECHIZO_CATEGORIA.format(spell_name=spell_row[0], value=spell_row[2])
    else:
        return HECHIZO_NOT_FOUND
