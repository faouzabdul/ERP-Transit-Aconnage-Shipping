# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields


class Crew(models.Model):
    _name = 'servoo.shipping.crew'
    _description = 'Crew list'

    file_id = fields.Many2one('servoo.shipping.file', 'Shipping File', required=True)
    rank = fields.Char('Rank or rating')
    crew_id = fields.Many2one('servoo.shipping.person', 'Crew', required=True)


class CrewEffect(models.Model):
    _name = 'servoo.shipping.crew.effect'
    _description = 'Crew Effect'

    file_id = fields.Many2one('servoo.shipping.file', 'Shipping File', required=True)
    crew_id = fields.Many2one('servoo.shipping.person', 'Crew', required=True)
    rank = fields.Char('Rank or rating')
    effect = fields.Char('Effects', required=True)


