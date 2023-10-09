# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class online_course(models.Model):
#     _name = 'online_course.online_course'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100