from odoo import models, fields

class HealthDiagnosisAttributeLine(models.Model):
    _name = 'health.diagnosis.attribute.line'
    _description = 'Diagnosis Attribute Line'

    diagnosis_id = fields.Many2one('health.diagnosis', string="Diagnosis", required=True)
    attribute_id = fields.Many2one('health.diagnosis.attribute', string="Attribute", required=True)
    value_ids = fields.Many2many('health.diagnosis.attribute.value', string="Values", relation="health_diagnosis_attribute_value_rel")
