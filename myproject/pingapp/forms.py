from django import forms
import socket

class PingForm(forms.Form):
    target = forms.CharField(label='Target (e.g. google.com)', max_length=100, required=True)

    def clean_target(self):
        target = self.cleaned_data['target']
        try:
            # Attempt to resolve the hostname to an IP address
            socket.gethostbyname(target)
        except socket.error:
            raise forms.ValidationError("Invalid IP address or hostname.")
        return target
