app_name = "advanced_payment_process"
app_title = "Advanced Payment Process"
app_publisher = "Markus"
app_description = "Vorkasse: Lieferung und Beschaffung bleiben gesperrt, bis die Anzahlung da ist."
app_email = "313874067+alyf-markus@users.noreply.github.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "advanced_payment_process",
# 		"logo": "/assets/advanced_payment_process/logo.png",
# 		"title": "Advanced Payment Process",
# 		"route": "/advanced_payment_process",
# 		"has_permission": "advanced_payment_process.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/advanced_payment_process/css/advanced_payment_process.css"
# app_include_js = "/assets/advanced_payment_process/js/advanced_payment_process.js"

# include js, css files in header of web template
# web_include_css = "/assets/advanced_payment_process/css/advanced_payment_process.css"
# web_include_js = "/assets/advanced_payment_process/js/advanced_payment_process.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "advanced_payment_process/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "advanced_payment_process/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "advanced_payment_process.utils.jinja_methods",
# 	"filters": "advanced_payment_process.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "advanced_payment_process.install.before_install"
# after_install = "advanced_payment_process.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "advanced_payment_process.uninstall.before_uninstall"
# after_uninstall = "advanced_payment_process.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "advanced_payment_process.utils.before_app_install"
# after_app_install = "advanced_payment_process.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "advanced_payment_process.utils.before_app_uninstall"
# after_app_uninstall = "advanced_payment_process.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "advanced_payment_process.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "advanced_payment_process.notifications.get_notification_config"

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

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"advanced_payment_process.tasks.all"
# 	],
# 	"daily": [
# 		"advanced_payment_process.tasks.daily"
# 	],
# 	"hourly": [
# 		"advanced_payment_process.tasks.hourly"
# 	],
# 	"weekly": [
# 		"advanced_payment_process.tasks.weekly"
# 	],
# 	"monthly": [
# 		"advanced_payment_process.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "advanced_payment_process.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "advanced_payment_process.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "advanced_payment_process.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "advanced_payment_process.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["advanced_payment_process.utils.before_request"]
# after_request = ["advanced_payment_process.utils.after_request"]

# Job Events
# ----------
# before_job = ["advanced_payment_process.utils.before_job"]
# after_job = ["advanced_payment_process.utils.after_job"]

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
# 	"advanced_payment_process.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

