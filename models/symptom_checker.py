from odoo import fields, models, api, _
import requests
import json
import re
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SymptomChecker(models.Model):
    _name = 'symptom.checker'
    _description = 'Symptom Checker with AI Diagnostics'

    name = fields.Char('Check Title', required=True, default="New Symptom Check")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    symptom_description = fields.Text('Symptoms', required=True)
    check_date = fields.Datetime('Check Date', default=fields.Datetime.now)
    suggested_conditions = fields.Text('Suggested Conditions', readonly=True)
    recommendation = fields.Text('Recommendation', readonly=True)

    def trigger_check(self):
        """ Trigger the AI-based symptom check. """
        # Prepare symptom data for AI API call
        symptoms = self._get_symptom_data()

        # Call the AI service to get possible conditions
        conditions, recommendation = self._call_ai_diagnostics(symptoms)

        # Update the record with the results
        self.write({
            'suggested_conditions': conditions,
            'recommendation': recommendation,
        })

    def _get_symptom_data(self):
        """ Fetch symptom information provided by the employee. """
        return {
            'employee_name': self.employee_id.name,
            'symptoms': self.symptom_description,
            'date': self.check_date.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def _call_ai_diagnostics(self, symptoms):
        """ Call OpenAI's API to get possible conditions based on symptoms. """
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('ai_health.openai_api_key')
        model = config.get_param('ai_health.openai_model')

        if not api_key or not model:
            raise UserError(_("Missing configuration for OpenAI API."))

        # Build the diagnostic prompt
        prompt = (
            f"Here is the symptom data:\n"
            f"{json.dumps(symptoms, indent=4)}\n"
            "Based on the symptoms provided, suggest possible conditions and provide a recommendation. "
            "Return the data in the following JSON structure:\n"
            "{'suggested_conditions': {}, 'recommendation': {}}."
        )

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Payload for OpenAI API
        data = {
            'model': model,
            'messages': [
                {"role": "system", "content": "You are a highly intelligent AI that provides diagnostic suggestions based on symptoms."},
                {"role": "user", "content": prompt}
            ],
            'max_tokens': 300,
            'temperature': 0.5
        }

        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)

        if response.status_code != 200:
            _logger.error("Error from OpenAI API: %s", response.text)
            raise UserError(_("Failed to retrieve symptom check results."))

        try:
            check_content = response.json()['choices'][0]['message']['content']
            check_data = json.loads(re.search(r'({.*})', check_content, re.DOTALL).group(1))

            return (
                check_data.get('suggested_conditions', 'No conditions suggested'),
                check_data.get('recommendation', 'No recommendation available')
            )
        except Exception as e:
            _logger.error("Error processing AI diagnostics: %s", str(e))
            raise UserError(_("Error processing AI diagnostics: %s") % str(e))
