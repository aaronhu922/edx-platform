from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from django.conf import settings
import logging


class Aliyun:

    def __init__(self):
        appid = settings.SMS.get('appid', None)
        secret = settings.SMS.get('secret', None)
        self.template = settings.SMS.get('template', 'SMS_205055214')
        self.client = AcsClient(appid, secret, 'cn-hangzhou')

    def send_sms(self, mobile, sign, data=None):
        """
        发送短信

        mobile: 手机号码
        sign: 短信签名
        template: 短信模板
        data: 短信内容
        """
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('dysmsapi.aliyuncs.com')
        request.set_method('POST')
        request.set_protocol_type('https') # https | http
        request.set_version('2017-05-25')
        request.set_action_name('SendSms')

        request.add_query_param('RegionId', "default")
        request.add_query_param('PhoneNumbers', mobile)
        request.add_query_param('SignName', sign)
        request.add_query_param('TemplateCode', self.template)
        request.add_query_param('TemplateParam', data)
        logging.warning("Sign name: {sign}, template: {template}".format(sign=sign, template=self.template))
        response = self.client.do_action_with_exception(request)
        logging.warning(response)
        return response
