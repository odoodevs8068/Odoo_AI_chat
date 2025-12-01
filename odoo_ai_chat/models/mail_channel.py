from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.iap.tools import iap_tools
from google import genai

DEFAULT_OLG_ENDPOINT = 'https://olg.api.odoo.com'


class Channel(models.Model):
    _inherit = 'discuss.channel'

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        rdata = super(Channel, self)._notify_thread(message, msg_vals=msg_vals, **kwargs)
        try:
            chatgpt_channel_id = self.env.ref('odoo_ai_chat.channel_chatgpt')
            user_chatgpt = self.env.ref("odoo_ai_chat.user_chatgpt")
            partner_chatgpt = self.env.ref("odoo_ai_chat.partner_chatgpt")

            author_id = msg_vals.get('author_id')
            prompt = msg_vals.get('body')
            if not prompt:
                return rdata
            if (
                author_id != partner_chatgpt.id
                and (str(partner_chatgpt.name or '') + ', ' in msg_vals.get('record_name', '') or 'Odoo AI' in msg_vals.get('record_name', ''))
                and self.channel_type == 'chat'
            ):
                res = self._get_ai_response(prompt=prompt)
                self.with_user(user_chatgpt).message_post(
                    body=res, message_type='comment', subtype_xmlid='mail.mt_comment'
                )

            elif (
                author_id != partner_chatgpt.id
                and msg_vals.get('model', '') == 'discuss.channel'
                and msg_vals.get('res_id', 0) == chatgpt_channel_id.id
            ):
                res = self._get_ai_response(prompt=prompt)
                chatgpt_channel_id.with_user(user_chatgpt).message_post(
                    body=res, message_type='comment', subtype_xmlid='mail.mt_comment'
                )
        except Exception as e:
            print(f"Error in _notify_thread: {e}")
        return rdata

    def _get_ai_response(self, prompt):
        ai_type = self.env['ir.config_parameter'].sudo().get_param('odoo_ai_chat.ai_type')
        if ai_type == 'gemini_ai' :
            return self.gemini_ai(prompt)
        else:
            return self.generate_odoo_ai_response(prompt)

    def generate_odoo_ai_response(self, prompt):
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        olg_api_endpoint = IrConfigParameter.get_param('web_editor.olg_api_endpoint', DEFAULT_OLG_ENDPOINT)
        database_id = IrConfigParameter.get_param('database.uuid')
        conversation_history = False
        response = iap_tools.iap_jsonrpc(olg_api_endpoint + "/api/olg/1/chat", params={
            'prompt': prompt,
            'conversation_history': conversation_history or [],
            'database_id': database_id,
        }, timeout=60)
        if response['status'] == 'success':
            return response['content']
        elif response['status'] == 'error_prompt_too_long':
            raise UserError(_("Sorry, your prompt is too long. Try to say it in fewer words."))
        elif response['status'] == 'limit_call_reached':
            raise UserError(_("You have reached the maximum number of requests for this service. Try again later."))
        else:
            raise UserError(_("Sorry, we could not generate a response. Please try again later."))

    def gemini_ai(self, prompt):
        api_key = self.env['ir.config_parameter'].sudo().get_param('odoo_ai_chat.gemini_api_key')
        gemini_model = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_ai_chat.gemini_model'
        ) or 'gemini-2.5-flash'

        if not api_key:
            return "Gemini API key is missing."

        if not prompt or not str(prompt).strip():
            return "Prompt is empty. Gemini requires non-empty input."

        prompt = str(prompt).strip()
        client = genai.Client(api_key=api_key)
        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=[
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ]
            )

            if response and response.text:
                return response.text

            return "No response text from Gemini."

        except Exception as e:
            error_msg = str(e)
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                return (
                    "⚠️ Gemini API quota exceeded.\n"
                    "Please upgrade your plan or wait before retrying.\n\n"
                    f"Technical message:\n{error_msg}"
                )

            return f"Gemini API Error: {error_msg}"

