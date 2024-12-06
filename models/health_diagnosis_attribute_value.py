from odoo import models, fields

class HealthDiagnosisAttributeValue(models.Model):
    _name = 'health.diagnosis.attribute.value'
    _description = 'Health Diagnosis Attribute Value'

    name = fields.Char("Value", required=True)
    attribute_id = fields.Many2one('health.diagnosis.attribute', string="Attribute", required=True)
