{
    'name': 'Odoo AI Chat',
    'version': '1.2',
    'category': 'Extra Tools',
    'author': "JD DEVS",
    'depends': ['base', 'base_setup', 'mail', 'web' ],
    'data': [
        'data/mail_channel_data.xml',
        'data/user_partner_data.xml',
        'views/view.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'images': ['static/description/assets/screenshots/banner.png'],
    'icon': "/odoo_ai_chat/static/description/gemin.png",
}

