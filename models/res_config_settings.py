from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    openai_api_key = fields.Char('OpenAI API Key')
    openai_prompt = fields.Text('OpenAI Prompt')
    openai_model = fields.Char('OpenAI Model', default='gpt-3.5-turbo')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('ai_health.openai_api_key', self.openai_api_key)
        self.env['ir.config_parameter'].set_param('ai_health.openai_prompt', self.openai_prompt)
        self.env['ir.config_parameter'].set_param('ai_health.openai_model', self.openai_model)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            openai_api_key=self.env['ir.config_parameter'].get_param('ai_health.openai_api_key', default=''),
            openai_prompt=self.env['ir.config_parameter'].get_param('ai_health.openai_prompt', default=''),
            openai_model=self.env['ir.config_parameter'].get_param('ai_health.openai_model', default='gpt-3.5-turbo'),
        )
        return res
