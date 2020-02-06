import random

from .sentences import *


def get_singular_dice_sentence(dice_type):
    if dice_type == 'PIFIA':
        return random.choice(FRASES_LANZAR_DADOS_PIFIA_SINGULAR)
    elif dice_type == 'CRITICO':
        return random.choice(FRASES_LANZAR_DADOS_CRITICO_SINGULAR)
    else:
        return random.choice(FRASES_LANZAR_DADOS_SINGULAR)


def get_plural_dice_sentence():
    return random.choice(FRASES_LANZAR_DADOS_PLURAL)


def get_dice_type(dice_result, dice_face):
    if dice_result <= 1:
        return 'PIFIA'
    elif dice_result == dice_face:
        return 'CRITICO'
    return 'NORMAL'


def get_dice_roll(dice_amount, dice_faces):
    # Montamos la estructura de resultados de cada tirada
    results = []
    for _ in range(dice_amount):
        dice_result = random.randrange(1, dice_faces + 1)
        results.append({
            'result': dice_result,
            'type': get_dice_type(dice_result, dice_faces)
        })

    # Calculamos la frase de respuesta
    if dice_amount == 1:
        sentence = get_singular_dice_sentence(results[0].get('type', ''))
        return sentence.format(dice_result=results[0].get('result', ''))
    else:
        dice_results_str = ', '.join([str(result.get('result', '')) for result in results][:-1]) + ' y ' + str(results[-1].get('result', ''))
        sentence = get_plural_dice_sentence()
        return sentence.format(dice_results=dice_results_str)


__all__ = ['get_dice_roll']
