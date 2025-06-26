from django.contrib import admin

class MonospaceAdminTextareaWidget(admin.widgets.AdminTextareaWidget):
    def __init__(self, attrs=None):
        my_attrs = {
            'style': 'font-family: "Bitstream Vera Sans Mono", Monaco, "Courier New", Courier, monospace;'
        }
        super().__init__(attrs={**my_attrs, **(attrs or {})})

class ShortMonospaceAdminTextareaWidget(MonospaceAdminTextareaWidget):
    def __init__(self, attrs=None):
        my_attrs = {
            'rows': 1,
        }
        super().__init__(attrs={**my_attrs, **(attrs or {})})