from odoo import models, fields

class HealthDiagnosisAttributeSet(models.Model):
    _name = 'health.diagnosis.attribute.set'
    _description = 'Health Diagnosis Attribute Set'

    name = fields.Char("Attribute Set", required=True)
    attribute_ids = fields.Many2many('health.diagnosis.attribute', string="Attributes")
