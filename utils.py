from messages import TEMPLATE_EVENT


def template_event_format(event_data):
    return TEMPLATE_EVENT.format(
        event_title=event_data.get('event_title', ''),
        event_date=event_data.get('event_date', ''),
        event_time=event_data.get('event_time', ''),
        event_address=event_data.get('event_address', ''),
        event_master=event_data.get('event_master', ''),
        event_free=event_data.get('event_players_limit', 0) - len(event_data.get('event_players', {})),
        event_players=''.join([f'\n📗 {name}' for _, name in event_data.get('event_players', {}).items()])
    )
