from django import forms


class CreateOrderForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    phone_number = forms.CharField()
    requires_delivery = forms.CharField()
    delivery_address = forms.CharField(required=False)
    payment_on_get = forms.CharField()