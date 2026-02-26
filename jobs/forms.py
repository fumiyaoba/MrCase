from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from jobs.models import Case


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ["name", "description", "is_active"]


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label="パスワード",
        widget=forms.PasswordInput,
    )
    password_confirm = forms.CharField(
        label="パスワード（確認）",
        widget=forms.PasswordInput,
    )
    is_staff = forms.BooleanField(label="管理者にする", required=False)
    slack_user_id = forms.CharField(
        label="Slack メンバーID",
        required=False,
        help_text="Slackのプロフィール「・・・」→「メンバーIDをコピー」で取得できます",
    )

    class Meta:
        model = User
        fields = ["username", "last_name", "first_name", "is_staff"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("パスワードが一致しません。")
        if password:
            validate_password(password)
        # 一般ユーザーはSlackID必須
        is_staff = cleaned_data.get("is_staff")
        slack_user_id = cleaned_data.get("slack_user_id", "").strip()
        if not is_staff and not slack_user_id:
            raise forms.ValidationError("一般ユーザーの場合は Slack メンバーID は必須です。")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            from jobs.models import UserProfile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"slack_user_id": self.cleaned_data.get("slack_user_id", "")},
            )
        return user


class UserEditForm(forms.ModelForm):
    is_staff = forms.BooleanField(label="管理者にする", required=False)
    slack_user_id = forms.CharField(
        label="Slack メンバーID",
        required=False,
        help_text="Slackのプロフィール「・・・」→「メンバーIDをコピー」で取得できます",
    )
    password = forms.CharField(
        label="新しいパスワード（変更しない場合は空欄）",
        widget=forms.PasswordInput,
        required=False,
    )
    password_confirm = forms.CharField(
        label="新しいパスワード（確認）",
        widget=forms.PasswordInput,
        required=False,
    )

    class Meta:
        model = User
        fields = ["username", "last_name", "first_name", "is_staff"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                self.fields["slack_user_id"].initial = self.instance.profile.slack_user_id
            except Exception:
                pass

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("パスワードが一致しません。")
        if password:
            validate_password(password)
        # 一般ユーザーはSlackID必須
        is_staff = cleaned_data.get("is_staff")
        slack_user_id = cleaned_data.get("slack_user_id", "").strip()
        if not is_staff and not slack_user_id:
            raise forms.ValidationError("一般ユーザーの場合は Slack メンバーID は必須です。")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            from jobs.models import UserProfile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"slack_user_id": self.cleaned_data.get("slack_user_id", "")},
            )
        return user
