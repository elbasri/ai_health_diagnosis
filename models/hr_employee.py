from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # One2many relationship with health.diagnosis
    # This field allows you to store multiple health diagnosis records for each employee
    diagnosis_ids = fields.One2many('health.diagnosis', 'employee_id', string="Health Diagnoses")
