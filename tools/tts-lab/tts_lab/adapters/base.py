from ..core import LabError, checked_response, validate_wav


class Adapter:
    name = ''
    models = ()

    def validate(self, request):
        request.validate()
        if request.provider != self.name or request.model not in self.models:
            raise LabError('Provider/model does not belong to this adapter.')
        if not self.supports_style(request.model, request.voice, request.style):
            raise LabError('This candidate has no documented equivalent gentle style; it is not silently replaced.')

    def supports_style(self, model, voice, style):
        return style == 'neutral'

    def parse(self, response, request):
        checked_response(response)
        validate_wav(response.body, request.audio)
        return response.body

    def synthesize(self, request, transport):
        plan = self.prepare(request)
        # One attempt only: an ambiguous failure may already have been billed.
        response = transport.send(plan)
        return self.parse(response, request)
