from django import forms

class LoginForm(forms.Form):
    login_email = forms.EmailField(
        error_messages={
            "required": "Email is required.",
            "invalid": "Enter a valid email address."
        }
    )

    login_password = forms.CharField(
        widget=forms.PasswordInput,
        error_messages={
            "required": "Password is required."
        }
    )
