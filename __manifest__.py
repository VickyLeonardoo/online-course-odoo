# -*- coding: utf-8 -*-
{
    'name': "online_course",

    'summary': """
        Module Course App""",

    'description': """
        Ini adalah contoh module custom 
    """,

    'author': "Piki",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://www.tigernix.com/tigernix/tigernix/blob/master/tigernix/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web','event','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/online_course_security.xml',
        'views/online_course_view.xml',
        'views/online_course_action.xml',
        'views/online_course_menuitem.xml',
        'views/online_course_cron.xml',
        'report/online_course_report.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}