from odoo import fields, models, tools

class HealthDiseaseOutbreakReport(models.Model):
    _name = 'health.disease.outbreak.report'
    _description = 'Health Disease Outbreak Report'
    _auto = False
    _order = 'prediction_date desc'

    prediction_date = fields.Datetime('Prediction Date', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    predicted_disease = fields.Char('Predicted Disease', readonly=True)
    region = fields.Char('Region', readonly=True)
    accuracy_rate = fields.Float('Prediction Accuracy', readonly=True)
    total_predictions = fields.Integer('Total Predictions', readonly=True)
    avg_accuracy = fields.Float('Average Prediction Accuracy', readonly=True)


    def init(self):
        tools.drop_view_if_exists(self._cr, 'health_disease_outbreak_report')
        self._cr.execute("""
            CREATE VIEW health_disease_outbreak_report AS (
                SELECT 
                    MIN(p.id) AS id,  -- Ensure a unique ID for each row
                    p.predicted_disease AS predicted_disease,
                    COUNT(p.id) AS total_predictions,  -- Count how many predictions for each disease
                    AVG(p.accuracy_rate) AS accuracy_rate,  -- Calculate the average accuracy and alias as accuracy_rate
                    MIN(p.prediction_date) AS prediction_date,  -- Use the earliest prediction date for this disease
                    MAX(p.prediction_date) AS last_prediction_date   -- The most recent prediction date for this disease
                FROM 
                    health_disease_outbreak_prediction p
                WHERE 
                    p.predicted_disease IS NOT NULL  -- Only include predictions with a valid disease
                GROUP BY 
                    p.predicted_disease
            );
        """)

