{
    'name': 'Project ML Predictor (Frontend)',
    'version': '1.0',
    'summary': 'Odoo UI to interact with ML backend API',
    'sequence': 10,
    'category': 'Project',
    'author': 'Wael Mjaied',
    'license': 'LGPL-3',
    'depends': ['project'],
"data": [
    "views/task_form_view.xml",
    "views/project_form_view.xml"
],

    'installable': True,
    'application': True,
    'auto_install': False,
    'icon': 'project_ml_predictor_odoo_ui/static/description/MLpredict.png',
'assets': {
    'web.assets_backend': [
        'project_ml_predictor_odoo_ui/static/src/xml/progress_bar_template.xml',
    ],
}

}
