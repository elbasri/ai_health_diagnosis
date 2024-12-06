from odoo import fields, models, api, _
import json
import logging
import requests
import re
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HealthRecommendation(models.Model):
    _name = 'health.recommendation'
    _description = 'Health Recommendation'
    
    # Fields
    name = fields.Char('Recommendation Title', required=True, default="New Health Recommendation")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    diagnosis_id = fields.Many2one('health.diagnosis', string='Diagnosis', required=True, domain="[('employee_id', '=', employee_id)]")
    recommendation_date = fields.Datetime('Recommendation Date', default=fields.Datetime.now)
    recommendation_result = fields.Text('Recommendation', readonly=True)
    lifestyle_suggestion = fields.Text('Lifestyle Suggestions', readonly=True)
    preventive_measures = fields.Text('Preventive Measures', readonly=True)
    historical_data = fields.Text('Historical Data', readonly=True)

    @api.depends('diagnosis_id')
    def _compute_symptoms(self):
        """ Compute the symptoms from the diagnosis record. """
        for record in self:
            record.symptoms = record.diagnosis_id.symptom_description if record.diagnosis_id else ''

    def trigger_recommendation(self):
        """ Trigger AI-based recommendation for the employee. """
        # Fetch the diagnosis details and employee's past health records
        diagnosis_data = self._get_diagnosis_data()
        historical_data = self._get_historical_data()

        # Call the AI service to get recommendations
        recommendation, lifestyle_suggestion, preventive_measures, new_title = self._call_recommendation_api(diagnosis_data, historical_data)

        # Update the record with the returned recommendations
        self.write({
            'name': new_title,
            'historical_data': historical_data,
            'recommendation_result': recommendation,
            'lifestyle_suggestion': lifestyle_suggestion,
            'preventive_measures': preventive_measures
        })

    def _get_diagnosis_data(self):
        """ Fetch diagnosis information for the current diagnosis. """
        return {
            'diagnosis_name': self.diagnosis_id.name,
            'symptoms': self.diagnosis_id.symptom_description,
            'date': self.diagnosis_id.date_diagnosis.strftime('%Y-%m-%d')
        }

    def _get_historical_data(self):
        """ Fetch past medical history for the employee. """
        diagnoses = self.env['health.diagnosis'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date_diagnosis', '!=', False),  # Ensure valid diagnosis dates
            ('diagnosis_attribute_line_ids.value_ids', '!=', False)  # Ensure non-empty attribute values
        ])
        
        historical_data = []
        for diagnosis in diagnoses:
            attributes_with_values = []
            for line in diagnosis.diagnosis_attribute_line_ids:
                if line.value_ids:
                    attribute_values = [value.name for value in line.value_ids]
                    attributes_with_values.append({
                        'attribute': line.attribute_id.name,
                        'values': attribute_values
                    })

            if attributes_with_values:
                historical_data.append({
                    'date': diagnosis.date_diagnosis.strftime('%Y-%m-%d'),
                    'diagnosis': diagnosis.name,
                    'attributes': attributes_with_values
                })
        
        return json.dumps(historical_data, indent=4)

    def _call_recommendation_api(self, diagnosis_data, historical_data):
        """ Call OpenAI's API to get health recommendations. """
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('ai_health.openai_api_key')
        model = config.get_param('ai_health.openai_model')

        if not api_key or not model:
            raise UserError(_("Missing configuration for OpenAI API."))

        # Build the recommendation prompt
        prompt = (
            f"Here is the diagnosis data:\n"
            f"{json.dumps(diagnosis_data, indent=4)}\n"
            f"Here is the employee's medical history:\n"
            f"{historical_data}\n"
            "Please provide a detailed health recommendation based on this diagnosis, including lifestyle suggestions and preventive measures. "
            "Return the data in the following JSON structure:\n"
            "{'recommendation': {}, 'lifestyle_suggestion': {}, 'preventive_measures': {}, 'title': {}}."
        )

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Payload for OpenAI API
        data = {
            'model': model,
            'messages': [
                {"role": "system", "content": "You are a highly intelligent AI that provides personalized health recommendations based on medical data."},
                {"role": "user", "content": prompt}
            ],
            'max_tokens': 500,  # Increased token limit
            'temperature': 0.7
        }

        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)

        if response.status_code != 200:
            _logger.error("Error from OpenAI API: %s", response.text)
            raise UserError(_("Failed to retrieve health recommendations."))

        try:
            recommendation_content = response.json()['choices'][0]['message']['content']
            _logger.info("Received AI recommendation response: %s", recommendation_content)  # Log the full response

            # Attempt to parse the response as JSON
            recommendation_data = json.loads(re.search(r'({.*})', recommendation_content, re.DOTALL).group(1))

            return (
                recommendation_data.get('recommendation', 'No recommendation available'),
                recommendation_data.get('lifestyle_suggestion', 'No lifestyle suggestion available'),
                recommendation_data.get('preventive_measures', 'No preventive measures available'),
                recommendation_data.get('title', 'New Health Recommendation')
            )
        except json.JSONDecodeError as e:
            _logger.error("Failed to decode JSON from AI response: %s", str(e))
            _logger.info("Full response text: %s", recommendation_content)
            raise UserError(_("Error decoding AI response. Please check the logs for details."))
        except Exception as e:
            _logger.error("Error processing AI recommendation: %s", str(e))
            raise UserError(_("Error processing AI recommendation: %s") % str(e))

