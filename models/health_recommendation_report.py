from odoo import fields, models, tools

class HealthRecommendationReport(models.Model):
    _name = 'health.recommendation.report'
    _description = 'Health Recommendation Report'
    _auto = False
    _order = 'recommendation_date desc'

    recommendation_date = fields.Datetime('Recommendation Date', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    diagnosis_id = fields.Many2one('health.diagnosis', string='Diagnosis', readonly=True)
    lifestyle_suggestion = fields.Text('Lifestyle Suggestions', readonly=True)
    preventive_measures = fields.Text('Preventive Measures', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'health_recommendation_report')
        self._cr.execute("""
            CREATE VIEW health_recommendation_report AS (
                SELECT 
                    hr.id as id,
                    hr.recommendation_date as recommendation_date,
                    hr.employee_id as employee_id,
                    hr.diagnosis_id as diagnosis_id,
                    hr.lifestyle_suggestion as lifestyle_suggestion,
                    hr.preventive_measures as preventive_measures
                FROM health_recommendation hr
            )
        """)
