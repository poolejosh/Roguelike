import json

logic = json.dumps([
    {'type': 'title',
     'title': 'Gameplay Settings'},
    {'type': 'numeric',
     'title': 'Update Speed',
     'desc': 'Number of Updates per Second',
     'section': 'logic',
     'key': 'updates_per_second'},
    {'type': 'string',
     'title': 'Up',
     'desc': 'Move Up',
     'section': 'logic',
     'key': 'move_up'},
    {'type': 'string',
     'title': 'Down',
     'desc': 'Move Down',
     'section': 'logic',
     'key': 'move_down'},
    {'type': 'string',
     'title': 'Left',
     'desc': 'Move Left',
     'section': 'logic',
     'key': 'move_left'},
    {'type': 'string',
     'title': 'Right',
     'desc': 'Move Right',
     'section': 'logic',
     'key': 'move_right'}])
