from odoo import models, fields, api, _
import json
import re
import requests
from odoo.exceptions import UserError
import logging

from odoo import http
from odoo.http import request, content_disposition

from io import BytesIO
import xlsxwriter


_logger = logging.getLogger(__name__)

class HealthDiagnosis(models.Model):
    _name = 'health.diagnosis'
    _description = 'Health Diagnosis Record'

    # Set default value for name to "New Diagnosis"
    name = fields.Char("Diagnosis Title", required=True, default="New Diagnosis")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    symptom_description = fields.Text("Symptom Description", required=True)
    date_diagnosis = fields.Datetime("Date", default=fields.Datetime.now)
    diagnosis_attribute_line_ids = fields.One2many('health.diagnosis.attribute.line', 'diagnosis_id', string="Diagnosis Attribute Lines")
    

    @api.model
    def create(self, vals):
        if 'name' not in vals or not vals['name']:
            vals['name'] = _("Auto-Generated Diagnosis")
        return super(HealthDiagnosis, self).create(vals)

    def get_health_advice(self):
        _logger.info("Executing get_health_advice for diagnosis: %s", self.name)

        # Retrieve the API key, prompt, and model from the system parameters
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('ai_health.openai_api_key')
        prompt_template = config.get_param('ai_health.openai_prompt')
        model = config.get_param('ai_health.openai_model')

        if not self.symptom_description:
            raise UserError(_("Please provide the symptom description."))

        # Collect employee data
        employee_data = self._get_employee_data()

        # Build the prompt
        prompt = (
            f"{prompt_template}\n"
            f"Symptoms: {self.symptom_description}\n"
            f"Employee Data: {employee_data}\n"
            "Please return the diagnosis strictly as a JSON object with key-value pairs inside the following structure:\n"
            "{'title': {}, 'preliminary': {}, 'treatment': {}, 'notes': {}}. "
            "Each key ('title', 'preliminary', 'treatment', and 'notes') should have a value. "
            "Ensure the response is a valid JSON object."
        )

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        messages = [
            {"role": "system", "content": "You are a medical assistant AI that provides health diagnosis based on symptoms. You must return structured JSON in key-value pairs."},
            {"role": "user", "content": prompt}
        ]

        data = {
            'model': model,
            'messages': messages,
            'max_tokens': 2048,
            'temperature': 0.7,
        }

        # Make the request to OpenAI's API
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)

        if response.status_code != 200:
            _logger.error("Error from OpenAI: %s", response.text)
            raise UserError(_("Error retrieving health advice from OpenAI."))

        try:
            # Get the AI's response
            advice_text = response.json()['choices'][0]['message']['content']
            _logger.info("OpenAI response: %s", advice_text)

            # Parse the response as a JSON object
            diagnosis_data = json.loads(re.search(r'({.*})', advice_text, re.DOTALL).group(1))

            # Extract the title and update the diagnosis name
            self.name = diagnosis_data.get('title', {}).get('diagnosis', 'Unknown Diagnosis')

            # Process each attribute set (preliminary, treatment, notes)
            for set_name, attributes in diagnosis_data.items():
                if set_name != 'title':  # Skip the title in attribute sets
                    self._process_attribute_set(set_name, attributes)

        except Exception as e:
            _logger.error("Error processing diagnosis: %s", str(e))
            raise UserError(f"Error processing diagnosis: {e}")

    def _process_attribute_set(self, set_name, attributes):
        # Find or create the attribute set
        attribute_set = self.env['health.diagnosis.attribute.set'].search([('name', '=', set_name)], limit=1)
        if not attribute_set:
            attribute_set = self.env['health.diagnosis.attribute.set'].create({'name': set_name})

        for attr_name, attr_values in attributes.items():
            # Find or create the attribute under this set
            attribute = self.env['health.diagnosis.attribute'].search([
                ('name', '=', attr_name),
                ('attribute_set_id', '=', attribute_set.id)
            ], limit=1)
            if not attribute:
                attribute = self.env['health.diagnosis.attribute'].create({
                    'name': attr_name,
                    'attribute_set_id': attribute_set.id
                })

            # Prepare value_ids to hold the ids of the diagnosis values
            value_ids = []
            if isinstance(attr_values, list):
                for value in attr_values:
                    val = self.env['health.diagnosis.attribute.value'].search([('name', '=', value)], limit=1)
                    if not val:
                        val = self.env['health.diagnosis.attribute.value'].create({
                            'name': value,
                            'attribute_id': attribute.id
                        })
                    value_ids.append(val.id)
            else:
                val = self.env['health.diagnosis.attribute.value'].search([('name', '=', attr_values)], limit=1)
                if not val:
                    val = self.env['health.diagnosis.attribute.value'].create({
                        'name': attr_values,
                        'attribute_id': attribute.id
                    })
                value_ids.append(val.id)

            # Check if there is already an attribute line for this diagnosis and attribute
            existing_line = self.env['health.diagnosis.attribute.line'].search([
                ('diagnosis_id', '=', self.id),
                ('attribute_id', '=', attribute.id)
            ], limit=1)

            if existing_line:
                # Append new values to the existing line
                existing_line.write({
                    'value_ids': [(4, value_id) for value_id in value_ids]
                })
            else:
                # Create a new line if no line exists
                self.env['health.diagnosis.attribute.line'].create({
                    'diagnosis_id': self.id,
                    'attribute_id': attribute.id,
                    'value_ids': [(6, 0, value_ids)]
                })

    def export_diagnosis_excel(self):
        # Create an in-memory Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Diagnosis Report')
        
        # Add column headers
        headers = ['Attribute Set', 'Attribute', 'Values']
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header)
        
        # Write data rows
        row_num = 1
        for line in self.diagnosis_attribute_line_ids:
            sheet.write(row_num, 0, line.attribute_id.attribute_set_id.name or '')
            sheet.write(row_num, 1, line.attribute_id.name or '')
            values = ', '.join([value.name for value in line.value_ids])
            sheet.write(row_num, 2, values or '')
            row_num += 1
        
        # Close the workbook
        workbook.close()
        output.seek(0)
        
        # Create a response with the Excel content
        excel_data = output.read()
        output.close()

        # Correctly create the response using the request object from odoo.http
        return request.make_response(
            excel_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(f'Diagnosis_Report_{self.id}.xlsx'))
            ]
        )
    
    def _get_employee_data(self):
        """Retrieve relevant employee information to include in the prompt."""
        if not self.employee_id:
            return {}

        employee = self.employee_id
        address = employee.address_id
        
        employee_data = {
            "Date of Birth": employee.birthday.strftime('%Y-%m-%d') if employee.birthday else '',
            "Gender": employee.gender or '',
            "Marital Status": employee.marital or '',
            "Nationality": employee.country_id.name or '',
            "Country of Birth": employee.country_of_birth.name or '',
            "Job Position": employee.job_id.name or '',
            "Department": employee.department_id.name or '',
            "Emergency Contact": employee.emergency_contact or '',
            "Emergency Phone": employee.emergency_phone or '',
            "Number of Children": employee.children or '',
            "Coach": employee.coach_id.name or '',
            "Home-Work Distance": employee.km_home_work or '',
            "Work Location": employee.work_location or '',
            "Notes": employee.notes or '',
            "Street": address.street or '',
            "Street2": address.street2 or '',
            "City": address.city or '',
            "State": address.state_id.name if address.state_id else '',
            "Zip": address.zip or '',
            "Country": address.country_id.name if address.country_id else '',
        }

        # Filter out empty values
        employee_data = {k: v for k, v in employee_data.items() if v}
        return json.dumps(employee_data, indent=4)
