from odoo import fields, models, api, _
import json
import logging
import requests
import re
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HealthRiskScoring(models.Model):
    _name = 'health.risk.scoring'
    _description = 'Symptom-Based Risk Scoring'
    
    # Fields
    name = fields.Char('Risk Scoring Title', required=True, default="New Risk Scoring")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    diagnosis_id = fields.Many2one('health.diagnosis', string='Diagnosis', required=True, domain="[('employee_id', '=', employee_id)]")
    risk_score = fields.Float('Risk Score', readonly=True)
    escalation_steps = fields.Text('Escalation Steps', readonly=True)
    risk_analysis = fields.Text('Risk Analysis', readonly=True)
    historical_data = fields.Text('Historical Data', readonly=True)
    scoring_date = fields.Datetime('Scoring Date', default=fields.Datetime.now)

    @api.onchange('diagnosis_id')
    def _onchange_diagnosis_id(self):
        """ Automatically fill the symptoms from the diagnosis when a diagnosis is selected. """
        if self.diagnosis_id:
            self.symptoms = self.diagnosis_id.symptom_description  # Get symptoms from diagnosis

    symptoms = fields.Text('Symptoms', compute='_compute_symptoms', store=True, readonly=True)

    @api.depends('diagnosis_id')
    def _compute_symptoms(self):
        """ Compute the symptoms from the diagnosis record. """
        for record in self:
            record.symptoms = record.diagnosis_id.symptom_description if record.diagnosis_id else ''

    def trigger_risk_scoring(self):
        """ Trigger AI-based risk scoring for the employee. """
        # Fetch the diagnosis and symptom data
        diagnosis_data = self._get_diagnosis_data()
        historical_data = self._get_historical_data()

        # Call the AI service to get the risk score and recommendations
        risk_score, escalation_steps, risk_analysis, new_title = self._call_risk_scoring_api(diagnosis_data, historical_data)

        # Update the record with the returned data
        self.write({
            'name': new_title,
            'risk_score': risk_score,
            'escalation_steps': escalation_steps,
            'risk_analysis': risk_analysis,
            'historical_data': historical_data
        })

    def _get_diagnosis_data(self):
        """ Fetch diagnosis and symptom data for the current diagnosis. """
        return {
            'diagnosis_name': self.diagnosis_id.name,
            'symptoms': self.symptoms,  # Automatically fetched from the diagnosis
            'date': self.diagnosis_id.date_diagnosis.strftime('%Y-%m-%d')
        }

    def _get_historical_data(self):
        """ Fetch past medical history for the employee. """
        diagnoses = self.env['health.diagnosis'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date_diagnosis', '!=', False),
            ('diagnosis_attribute_line_ids.value_ids', '!=', False)
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

    def _call_risk_scoring_api(self, diagnosis_data, historical_data):
        """ Call OpenAI's API to get the risk score and escalation steps. """
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('ai_health.openai_api_key')
        model = config.get_param('ai_health.openai_model')

        if not api_key or not model:
            raise UserError(_("Missing configuration for OpenAI API."))

        # Build the risk scoring prompt
        prompt = (
            f"Here is the diagnosis and symptom data:\n"
            f"{json.dumps(diagnosis_data, indent=4)}\n"
            f"Here is the employee's medical history:\n"
            f"{historical_data}\n"
            "Based on the above, assign a risk score (0-100) where 0 is no risk and 100 is high risk. "
            "Also provide escalation steps for critical cases and a brief analysis of the risk. "
            "Return the data in the following JSON structure:\n"
            "{'risk_score': {}, 'escalation_steps': {}, 'risk_analysis': {}, 'title': {}}."
        )

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Payload for OpenAI API
        data = {
            'model': model,
            'messages': [
                {"role": "system", "content": "You are a highly intelligent AI that calculates risk scores based on symptoms and medical history."},
                {"role": "user", "content": prompt}
            ],
            'max_tokens': 500,
            'temperature': 0.7
        }

        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)

        if response.status_code != 200:
            _logger.error("Error from OpenAI API: %s", response.text)
            raise UserError(_("Failed to retrieve risk scoring data."))

        try:
            risk_content = response.json()['choices'][0]['message']['content']
            _logger.info("Received AI risk scoring response: %s", risk_content)  # Log the full response

            # Attempt to parse the response as JSON
            risk_data = json.loads(re.search(r'({.*})', risk_content, re.DOTALL).group(1))

            return (
                risk_data.get('risk_score', 0.0),
                risk_data.get('escalation_steps', 'No escalation steps available'),
                risk_data.get('risk_analysis', 'No risk analysis available'),
                risk_data.get('title', 'New Risk Scoring')
            )
        except Exception as e:
            _logger.error("Error processing AI risk scoring: %s", str(e))
            raise UserError(_("Error processing AI risk scoring: %s") % str(e))
