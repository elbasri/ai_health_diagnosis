from odoo import fields, models, tools

class HealthDiagnosisReport(models.Model):
    _name = 'health.diagnosis.report'
    _description = 'Health Diagnosis Report'
    _auto = False
    _order = 'date_diagnosis desc'

    date_diagnosis = fields.Datetime('Date of Diagnosis', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    attribute_id = fields.Many2one('health.diagnosis.attribute', string='Attribute', readonly=True)
    attribute_value_id = fields.Many2one('health.diagnosis.attribute.value', string='Attribute Value', readonly=True)
    diagnosis_id = fields.Many2one('health.diagnosis', string='Diagnosis', readonly=True)
    total_diagnoses = fields.Integer(string='Total Diagnoses', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'health_diagnosis_report')
        self._cr.execute("""
            CREATE VIEW health_diagnosis_report AS (
                SELECT 
                    hl.id as id,
                    hl.date_diagnosis as date_diagnosis,
                    hl.employee_id as employee_id,
                    l.attribute_id as attribute_id,
                    v.id as attribute_value_id,
                    hl.id as diagnosis_id,
                    COUNT(hl.id) OVER() as total_diagnoses
                FROM health_diagnosis hl
                LEFT JOIN health_diagnosis_attribute_line l ON l.diagnosis_id = hl.id
                LEFT JOIN health_diagnosis_attribute_value_rel rel ON rel.health_diagnosis_attribute_line_id = l.id
                LEFT JOIN health_diagnosis_attribute_value v ON v.id = rel.health_diagnosis_attribute_value_id
            )
        """)
