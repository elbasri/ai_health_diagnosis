from odoo import models, fields

class HealthDiagnosisAttribute(models.Model):
    _name = 'health.diagnosis.attribute'
    _description = 'Health Diagnosis Attribute'

    name = fields.Char("Attribute", required=True)
    description = fields.Text("Description")
    attribute_set_id = fields.Many2one('health.diagnosis.attribute.set', string="Attribute Set")
