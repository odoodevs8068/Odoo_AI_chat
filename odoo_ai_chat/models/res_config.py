from odoo import fields, models, api

class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    ai_type = fields.Selection([
        ('odoo_ai', 'Odoo AI'),
        ('gemini_ai', 'Gemini AI'),
    ], default='odoo_ai', string="AI Type")

    gemini_model = fields.Selection([
        ('gemini-2.5-flash', 'Gemini-2.5-Flash'),
        ('gemini-3-pro-preview', 'Gemini 3 Pro Preview'),
    ], default='gemini-2.5-flash', string="Gemini Model")

    gemini_api_key = fields.Char("Gemini API Key")

    def set_values(self):
        res = super(ResConfigSettingsInherit, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('odoo_ai_chat.ai_type', self.ai_type)
        self.env['ir.config_parameter'].sudo().set_param('odoo_ai_chat.gemini_api_key', self.gemini_api_key)
        self.env['ir.config_parameter'].sudo().set_param('odoo_ai_chat.gemini_model', self.gemini_model)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            ai_type=params.get_param('odoo_ai_chat.ai_type'),
            gemini_model=params.get_param('odoo_ai_chat.gemini_model'),
            gemini_api_key=params.get_param('odoo_ai_chat.gemini_api_key'),
        )
        return res

