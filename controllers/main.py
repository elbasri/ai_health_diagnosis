from odoo import http
from odoo.http import request

class HealthDiagnosisController(http.Controller):
    
    @http.route('/web/content/diagnosis_report/<int:diagnosis_id>', type='http', auth="user", csrf=False)
    def download_excel_report(self, diagnosis_id, **kwargs):
        # Get the diagnosis record
        diagnosis = request.env['health.diagnosis'].browse(diagnosis_id)

        # Generate the report (ensure export_diagnosis_excel method exists and returns the correct response)
        report = diagnosis.export_diagnosis_excel()

        # Return the generated report
        return report
