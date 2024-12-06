from odoo import fields, models, api, tools, _
import requests
import json
import logging
from odoo.exceptions import UserError
import re

_logger = logging.getLogger(__name__)

class HealthDiseaseOutbreakPrediction(models.Model):
    _name = 'health.disease.outbreak.prediction'
    _description = 'Disease Outbreak Prediction'

    # Fields to store predictive results and input data
    name = fields.Char('Prediction Title', required=True, default="New Disease Prediction")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    predicted_disease = fields.Char('Predicted Disease', readonly=True)
    region = fields.Char('Region', compute='_compute_region', store=True, readonly=True)
    prediction_date = fields.Datetime('Prediction Date', default=fields.Datetime.now)
    historical_data = fields.Text('Historical Data', readonly=True)
    prediction_result = fields.Text('Prediction Result', readonly=True)
    accuracy_rate = fields.Float('Prediction Accuracy', readonly=True)

    @api.depends('employee_id')
    def _compute_region(self):
        """Compute region from the employee's work address (address_id)."""
        for record in self:
            if record.employee_id and record.employee_id.address_id:
                # Assuming 'city' in res.partner is used as the region
                record.region = record.employee_id.address_id.city or 'Unknown Region'
            else:
                record.region = 'Unknown Region'

    def trigger_prediction(self):
        """ Trigger the AI-based prediction logic. """
        # Fetch the historical diagnosis data for the selected employee
        historical_data = self._get_historical_data()

        # Call AI-based prediction API
        prediction_result, predicted_disease, accuracy, new_title = self._call_prediction_api(historical_data)

        # Update the prediction results and set the new title returned by OpenAI
        self.write({
            'name': new_title,
            'historical_data': historical_data,
            'prediction_result': prediction_result,
            'predicted_disease': predicted_disease,
            'accuracy_rate': accuracy,
        })

    def _get_historical_data(self):
        """Fetch actual historical diagnosis data for prediction."""
        # Fetch historical diagnosis data specific to the selected employee
        diagnoses = self.env['health.diagnosis'].search([
            ('employee_id', '=', self.employee_id.id),  # Get diagnoses only for this employee
            ('date_diagnosis', '!=', False),  # Ensure the record has a diagnosis date
            ('diagnosis_attribute_line_ids.value_ids', '!=', False)  # Ensure non-empty attribute values
        ])

        # Prepare a list to hold the filtered historical data
        data_for_prediction = []

        for diagnosis in diagnoses:
            # Gather attributes with non-empty values
            attributes_with_values = []
            for line in diagnosis.diagnosis_attribute_line_ids:
                if line.value_ids:  # Check if the attribute has any values
                    attribute_values = [value.name for value in line.value_ids]
                    attributes_with_values.append({
                        'attribute': line.attribute_id.name,
                        'values': attribute_values
                    })

            # If there are any attributes with values, add this diagnosis to the historical data
            if attributes_with_values:
                data_for_prediction.append({
                    'date': diagnosis.date_diagnosis.strftime('%Y-%m-%d'),
                    'disease': diagnosis.name,
                    'attributes': attributes_with_values
                })

        return json.dumps(data_for_prediction, indent=4)

    def _call_prediction_api(self, historical_data):
        """ Call AI-based prediction API using OpenAI. """
        # Retrieve the API key and model details from system parameters
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('ai_health.openai_api_key')
        model = config.get_param('ai_health.openai_model')

        if not api_key or not model:
            raise UserError(_("Missing configuration for AI-based prediction API."))

        # Build the prediction prompt based on historical data
        prompt = (
            f"Here is the historical diagnosis data for the employee:\n"
            f"{historical_data}\n"
            "Based on this data, predict any significant disease outbreak trends for the next week. "
            "Please return the prediction as a JSON object with the following structure:\n"
            "{'prediction_result': {}, 'predicted_disease': {}, 'accuracy': {}, 'title': {}}.\n"
            "Ensure that the 'accuracy' is a numeric value between 0 and 100, representing a percentage confidence level."
        )

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        # Construct the API call payload
        data = {
            'model': model,
            'messages': [
                {"role": "system", "content": "You are a highly intelligent AI that predicts disease outbreaks based on historical health data."},
                {"role": "user", "content": prompt}
            ],
            'max_tokens': 300,
            'temperature': 0.5,  # Adjust based on required creativity level
        }

        # Make the request to OpenAI's API
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)

        if response.status_code != 200:
            _logger.error("Error from OpenAI API: %s", response.text)
            raise UserError(_("Failed to retrieve prediction from the AI API."))

        try:
            # Get the AI's response and parse the result
            prediction_content = response.json()['choices'][0]['message']['content']
            _logger.info("OpenAI prediction response: %s", prediction_content)

            # Parse the response as a JSON object
            prediction_data = json.loads(re.search(r'({.*})', prediction_content, re.DOTALL).group(1))

            prediction_result = prediction_data.get('prediction_result', 'No significant trends detected')
            predicted_disease = prediction_data.get('predicted_disease', 'Unknown')
            title = prediction_data.get('title', 'New Disease Prediction')

            # Extract numerical accuracy
            accuracy = prediction_data.get('accuracy', 0.0)
            
            if isinstance(accuracy, (str, float, int)):
                # If accuracy is a string, float, or integer, convert it to a float
                accuracy = float(accuracy)
            elif isinstance(accuracy, dict):
                # In case a dictionary is returned, try to force the confidence into a numeric form
                if 'confidence_level' in accuracy:
                    confidence_mapping = {
                        'low': 30.0,
                        'moderate': 60.0,
                        'high': 90.0
                    }
                    accuracy = confidence_mapping.get(accuracy['confidence_level'], 0.0)
                else:
                    accuracy = 0.0  # Default if no confidence level is found

            return prediction_result, predicted_disease, accuracy, title

        except Exception as e:
            _logger.error("Error processing AI prediction: %s", str(e))
            raise UserError(_("Error processing AI prediction: %s") % str(e))
