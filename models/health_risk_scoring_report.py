from odoo import fields, models, tools

class HealthRiskScoringReport(models.Model):
    _name = 'health.risk.scoring.report'
    _description = 'Health Risk Scoring Report'
    _auto = False
    _order = 'scoring_date desc'

    scoring_date = fields.Datetime('Scoring Date', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    risk_score = fields.Float('Risk Score', readonly=True)
    diagnosis_id = fields.Many2one('health.diagnosis', string='Diagnosis', readonly=True)
    total_risks = fields.Integer(string='Total Risk Assessments', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'health_risk_scoring_report')
        self._cr.execute("""
            CREATE VIEW health_risk_scoring_report AS (
                SELECT
                    s.id AS id,
                    s.scoring_date AS scoring_date,
                    s.employee_id AS employee_id,
                    s.risk_score AS risk_score,
                    s.diagnosis_id AS diagnosis_id,
                    COUNT(s.id) OVER() AS total_risks
                FROM health_risk_scoring s
            )
        """)
