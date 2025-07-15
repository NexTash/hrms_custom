app_name = "hrms_custom"
app_title = "Hrms Custom"
app_publisher = "Nextash"
app_description = "Hrms Custumizations"
app_email = "support@nextash.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "hrms_custom",
# 		"logo": "/assets/hrms_custom/logo.png",
# 		"title": "Hrms Custom",
# 		"route": "/hrms_custom",
# 		"has_permission": "hrms_custom.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/hrms_custom/css/hrms_custom.css"
app_include_js = "/assets/hrms_custom/js/hrms_custom.js"

# include js, css files in header of web template
# web_include_css = "/assets/hrms_custom/css/hrms_custom.css"
# web_include_js = "/assets/hrms_custom/js/hrms_custom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "hrms_custom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Salary Slip" : "public/js/salary_slip_custom.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "hrms_custom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
role_home_page = {
	"Employee": "hrms"
}
website_route_rules = [
    {"from_route": "/hrms/login", "to_route": "hrms_login"},
]
# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "hrms_custom.utils.jinja_methods",
# 	"filters": "hrms_custom.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "hrms_custom.install.before_install"
# after_install = "hrms_custom.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "hrms_custom.uninstall.before_uninstall"
# after_uninstall = "hrms_custom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "hrms_custom.utils.before_app_install"
# after_app_install = "hrms_custom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "hrms_custom.utils.before_app_uninstall"
# after_app_uninstall = "hrms_custom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hrms_custom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Salary Slip": "hrms_custom.overrides.salary_slip.SalarySlipCustom"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Journal Entry": {
        "on_submit": "hrms_custom.events.journal_hooks.process_salary_payment",
        "on_cancel": "hrms_custom.events.journal_hooks.reverse_salary_payment"
    },
    "Salary Slip": {
        "after_insert": "hrms_custom.events.salary_slip_auto_recalc.auto_recalculate_dependent_components_after_insert",
        "before_save": "hrms_custom.events.salary_slip_auto_recalc.auto_recalculate_dependent_components_before_save"
    }
    # Temporarily disabled automatic recalculation to avoid conflicts
    # "Salary Slip": {
    #     "before_save": "hrms_custom.events.salary_slip_hooks.auto_recalculate_deductions"
    # }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"hrms_custom.tasks.all"
# 	],
# 	"daily": [
# 		"hrms_custom.tasks.daily"
# 	],
# 	"hourly": [
# 		"hrms_custom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"hrms_custom.tasks.weekly"
# 	],
# 	"monthly": [
# 		"hrms_custom.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "hrms_custom.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "hrms_custom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "hrms_custom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["hrms_custom.utils.before_request"]
# after_request = ["hrms_custom.utils.after_request"]

# Job Events
# ----------
# before_job = ["hrms_custom.utils.before_job"]
# after_job = ["hrms_custom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"hrms_custom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# fixtures = [
#     {
#         "doctype": "Custom Field",
#         "filters": [
#             ["name", "in", ["Salary Slip-custom_journal_amount","Salary Slip-payment_status"]]
#         ]
#     },
#     {
#         "doctype": "Property Setter",
#         "filters": [
#             ["doc_type", "=", "Account"],
#             ["field_name", "=", "account_type"],
#             ["property", "=", "options"]
#         ]
#     }
# ]
